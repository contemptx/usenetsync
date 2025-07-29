#!/usr/bin/env python3
"""
Advanced Connection Pool Manager for UsenetSync
Handles connection lifecycle, health monitoring, and load balancing
"""

import threading
import time
import queue
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class ConnectionHealth:
    """Health metrics for a connection"""
    successful_operations: int = 0
    failed_operations: int = 0
    total_bytes_transferred: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def record_success(self, response_time: float, bytes_transferred: int = 0):
        """Record successful operation"""
        self.successful_operations += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()
        self.total_bytes_transferred += bytes_transferred
        self.response_times.append(response_time)
        self.average_response_time = sum(self.response_times) / len(self.response_times)
        
    def record_failure(self):
        """Record failed operation"""
        self.failed_operations += 1
        self.consecutive_failures += 1
        self.last_failure = datetime.now()
        
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successful_operations + self.failed_operations
        if total == 0:
            return 1.0
        return self.successful_operations / total
        
    def is_healthy(self, max_consecutive_failures: int = 5) -> bool:
        """Check if connection is healthy"""
        if self.consecutive_failures >= max_consecutive_failures:
            return False
            
        # Check if connection has been idle too long
        if self.last_success:
            idle_time = datetime.now() - self.last_success
            if idle_time > timedelta(minutes=5):
                return False
                
        return True

class ConnectionManager:
    """
    Advanced connection manager with health monitoring and load balancing
    """
    
    def __init__(self, create_connection: Callable, max_connections: int = 10):
        self.create_connection = create_connection
        self.max_connections = max_connections
        self.connections: Dict[int, Any] = {}
        self.health_metrics: Dict[int, ConnectionHealth] = {}
        self.available_connections = queue.PriorityQueue()
        self.in_use_connections = set()
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        self._connection_counter = 0
        
        # Start health monitor
        self._start_health_monitor()
        
    def get_connection(self, timeout: float = 30.0) -> Optional[Tuple[int, Any]]:
        """
        Get a healthy connection
        Returns: (connection_id, connection_object)
        """
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                # Get connection with best health score
                priority, conn_id = self.available_connections.get(
                    timeout=min(1.0, deadline - time.time())
                )
                
                with self._lock:
                    if conn_id in self.connections:
                        conn = self.connections[conn_id]
                        health = self.health_metrics[conn_id]
                        
                        # Check if connection is still healthy
                        if health.is_healthy():
                            self.in_use_connections.add(conn_id)
                            return conn_id, conn
                        else:
                            # Connection unhealthy, remove it
                            self._remove_connection(conn_id)
                            
            except queue.Empty:
                # No available connections, try to create new one
                if len(self.connections) < self.max_connections:
                    conn_id, conn = self._create_new_connection()
                    if conn:
                        return conn_id, conn
                        
        return None
        
    def return_connection(self, conn_id: int, success: bool = True,
                         response_time: float = 0.0, bytes_transferred: int = 0):
        """Return connection to pool and update health metrics"""
        with self._lock:
            if conn_id not in self.connections:
                return
                
            # Update health metrics
            health = self.health_metrics[conn_id]
            if success:
                health.record_success(response_time, bytes_transferred)
            else:
                health.record_failure()
                
            # Return to pool if healthy
            if conn_id in self.in_use_connections:
                self.in_use_connections.remove(conn_id)
                
            if health.is_healthy():
                # Priority based on success rate and response time
                priority = self._calculate_priority(health)
                self.available_connections.put((priority, conn_id))
            else:
                # Remove unhealthy connection
                self._remove_connection(conn_id)
                
    def _create_new_connection(self) -> Tuple[Optional[int], Optional[Any]]:
        """Create new connection"""
        try:
            conn = self.create_connection()
            if conn:
                with self._lock:
                    conn_id = self._connection_counter
                    self._connection_counter += 1
                    
                    self.connections[conn_id] = conn
                    self.health_metrics[conn_id] = ConnectionHealth()
                    self.in_use_connections.add(conn_id)
                    
                    logger.info(f"Created new connection {conn_id}")
                    return conn_id, conn
                    
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            
        return None, None
        
    def _remove_connection(self, conn_id: int):
        """Remove connection from pool"""
        if conn_id in self.connections:
            try:
                conn = self.connections[conn_id]
                # Call cleanup method if available
                if hasattr(conn, 'disconnect'):
                    conn.disconnect()
                elif hasattr(conn, 'close'):
                    conn.close()
            except:
                pass
                
            del self.connections[conn_id]
            del self.health_metrics[conn_id]
            self.in_use_connections.discard(conn_id)
            
            logger.info(f"Removed connection {conn_id}")
            
    def _calculate_priority(self, health: ConnectionHealth) -> float:
        """
        Calculate connection priority (lower is better)
        Based on success rate and response time
        """
        success_rate = health.get_success_rate()
        avg_response = health.average_response_time or 1.0
        
        # Weight success rate more heavily
        priority = (1.0 - success_rate) * 100 + avg_response
        
        return priority
        
    def _start_health_monitor(self):
        """Start background health monitoring thread"""
        self._monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
    def _health_monitor_loop(self):
        """Background thread to monitor connection health"""
        while not self._stop_monitor.is_set():
            try:
                with self._lock:
                    # Check for idle connections
                    now = datetime.now()
                    idle_threshold = timedelta(minutes=2)
                    
                    for conn_id, health in list(self.health_metrics.items()):
                        if conn_id in self.in_use_connections:
                            continue
                            
                        # Check if connection has been idle
                        if health.last_success:
                            idle_time = now - health.last_success
                            if idle_time > idle_threshold:
                                # Send keepalive
                                self._send_keepalive(conn_id)
                                
                # Sleep before next check
                self._stop_monitor.wait(30)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                
    def _send_keepalive(self, conn_id: int):
        """Send keepalive to connection"""
        if conn_id in self.connections:
            conn = self.connections[conn_id]
            try:
                # Call keepalive method if available
                if hasattr(conn, 'keepalive'):
                    conn.keepalive()
                elif hasattr(conn, 'noop'):
                    conn.noop()
            except Exception as e:
                logger.debug(f"Keepalive failed for connection {conn_id}: {e}")
                self._remove_connection(conn_id)
                
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            total_success = sum(h.successful_operations for h in self.health_metrics.values())
            total_failure = sum(h.failed_operations for h in self.health_metrics.values())
            total_bytes = sum(h.total_bytes_transferred for h in self.health_metrics.values())
            
            healthy_connections = sum(
                1 for h in self.health_metrics.values() if h.is_healthy()
            )
            
            avg_response_times = [
                h.average_response_time 
                for h in self.health_metrics.values() 
                if h.average_response_time > 0
            ]
            
            overall_avg_response = (
                sum(avg_response_times) / len(avg_response_times)
                if avg_response_times else 0
            )
            
            return {
                'total_connections': len(self.connections),
                'healthy_connections': healthy_connections,
                'in_use_connections': len(self.in_use_connections),
                'available_connections': self.available_connections.qsize(),
                'total_operations': total_success + total_failure,
                'successful_operations': total_success,
                'failed_operations': total_failure,
                'success_rate': total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 1.0,
                'total_bytes_transferred': total_bytes,
                'average_response_time': overall_avg_response
            }
            
    def shutdown(self):
        """Shutdown connection manager"""
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            
        with self._lock:
            # Close all connections
            for conn_id in list(self.connections.keys()):
                self._remove_connection(conn_id)
                
        logger.info("Connection manager shutdown complete")