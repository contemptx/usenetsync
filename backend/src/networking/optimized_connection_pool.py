#!/usr/bin/env python3
"""
Optimized NNTP Connection Pool
Manages connections efficiently with lazy creation and proper reuse
"""

import queue
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OptimizedConnectionPool:
    """
    Optimized connection pool that:
    - Creates connections lazily (on-demand)
    - Reuses connections efficiently
    - Respects server limits
    - Manages connection health
    """
    
    def __init__(self, 
                 host: str,
                 port: int,
                 username: str,
                 password: str,
                 use_ssl: bool = True,
                 max_connections: int = 60,  # Server allows ~60 concurrent
                 initial_connections: int = 1,  # Start with just 1
                 connection_lifetime: int = 3600,  # Max lifetime in seconds
                 idle_timeout: int = 300,  # Close idle connections after 5 min
                 create_timeout: float = 30.0):
        """
        Initialize optimized connection pool
        
        Args:
            host: NNTP server hostname
            port: Server port
            username: Authentication username
            password: Authentication password
            use_ssl: Use SSL/TLS
            max_connections: Maximum concurrent connections (server limit)
            initial_connections: Number of connections to create initially
            connection_lifetime: Maximum lifetime for a connection
            idle_timeout: Close connections idle for this long
            create_timeout: Timeout for creating new connections
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.max_connections = max_connections
        self.initial_connections = min(initial_connections, max_connections)
        self.connection_lifetime = connection_lifetime
        self.idle_timeout = idle_timeout
        self.create_timeout = create_timeout
        
        # Connection tracking
        self.active_connections = []
        self.available_pool = queue.Queue()
        self.total_created = 0
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'connections_closed': 0,
            'current_active': 0,
            'peak_connections': 0,
            'failed_creates': 0,
            'health_checks': 0,
            'recycled': 0
        }
        
        # Create initial connections
        self._initialize_minimal()
        
        # Start maintenance thread
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True
        )
        self.maintenance_thread.start()
        
    def _initialize_minimal(self):
        """Create minimal initial connections"""
        logger.info(f"Creating {self.initial_connections} initial connection(s)")
        
        for i in range(self.initial_connections):
            try:
                conn = self._create_connection()
                if conn:
                    self.available_pool.put(conn)
                    logger.info(f"Initial connection {i+1} created successfully")
                else:
                    logger.warning(f"Failed to create initial connection {i+1}")
            except Exception as e:
                logger.error(f"Error creating initial connection: {e}")
                
    def _create_connection(self) -> Optional['ConnectionWrapper']:
        """Create a new connection with proper tracking"""
        with self.lock:
            # Check if we're at the limit
            if self.total_created >= self.max_connections:
                logger.warning(f"Connection limit reached ({self.max_connections})")
                return None
                
            # Prevent creating too many connections too quickly
            if self.total_created > 0:
                time.sleep(0.5)  # Small delay between connections
                
        try:
            # Import here to avoid circular dependency
            from networking.production_nntp_client import NNTPConnection
            
            # Create the actual connection
            conn = NNTPConnection(
                self.host, self.port, self.username,
                self.password, self.use_ssl, self.create_timeout
            )
            
            if conn.connect():
                # Wrap the connection with metadata
                wrapper = ConnectionWrapper(
                    connection=conn,
                    created_at=datetime.now(),
                    pool=self
                )
                
                with self.lock:
                    self.total_created += 1
                    self.active_connections.append(wrapper)
                    self.stats['connections_created'] += 1
                    self.stats['current_active'] = len(self.active_connections)
                    self.stats['peak_connections'] = max(
                        self.stats['peak_connections'],
                        self.stats['current_active']
                    )
                    
                logger.info(f"Created connection {self.total_created}/{self.max_connections}")
                return wrapper
            else:
                self.stats['failed_creates'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            self.stats['failed_creates'] += 1
            return None
            
    @contextmanager
    def get_connection(self, timeout: float = 5.0):
        """
        Get a connection from the pool
        
        This will:
        1. Try to get an existing healthy connection
        2. Create a new one if needed and allowed
        3. Wait if at capacity
        """
        connection = None
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                # Try to get an available connection
                try:
                    connection = self.available_pool.get_nowait()
                    
                    # Check if connection is healthy and not expired
                    if connection.is_healthy():
                        self.stats['connections_reused'] += 1
                        connection.last_used = datetime.now()
                        yield connection.connection
                        return
                    else:
                        # Connection is bad, close it
                        logger.debug("Closing unhealthy connection")
                        self._close_connection(connection)
                        connection = None
                        
                except queue.Empty:
                    # No available connections, try to create one
                    with self.lock:
                        can_create = self.total_created < self.max_connections
                        
                    if can_create:
                        connection = self._create_connection()
                        if connection:
                            connection.last_used = datetime.now()
                            yield connection.connection
                            return
                    else:
                        # At capacity, wait a bit
                        time.sleep(0.1)
                        
            # Timeout reached
            raise TimeoutError(f"Could not get connection within {timeout}s")
            
        finally:
            # Return connection to pool
            if connection and connection.is_healthy():
                self.available_pool.put(connection)
            elif connection:
                self._close_connection(connection)
                
    def _close_connection(self, wrapper: 'ConnectionWrapper'):
        """Close a connection and remove from tracking"""
        try:
            wrapper.connection.close()
        except:
            pass
            
        with self.lock:
            if wrapper in self.active_connections:
                self.active_connections.remove(wrapper)
            self.stats['connections_closed'] += 1
            self.stats['current_active'] = len(self.active_connections)
            
    def _maintenance_loop(self):
        """Background thread to maintain connection health"""
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                self._cleanup_idle_connections()
                self._check_connection_health()
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                
    def _cleanup_idle_connections(self):
        """Close connections that have been idle too long"""
        now = datetime.now()
        to_close = []
        
        # Check available connections
        temp_queue = []
        while not self.available_pool.empty():
            try:
                conn = self.available_pool.get_nowait()
                
                # Check if idle too long
                idle_time = (now - conn.last_used).total_seconds()
                if idle_time > self.idle_timeout:
                    to_close.append(conn)
                    logger.debug(f"Closing idle connection (idle for {idle_time:.0f}s)")
                else:
                    temp_queue.append(conn)
            except queue.Empty:
                break
                
        # Put back the connections we're keeping
        for conn in temp_queue:
            self.available_pool.put(conn)
            
        # Close idle connections
        for conn in to_close:
            self._close_connection(conn)
            
    def _check_connection_health(self):
        """Periodic health check of connections"""
        with self.lock:
            # Check for expired connections
            now = datetime.now()
            to_close = []
            
            for conn in self.active_connections:
                age = (now - conn.created_at).total_seconds()
                if age > self.connection_lifetime:
                    to_close.append(conn)
                    logger.debug(f"Connection expired (age: {age:.0f}s)")
                    
        # Close expired connections
        for conn in to_close:
            self._close_connection(conn)
            self.stats['recycled'] += 1
            
    def close_all(self):
        """Close all connections in the pool"""
        logger.info("Closing all connections")
        
        # Close available connections
        while not self.available_pool.empty():
            try:
                conn = self.available_pool.get_nowait()
                self._close_connection(conn)
            except queue.Empty:
                break
                
        # Close all active connections
        with self.lock:
            for conn in list(self.active_connections):
                self._close_connection(conn)
                
        logger.info(f"Closed all connections. Stats: {self.get_stats()}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            **self.stats,
            'available_now': self.available_pool.qsize(),
            'total_created': self.total_created,
            'limit': self.max_connections
        }


class ConnectionWrapper:
    """Wrapper for connection with metadata"""
    
    def __init__(self, connection, created_at: datetime, pool: OptimizedConnectionPool):
        self.connection = connection
        self.created_at = created_at
        self.last_used = created_at
        self.pool = pool
        self.health_check_count = 0
        
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        try:
            # Don't check too frequently
            self.health_check_count += 1
            if self.health_check_count % 10 == 0:  # Check every 10th use
                self.pool.stats['health_checks'] += 1
                return self.connection.is_healthy()
            return True  # Assume healthy between checks
        except:
            return False


# Singleton instance management
_pool_instance = None
_pool_lock = threading.Lock()


def get_shared_pool(host: str, port: int, username: str, password: str,
                    use_ssl: bool = True, **kwargs) -> OptimizedConnectionPool:
    """
    Get or create a shared connection pool instance
    
    This ensures only one pool is created per server configuration
    """
    global _pool_instance
    
    with _pool_lock:
        if _pool_instance is None:
            logger.info("Creating shared connection pool")
            _pool_instance = OptimizedConnectionPool(
                host=host,
                port=port,
                username=username,
                password=password,
                use_ssl=use_ssl,
                **kwargs
            )
        else:
            logger.debug("Reusing existing connection pool")
            
    return _pool_instance


def reset_shared_pool():
    """Reset the shared pool (useful for testing)"""
    global _pool_instance
    
    with _pool_lock:
        if _pool_instance:
            _pool_instance.close_all()
            _pool_instance = None


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/workspace')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the optimized pool
    print("Testing Optimized Connection Pool")
    print("-" * 40)
    
    # Create pool with minimal connections
    pool = OptimizedConnectionPool(
        host='news.newshosting.com',
        port=563,
        username='contemptx',
        password='Kia211101#',
        use_ssl=True,
        max_connections=60,
        initial_connections=1  # Start with just 1 connection
    )
    
    print(f"Initial stats: {pool.get_stats()}")
    
    # Test getting connections
    print("\nTesting connection acquisition:")
    for i in range(3):
        try:
            with pool.get_connection() as conn:
                print(f"  Got connection {i+1}")
                time.sleep(0.5)
        except Exception as e:
            print(f"  Failed to get connection: {e}")
            
    print(f"\nFinal stats: {pool.get_stats()}")
    
    # Cleanup
    pool.close_all()