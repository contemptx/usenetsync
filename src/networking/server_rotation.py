"""
Server Rotation and Failover Manager
Handles automatic server switching and load balancing
"""

import asyncio
import random
import time
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RotationStrategy(Enum):
    """Server rotation strategies"""
    ROUND_ROBIN = "round_robin"
    FAILOVER = "failover"
    LOAD_BALANCE = "load_balance"
    RANDOM = "random"
    PRIORITY = "priority"
    GEOGRAPHIC = "geographic"

@dataclass
class ServerHealth:
    """Server health metrics"""
    server_id: str
    is_alive: bool = True
    response_time: float = 0.0
    success_rate: float = 1.0
    failed_attempts: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    bytes_transferred: int = 0
    active_connections: int = 0
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if not self.is_alive:
            return 0.0
        
        # Weight factors
        success_weight = 0.5
        response_weight = 0.3
        failure_weight = 0.2
        
        # Calculate components
        success_score = self.success_rate * 100 * success_weight
        
        # Response time score (lower is better, cap at 5 seconds)
        response_score = max(0, (1 - min(self.response_time, 5) / 5)) * 100 * response_weight
        
        # Failure score (fewer failures is better)
        failure_score = max(0, (1 - min(self.failed_attempts, 10) / 10)) * 100 * failure_weight
        
        return success_score + response_score + failure_score

@dataclass
class ServerConfig:
    """Server configuration"""
    server_id: str
    hostname: str
    port: int
    priority: int = 1
    weight: int = 1
    region: Optional[str] = None
    max_connections: int = 10
    enabled: bool = True

