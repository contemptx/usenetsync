#!/usr/bin/env python3
"""
Unified Server Health - Monitor NNTP server health
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UnifiedServerHealth:
    """Monitor and track NNTP server health"""
    
    def __init__(self, db=None):
        """Initialize server health monitor"""
        self.db = db
        self._health_cache = {}
        self._last_check = {}
    
    def update_health(self, server: str, port: int, 
                     success: bool, response_time_ms: Optional[int] = None):
        """
        Update server health status
        
        Args:
            server: Server hostname
            port: Server port
            success: Whether operation succeeded
            response_time_ms: Response time in milliseconds
        """
        server_key = f"{server}:{port}"
        
        if server_key not in self._health_cache:
            self._health_cache[server_key] = {
                'server': server,
                'port': port,
                'success_count': 0,
                'failure_count': 0,
                'consecutive_failures': 0,
                'avg_response_time': 0,
                'status': 'unknown'
            }
        
        health = self._health_cache[server_key]
        
        if success:
            health['success_count'] += 1
            health['consecutive_failures'] = 0
            health['status'] = 'healthy'
            
            # Update average response time
            if response_time_ms:
                if health['avg_response_time'] == 0:
                    health['avg_response_time'] = response_time_ms
                else:
                    health['avg_response_time'] = (
                        health['avg_response_time'] * 0.9 + response_time_ms * 0.1
                    )
        else:
            health['failure_count'] += 1
            health['consecutive_failures'] += 1
            
            if health['consecutive_failures'] >= 3:
                health['status'] = 'unhealthy'
            elif health['consecutive_failures'] >= 1:
                health['status'] = 'degraded'
        
        health['last_check'] = datetime.now()
        
        # Store in database if available
        if self.db:
            self._store_health(server_key, health)
    
    def get_health(self, server: str, port: int) -> Dict[str, Any]:
        """Get server health status"""
        server_key = f"{server}:{port}"
        
        if server_key in self._health_cache:
            return self._health_cache[server_key]
        
        # Try to load from database
        if self.db:
            health = self.db.fetch_one(
                "SELECT * FROM server_health WHERE server = ? AND port = ?",
                (server, port)
            )
            if health:
                self._health_cache[server_key] = dict(health)
                return self._health_cache[server_key]
        
        return {
            'server': server,
            'port': port,
            'status': 'unknown',
            'success_count': 0,
            'failure_count': 0
        }
    
    def get_best_server(self, servers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get best server based on health
        
        Args:
            servers: List of server configurations
        
        Returns:
            Best server or None
        """
        best_server = None
        best_score = -1
        
        for server in servers:
            health = self.get_health(server['host'], server.get('port', 119))
            
            # Calculate score
            score = 0
            if health['status'] == 'healthy':
                score = 100
            elif health['status'] == 'degraded':
                score = 50
            elif health['status'] == 'unhealthy':
                score = 10
            
            # Factor in success rate
            total = health['success_count'] + health['failure_count']
            if total > 0:
                success_rate = health['success_count'] / total
                score *= success_rate
            
            # Factor in response time
            if health.get('avg_response_time', 0) > 0:
                # Lower response time is better
                score *= (1000 / health['avg_response_time'])
            
            if score > best_score:
                best_score = score
                best_server = server
        
        return best_server
    
    def _store_health(self, server_key: str, health: Dict[str, Any]):
        """Store health in database"""
        try:
            self.db.upsert(
                'server_health',
                {
                    'server': health['server'],
                    'port': health['port'],
                    'status': health['status'],
                    'response_time_ms': int(health.get('avg_response_time', 0)),
                    'success_count': health['success_count'],
                    'failure_count': health['failure_count'],
                    'consecutive_failures': health['consecutive_failures'],
                    'checked_at': datetime.now().isoformat()
                },
                ['server', 'port']
            )
        except Exception as e:
            logger.error(f"Failed to store health: {e}")
    
    def is_healthy(self, server: str, port: int) -> bool:
        """Check if server is healthy"""
        health = self.get_health(server, port)
        return health['status'] in ['healthy', 'degraded']