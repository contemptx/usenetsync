#!/usr/bin/env python3
"""
Unified Connection Pool - Manage multiple NNTP connections
Production-ready with health monitoring and load balancing
"""

import threading
import queue
import time
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import logging

from .nntp_client import UnifiedNNTPClient

logger = logging.getLogger(__name__)

class UnifiedConnectionPool:
    """
    Connection pool for NNTP clients
    Manages multiple connections with health checks
    """
    
    def __init__(self, servers: List[Dict[str, Any]], 
                 max_connections_per_server: int = 10):
        """
        Initialize connection pool
        
        Args:
            servers: List of server configurations
            max_connections_per_server: Max connections per server
        """
        self.servers = servers
        self.max_connections = max_connections_per_server
        self.pools = {}  # server_id -> queue of connections
        self.locks = {}  # server_id -> lock
        self.stats = {}  # server_id -> statistics
        self._closed = False
        
        # Initialize pools for each server
        for server in servers:
            server_id = f"{server['host']}:{server.get('port', 119)}"
            self.pools[server_id] = queue.Queue(maxsize=max_connections_per_server)
            self.locks[server_id] = threading.Lock()
            self.stats[server_id] = {
                'connections_created': 0,
                'connections_reused': 0,
                'connection_errors': 0,
                'posts_successful': 0,
                'posts_failed': 0,
                'retrieves_successful': 0,
                'retrieves_failed': 0
            }
    
    @contextmanager
    def get_connection(self, prefer_server: Optional[str] = None):
        """
        Get connection from pool
        
        Args:
            prefer_server: Preferred server ID
        
        Yields:
            NNTP client connection
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        connection = None
        server_id = None
        
        try:
            # Get connection
            connection, server_id = self._get_connection(prefer_server)
            
            if connection:
                self.stats[server_id]['connections_reused'] += 1
                yield connection
            else:
                raise RuntimeError("No available connections")
                
        except Exception as e:
            if server_id:
                self.stats[server_id]['connection_errors'] += 1
            raise
            
        finally:
            # Return connection to pool
            if connection and server_id:
                self._return_connection(server_id, connection)
    
    def _get_connection(self, prefer_server: Optional[str] = None) -> Tuple[Optional[UnifiedNNTPClient], Optional[str]]:
        """Get connection from pool or create new one"""
        
        # Try preferred server first
        if prefer_server and prefer_server in self.pools:
            conn = self._get_from_server(prefer_server)
            if conn:
                return conn, prefer_server
        
        # Try all servers
        for server_id in self.pools:
            conn = self._get_from_server(server_id)
            if conn:
                return conn, server_id
        
        # No existing connections, create new one
        for server in self.servers:
            server_id = f"{server['host']}:{server.get('port', 119)}"
            
            with self.locks[server_id]:
                # Check if we can create more connections
                if self.pools[server_id].qsize() < self.max_connections:
                    conn = self._create_connection(server)
                    if conn:
                        self.stats[server_id]['connections_created'] += 1
                        return conn, server_id
        
        return None, None
    
    def _get_from_server(self, server_id: str) -> Optional[UnifiedNNTPClient]:
        """Get connection from specific server pool"""
        try:
            # Try to get existing connection
            conn = self.pools[server_id].get_nowait()
            
            # Test if connection is alive
            if conn.test_connection():
                return conn
            else:
                # Connection dead, discard it
                conn.disconnect()
                return None
                
        except queue.Empty:
            return None
    
    def _create_connection(self, server: Dict[str, Any]) -> Optional[UnifiedNNTPClient]:
        """Create new connection to server"""
        try:
            client = UnifiedNNTPClient()
            
            # Connect
            if client.connect(
                server['host'],
                server.get('port', 119),
                server.get('ssl', False),
                server.get('timeout', 30)
            ):
                # Authenticate if credentials provided
                if 'username' in server and 'password' in server:
                    client.authenticate(server['username'], server['password'])
                
                return client
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def _return_connection(self, server_id: str, connection: UnifiedNNTPClient):
        """Return connection to pool"""
        if self._closed:
            connection.disconnect()
            return
        
        try:
            self.pools[server_id].put_nowait(connection)
        except queue.Full:
            # Pool full, close connection
            connection.disconnect()
    
    def post_article(self, subject: str, body: bytes, 
                     newsgroups: List[str],
                     headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Post article using pool
        
        Args:
            subject: Article subject
            body: Article body
            newsgroups: List of newsgroups
            headers: Optional headers
        
        Returns:
            Message ID if successful
        """
        with self.get_connection() as conn:
            server_id = self._get_server_id(conn)
            
            try:
                message_id = conn.post_article(subject, body, newsgroups, headers)
                
                if message_id:
                    self.stats[server_id]['posts_successful'] += 1
                else:
                    self.stats[server_id]['posts_failed'] += 1
                
                return message_id
                
            except Exception as e:
                self.stats[server_id]['posts_failed'] += 1
                logger.error(f"Post failed: {e}")
                return None
    
    def retrieve_article(self, message_id: str) -> Optional[Tuple[str, List[str]]]:
        """
        Retrieve article using pool
        
        Args:
            message_id: Message ID to retrieve
        
        Returns:
            Article data or None
        """
        # Try all servers
        for server_id in self.pools:
            try:
                with self.get_connection(prefer_server=server_id) as conn:
                    result = conn.retrieve_article(message_id)
                    
                    if result:
                        self.stats[server_id]['retrieves_successful'] += 1
                        return result
                    else:
                        self.stats[server_id]['retrieves_failed'] += 1
                        
            except Exception as e:
                self.stats[server_id]['retrieves_failed'] += 1
                logger.debug(f"Retrieve from {server_id} failed: {e}")
        
        return None
    
    def _get_server_id(self, connection: UnifiedNNTPClient) -> str:
        """Get server ID for connection"""
        info = connection.get_server_info()
        return f"{info['host']}:{info['port']}"
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get pool statistics"""
        stats = {}
        
        for server_id, server_stats in self.stats.items():
            stats[server_id] = {
                **server_stats,
                'pool_size': self.pools[server_id].qsize()
            }
        
        return stats
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all servers"""
        health = {}
        
        for server in self.servers:
            server_id = f"{server['host']}:{server.get('port', 119)}"
            
            # Try to create test connection
            conn = self._create_connection(server)
            if conn:
                health[server_id] = conn.test_connection()
                conn.disconnect()
            else:
                health[server_id] = False
        
        return health
    
    def close(self):
        """Close all connections"""
        self._closed = True
        
        for server_id, pool in self.pools.items():
            while not pool.empty():
                try:
                    conn = pool.get_nowait()
                    conn.disconnect()
                except:
                    pass
        
        logger.info("Connection pool closed")