class ServerRotationManager:
    """Manages server rotation and failover"""
    
    def __init__(self, servers: Optional[List[ServerConfig]] = None,
        strategy: RotationStrategy = RotationStrategy.FAILOVER,
        health_check_interval: int = 60,
        failure_threshold: int = 3
    ):
        """
        Initialize server rotation manager
        
        Args:
            servers: List of server configurations
            strategy: Rotation strategy to use
            health_check_interval: Seconds between health checks
            failure_threshold: Failures before marking server as down
        """
        self.servers = {s.id: s for s in (servers or [])}
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold
        
        # Server health tracking
        self.server_health = {s.id: ServerHealth(server_id=s.id) for s in (servers or [])}
        
        # Rotation state
        self.current_server_index = 0
        self.current_server_id: Optional[str] = None
        self.server_order = list(self.servers.keys())
        
        # Callbacks
        self.on_server_change: Optional[Callable] = None
        self.on_server_failure: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'total_rotations': 0,
            'total_failures': 0,
            'strategy_changes': 0
        }
        
        # Start health monitoring
        self._health_check_task = None
        self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        async def monitor():
            while True:
                await self._check_all_servers_health()
                await asyncio.sleep(self.health_check_interval)
        
        self._health_check_task = asyncio.create_task(monitor())
    
    async def _check_all_servers_health(self):
        """Check health of all servers"""
        for server_id in self.servers:
            if self.servers[server_id].enabled:
                await self._check_server_health(server_id)
    
    async def _check_server_health(self, server_id: str) -> bool:
        """
        Check if a server is healthy
        
        Returns:
            True if server is healthy
        """
        # This would normally do actual health check
        # For now, simulate with random success
        health = self.server_health[server_id]
        
        # Simulate health check
        is_healthy = random.random() > 0.1  # 90% success rate
        response_time = random.uniform(0.1, 2.0) if is_healthy else 5.0
        
        health.last_check = datetime.now()
        
        if is_healthy:
            health.is_alive = True
            health.response_time = response_time
            health.last_success = datetime.now()
            health.failed_attempts = 0
            
            # Update success rate
            health.success_rate = min(1.0, health.success_rate * 0.9 + 0.1)
        else:
            health.failed_attempts += 1
            health.last_failure = datetime.now()
            
            # Update success rate
            health.success_rate = max(0.0, health.success_rate * 0.9)
            
            # Mark as down if threshold exceeded
            if health.failed_attempts >= self.failure_threshold:
                health.is_alive = False
                logger.warning(f"Server {server_id} marked as down after {health.failed_attempts} failures")
                
                if self.on_server_failure:
                    await self.on_server_failure(server_id)
        
        return is_healthy
    
    def get_next_server(self) -> Optional[ServerConfig]:
        """
        Get next server based on rotation strategy
        
        Returns:
            Next server configuration or None if all servers are down
        """
        if self.strategy == RotationStrategy.ROUND_ROBIN:
            return self._get_round_robin_server()
        elif self.strategy == RotationStrategy.FAILOVER:
            return self._get_failover_server()
        elif self.strategy == RotationStrategy.LOAD_BALANCE:
            return self._get_load_balanced_server()
        elif self.strategy == RotationStrategy.RANDOM:
            return self._get_random_server()
        elif self.strategy == RotationStrategy.PRIORITY:
            return self._get_priority_server()
        elif self.strategy == RotationStrategy.GEOGRAPHIC:
            return self._get_geographic_server()
        else:
            return self._get_failover_server()
    
    def _get_round_robin_server(self) -> Optional[ServerConfig]:
        """Get next server in round-robin order"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        # Find next available server in order
        for _ in range(len(self.server_order)):
            self.current_server_index = (self.current_server_index + 1) % len(self.server_order)
            server_id = self.server_order[self.current_server_index]
            
            if server_id in available_servers:
                self._set_current_server(server_id)
                return self.servers[server_id]
        
        return None
    
    def _get_failover_server(self) -> Optional[ServerConfig]:
        """Get primary server or failover to next"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        # Try current server first
        if self.current_server_id and self.current_server_id in available_servers:
            return self.servers[self.current_server_id]
        
        # Failover to next available by priority
        sorted_servers = sorted(
            available_servers,
            key=lambda s: self.servers[s].priority
        )
        
        if sorted_servers:
            self._set_current_server(sorted_servers[0])
            return self.servers[sorted_servers[0]]
        
        return None
    
    def _get_load_balanced_server(self) -> Optional[ServerConfig]:
        """Get server with best load balance"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        # Select server with lowest active connections and best health
        best_server = None
        best_score = float('inf')
        
        for server_id in available_servers:
            health = self.server_health[server_id]
            config = self.servers[server_id]
            
            # Calculate load score (lower is better)
            load_score = (
                health.active_connections / config.max_connections * 100 +
                (100 - health.health_score) +
                health.response_time * 10
            ) / config.weight
            
            if load_score < best_score:
                best_score = load_score
                best_server = server_id
        
        if best_server:
            self._set_current_server(best_server)
            return self.servers[best_server]
        
        return None
    
    def _get_random_server(self) -> Optional[ServerConfig]:
        """Get random available server"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        server_id = random.choice(list(available_servers))
        self._set_current_server(server_id)
        return self.servers[server_id]
    
    def _get_priority_server(self) -> Optional[ServerConfig]:
        """Get highest priority available server"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        # Sort by priority (lower number = higher priority)
        sorted_servers = sorted(
            available_servers,
            key=lambda s: (self.servers[s].priority, -self.server_health[s].health_score)
        )
        
        if sorted_servers:
            self._set_current_server(sorted_servers[0])
            return self.servers[sorted_servers[0]]
        
        return None
    
    def _get_geographic_server(self, user_region: Optional[str] = None) -> Optional[ServerConfig]:
        """Get geographically closest server"""
        available_servers = self._get_available_servers()
        if not available_servers:
            return None
        
        # If user region specified, prefer servers in same region
        if user_region:
            regional_servers = [
                s for s in available_servers
                if self.servers[s].region == user_region
            ]
            if regional_servers:
                server_id = random.choice(regional_servers)
                self._set_current_server(server_id)
                return self.servers[server_id]
        
        # Fall back to random selection
        return self._get_random_server()
    
    def _get_available_servers(self) -> set:
        """Get set of available server IDs"""
        return {
            server_id
            for server_id, config in self.servers.items()
            if config.enabled and self.server_health[server_id].is_alive
        }
    
    def _set_current_server(self, server_id: str):
        """Set current server and trigger callback"""
        old_server = self.current_server_id
        self.current_server_id = server_id
        
        if old_server != server_id:
            self.stats['total_rotations'] += 1
            logger.info(f"Rotated from server {old_server} to {server_id}")
            
            if self.on_server_change:
                asyncio.create_task(self.on_server_change(old_server, server_id))
    
    def mark_server_failed(self, server_id: str):
        """Mark a server as failed"""
        if server_id in self.server_health:
            health = self.server_health[server_id]
            health.failed_attempts += 1
            health.last_failure = datetime.now()
            health.success_rate = max(0.0, health.success_rate * 0.8)
            
            if health.failed_attempts >= self.failure_threshold:
                health.is_alive = False
                self.stats['total_failures'] += 1
                logger.error(f"Server {server_id} marked as failed")
                
                # Trigger rotation if this was current server
                if server_id == self.current_server_id:
                    self.get_next_server()
    
    def mark_server_success(self, server_id: str, response_time: float = 0.0):
        """Mark a server operation as successful"""
        if server_id in self.server_health:
            health = self.server_health[server_id]
            health.is_alive = True
            health.failed_attempts = 0
            health.last_success = datetime.now()
            health.response_time = response_time
            health.success_rate = min(1.0, health.success_rate * 0.95 + 0.05)
    
    def add_server(self, config: ServerConfig):
        """Add a new server to rotation"""
        self.servers[config.server_id] = config
        self.server_health[config.server_id] = ServerHealth(server_id=config.server_id)
        self.server_order.append(config.server_id)
        logger.info(f"Added server {config.server_id} to rotation")
    
    def remove_server(self, server_id: str):
        """Remove a server from rotation"""
        if server_id in self.servers:
            del self.servers[server_id]
            del self.server_health[server_id]
            self.server_order.remove(server_id)
            
            # Rotate if this was current server
            if server_id == self.current_server_id:
                self.get_next_server()
            
            logger.info(f"Removed server {server_id} from rotation")
    
    def set_strategy(self, strategy: RotationStrategy):
        """Change rotation strategy"""
        old_strategy = self.strategy
        self.strategy = strategy
        self.stats['strategy_changes'] += 1
        logger.info(f"Changed rotation strategy from {old_strategy} to {strategy}")
    
    def get_server_stats(self, server_id: str) -> Dict[str, Any]:
        """Get statistics for a specific server"""
        if server_id not in self.server_health:
            return {}
        
        health = self.server_health[server_id]
        config = self.servers[server_id]
        
        return {
            'server_id': server_id,
            'hostname': config.hostname,
            'is_alive': health.is_alive,
            'health_score': health.health_score,
            'success_rate': health.success_rate,
            'response_time': health.response_time,
            'failed_attempts': health.failed_attempts,
            'last_check': health.last_check.isoformat() if health.last_check else None,
            'last_success': health.last_success.isoformat() if health.last_success else None,
            'last_failure': health.last_failure.isoformat() if health.last_failure else None
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all servers"""
        return {
            'strategy': self.strategy.value,
            'current_server': self.current_server_id,
            'total_servers': len(self.servers),
            'available_servers': len(self._get_available_servers()),
            'rotation_stats': self.stats,
            'servers': [
                self.get_server_stats(server_id)
                for server_id in self.servers
            ]
        }
    
    async def shutdown(self):
        """Shutdown rotation manager"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Server rotation manager shutdown")