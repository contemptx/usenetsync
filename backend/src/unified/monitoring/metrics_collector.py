#!/usr/bin/env python3
"""
Unified Metrics Collector - Collect system metrics
Production-ready with time-series data collection
"""

import time
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import logging

logger = logging.getLogger(__name__)

class UnifiedMetricsCollector:
    """
    Unified metrics collector
    Collects and stores system and application metrics
    """
    
    def __init__(self, db=None, max_history: int = 1000):
        """Initialize metrics collector"""
        self.db = db
        self.max_history = max_history
        
        # Time-series storage
        self.metrics_history = {
            'cpu': deque(maxlen=max_history),
            'memory': deque(maxlen=max_history),
            'disk': deque(maxlen=max_history),
            'network': deque(maxlen=max_history),
            'database': deque(maxlen=max_history),
            'uploads': deque(maxlen=max_history),
            'downloads': deque(maxlen=max_history)
        }
        
        # Counters
        self.counters = {
            'files_indexed': 0,
            'segments_created': 0,
            'uploads_completed': 0,
            'downloads_completed': 0,
            'shares_created': 0,
            'errors_total': 0
        }
        
        # Gauges
        self.gauges = {
            'active_connections': 0,
            'queue_size': 0,
            'cache_size': 0,
            'database_connections': 0
        }
        
        self._last_network = psutil.net_io_counters()
        self._start_time = time.time()
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        network_rate = self._calculate_network_rate(network)
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_avg': psutil.getloadavg()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
                'send_rate': network_rate['send_rate'],
                'recv_rate': network_rate['recv_rate']
            }
        }
        
        # Store in history
        self.metrics_history['cpu'].append((timestamp, cpu_percent))
        self.metrics_history['memory'].append((timestamp, memory.percent))
        self.metrics_history['disk'].append((timestamp, disk.percent))
        self.metrics_history['network'].append((timestamp, network_rate))
        
        # Store in database
        if self.db:
            self._store_metrics(metrics)
        
        return metrics
    
    def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'counters': self.counters.copy(),
            'gauges': self.gauges.copy(),
            'uptime': time.time() - self._start_time
        }
        
        # Get database metrics
        if self.db:
            db_stats = self.db.get_stats()
            metrics['database'] = {
                'connections': db_stats.get('connections', 0),
                'queries': db_stats.get('queries', 0),
                'cache_hits': db_stats.get('cache_hits', 0),
                'cache_misses': db_stats.get('cache_misses', 0)
            }
            
            # Get table sizes
            metrics['tables'] = {}
            tables = ['folders', 'files', 'segments', 'publications', 'users']
            
            for table in tables:
                count = self.db.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                if count:
                    metrics['tables'][table] = count['count']
        
        return metrics
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        if name in self.counters:
            self.counters[name] += value
            logger.debug(f"Counter {name} incremented by {value}")
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        if name in self.gauges:
            self.gauges[name] = value
            logger.debug(f"Gauge {name} set to {value}")
    
    def record_event(self, event_type: str, metadata: Optional[Dict] = None):
        """Record an event"""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        if self.db:
            self.db.insert('metrics', event)
        
        logger.info(f"Event recorded: {event_type}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        system = self.collect_system_metrics()
        application = self.collect_application_metrics()
        
        # Calculate rates
        rates = {
            'indexing_rate': self._calculate_rate('files_indexed'),
            'upload_rate': self._calculate_rate('uploads_completed'),
            'download_rate': self._calculate_rate('downloads_completed')
        }
        
        return {
            'system': system,
            'application': application,
            'rates': rates,
            'health_score': self._calculate_health_score()
        }
    
    def get_time_series(self, metric: str, 
                       duration_minutes: int = 60) -> List[Tuple[datetime, float]]:
        """Get time series data for metric"""
        if metric not in self.metrics_history:
            return []
        
        history = list(self.metrics_history[metric])
        
        # Filter by duration
        cutoff = datetime.now().timestamp() - (duration_minutes * 60)
        filtered = [(ts, val) for ts, val in history 
                   if ts.timestamp() > cutoff]
        
        return filtered
    
    def _calculate_network_rate(self, current) -> Dict[str, float]:
        """Calculate network transfer rates"""
        if self._last_network:
            time_delta = 1.0  # Assuming 1 second interval
            send_rate = (current.bytes_sent - self._last_network.bytes_sent) / time_delta
            recv_rate = (current.bytes_recv - self._last_network.bytes_recv) / time_delta
        else:
            send_rate = recv_rate = 0
        
        self._last_network = current
        
        return {
            'send_rate': send_rate,
            'recv_rate': recv_rate
        }
    
    def _calculate_rate(self, counter: str) -> float:
        """Calculate rate for counter"""
        if counter in self.counters:
            uptime = time.time() - self._start_time
            if uptime > 0:
                return self.counters[counter] / uptime
        return 0.0
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Check CPU
        if self.metrics_history['cpu']:
            cpu_avg = sum(val for _, val in list(self.metrics_history['cpu'])[-10:]) / 10
            if cpu_avg > 80:
                score -= 20
            elif cpu_avg > 60:
                score -= 10
        
        # Check memory
        if self.metrics_history['memory']:
            mem_avg = sum(val for _, val in list(self.metrics_history['memory'])[-10:]) / 10
            if mem_avg > 90:
                score -= 20
            elif mem_avg > 70:
                score -= 10
        
        # Check disk
        if self.metrics_history['disk']:
            disk_usage = list(self.metrics_history['disk'])[-1][1]
            if disk_usage > 90:
                score -= 30
            elif disk_usage > 80:
                score -= 15
        
        # Check errors
        error_rate = self._calculate_rate('errors_total')
        if error_rate > 1.0:
            score -= 20
        elif error_rate > 0.1:
            score -= 10
        
        return max(0, score)
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in database"""
        try:
            self.db.insert('metrics', {
                'timestamp': metrics['timestamp'],
                'type': 'system',
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")