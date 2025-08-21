#!/usr/bin/env python3
"""
Monitoring and Metrics System for Unified UsenetSync
Real-time monitoring, alerting, and Prometheus metrics export
"""

import os
import sys
import time
import psutil
import threading
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import deque, defaultdict
from enum import Enum
import statistics

# Prometheus client for metrics export
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class Alert:
    """Alert definition"""
    name: str
    condition: str
    threshold: float
    severity: str  # info, warning, critical
    message: str
    cooldown_seconds: int = 300
    last_triggered: Optional[datetime] = None

class MonitoringSystem:
    """Comprehensive monitoring and metrics system"""
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize monitoring system
        
        Args:
            retention_hours: How long to keep metrics in memory
        """
        self.retention_hours = retention_hours
        self.metrics_store = defaultdict(lambda: deque(maxlen=3600))  # 1 hour of seconds
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.running = False
        self._lock = threading.Lock()
        
        # System monitoring
        self.process = psutil.Process()
        
        # Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self._setup_prometheus_metrics()
            
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics collectors"""
        # Counters
        self.prom_files_indexed = Counter(
            'usenetsync_files_indexed_total',
            'Total number of files indexed'
        )
        self.prom_segments_uploaded = Counter(
            'usenetsync_segments_uploaded_total',
            'Total number of segments uploaded'
        )
        self.prom_errors = Counter(
            'usenetsync_errors_total',
            'Total number of errors',
            ['component', 'error_type']
        )
        
        # Gauges
        self.prom_memory_usage = Gauge(
            'usenetsync_memory_usage_bytes',
            'Current memory usage in bytes'
        )
        self.prom_cpu_usage = Gauge(
            'usenetsync_cpu_usage_percent',
            'Current CPU usage percentage'
        )
        self.prom_active_connections = Gauge(
            'usenetsync_active_connections',
            'Number of active NNTP connections'
        )
        
        # Histograms
        self.prom_indexing_duration = Histogram(
            'usenetsync_indexing_duration_seconds',
            'Time spent indexing files',
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
        )
        self.prom_upload_duration = Histogram(
            'usenetsync_upload_duration_seconds',
            'Time spent uploading segments',
            buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
        )
        
        # Summary
        self.prom_throughput = Summary(
            'usenetsync_throughput_mbps',
            'Data throughput in MB/s'
        )
        
    def start(self, prometheus_port: int = 8000):
        """Start monitoring system"""
        if self.running:
            return
            
        self.running = True
        
        # Start Prometheus HTTP server if available
        if PROMETHEUS_AVAILABLE and prometheus_port:
            try:
                start_http_server(prometheus_port)
                logger.info(f"Prometheus metrics available at http://localhost:{prometheus_port}/metrics")
            except Exception as e:
                logger.warning(f"Failed to start Prometheus server: {e}")
                
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info("Monitoring system started")
        
    def stop(self):
        """Stop monitoring system"""
        self.running = False
        logger.info("Monitoring system stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check alerts
                self._check_alerts()
                
                # Clean old metrics
                self._cleanup_old_metrics()
                
                time.sleep(1)  # Collect every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        # CPU usage
        cpu_percent = self.process.cpu_percent()
        self.record_metric('system.cpu_usage', cpu_percent, MetricType.GAUGE)
        
        # Memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        self.record_metric('system.memory_mb', memory_mb, MetricType.GAUGE)
        self.record_metric('system.memory_percent', 
                          self.process.memory_percent(), MetricType.GAUGE)
        
        # Disk I/O
        try:
            io_counters = self.process.io_counters()
            self.record_metric('system.disk_read_mb', 
                             io_counters.read_bytes / (1024 * 1024), MetricType.COUNTER)
            self.record_metric('system.disk_write_mb',
                             io_counters.write_bytes / (1024 * 1024), MetricType.COUNTER)
        except:
            pass  # Not available on all systems
            
        # Network connections
        try:
            connections = len(self.process.connections())
            self.record_metric('system.connections', connections, MetricType.GAUGE)
        except:
            pass
            
        # Thread count
        self.record_metric('system.threads', self.process.num_threads(), MetricType.GAUGE)
        
        # Update Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self.prom_memory_usage.set(memory_info.rss)
            self.prom_cpu_usage.set(cpu_percent)
            
    def record_metric(self, name: str, value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None):
        """Record a metric value"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metric_type=metric_type
        )
        
        with self._lock:
            self.metrics_store[name].append(metric)
            
    def record_operation(self, operation: str, duration: float, 
                        success: bool = True, metadata: Dict[str, Any] = None):
        """Record an operation completion"""
        # Record duration
        self.record_metric(f'operation.{operation}.duration', duration, MetricType.HISTOGRAM)
        
        # Record success/failure
        if success:
            self.record_metric(f'operation.{operation}.success', 1, MetricType.COUNTER)
        else:
            self.record_metric(f'operation.{operation}.failure', 1, MetricType.COUNTER)
            
        # Update Prometheus if available
        if PROMETHEUS_AVAILABLE:
            if operation == 'indexing':
                self.prom_indexing_duration.observe(duration)
                if success:
                    self.prom_files_indexed.inc()
            elif operation == 'upload':
                self.prom_upload_duration.observe(duration)
                if success:
                    self.prom_segments_uploaded.inc()
                    
    def record_error(self, component: str, error_type: str, message: str):
        """Record an error occurrence"""
        self.record_metric(f'error.{component}.{error_type}', 1, MetricType.COUNTER)
        
        if PROMETHEUS_AVAILABLE:
            self.prom_errors.labels(component=component, error_type=error_type).inc()
            
        logger.error(f"[{component}] {error_type}: {message}")
        
    def record_throughput(self, mbps: float):
        """Record data throughput"""
        self.record_metric('throughput.mbps', mbps, MetricType.GAUGE)
        
        if PROMETHEUS_AVAILABLE:
            self.prom_throughput.observe(mbps)
            
    def add_alert(self, alert: Alert):
        """Add an alert rule"""
        self.alerts[alert.name] = alert
        logger.info(f"Added alert: {alert.name}")
        
    def _check_alerts(self):
        """Check all alert conditions"""
        for alert_name, alert in self.alerts.items():
            try:
                # Check if alert is in cooldown
                if alert.last_triggered:
                    cooldown_end = alert.last_triggered + timedelta(seconds=alert.cooldown_seconds)
                    if datetime.now() < cooldown_end:
                        continue
                        
                # Evaluate alert condition
                if self._evaluate_alert_condition(alert):
                    self._trigger_alert(alert)
                    
            except Exception as e:
                logger.error(f"Error checking alert {alert_name}: {e}")
                
    def _evaluate_alert_condition(self, alert: Alert) -> bool:
        """Evaluate if alert condition is met"""
        # Parse condition (simple format: metric_name operator threshold)
        parts = alert.condition.split()
        if len(parts) != 3:
            return False
            
        metric_name, operator, _ = parts
        
        # Get recent metric values
        metrics = self.get_metric_values(metric_name, seconds=60)
        if not metrics:
            return False
            
        # Calculate average
        avg_value = statistics.mean(metrics)
        
        # Check condition
        if operator == '>':
            return avg_value > alert.threshold
        elif operator == '<':
            return avg_value < alert.threshold
        elif operator == '>=':
            return avg_value >= alert.threshold
        elif operator == '<=':
            return avg_value <= alert.threshold
        elif operator == '==':
            return avg_value == alert.threshold
            
        return False
        
    def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        alert.last_triggered = datetime.now()
        
        alert_event = {
            'timestamp': alert.last_triggered.isoformat(),
            'name': alert.name,
            'severity': alert.severity,
            'message': alert.message
        }
        
        self.alert_history.append(alert_event)
        
        # Log based on severity
        if alert.severity == 'critical':
            logger.critical(f"ALERT: {alert.message}")
        elif alert.severity == 'warning':
            logger.warning(f"ALERT: {alert.message}")
        else:
            logger.info(f"ALERT: {alert.message}")
            
    def get_metric_values(self, name: str, seconds: int = 60) -> List[float]:
        """Get recent metric values"""
        with self._lock:
            if name not in self.metrics_store:
                return []
                
            cutoff = datetime.now() - timedelta(seconds=seconds)
            values = []
            
            for metric in self.metrics_store[name]:
                if metric.timestamp >= cutoff:
                    values.append(metric.value)
                    
            return values
            
    def get_metric_stats(self, name: str, seconds: int = 300) -> Dict[str, float]:
        """Get statistics for a metric"""
        values = self.get_metric_values(name, seconds)
        
        if not values:
            return {}
            
        return {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'stddev': statistics.stdev(values) if len(values) > 1 else 0,
            'count': len(values)
        }
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': self.get_metric_values('system.cpu_usage', 1)[0] if self.get_metric_values('system.cpu_usage', 1) else 0,
            'memory_mb': self.get_metric_values('system.memory_mb', 1)[0] if self.get_metric_values('system.memory_mb', 1) else 0,
            'threads': self.get_metric_values('system.threads', 1)[0] if self.get_metric_values('system.threads', 1) else 0,
            'connections': self.get_metric_values('system.connections', 1)[0] if self.get_metric_values('system.connections', 1) else 0,
            'alerts_triggered': len([a for a in self.alert_history if 
                                    datetime.fromisoformat(a['timestamp']) > 
                                    datetime.now() - timedelta(hours=1)])
        }
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        return {
            'system_status': self.get_system_status(),
            'metrics': {
                'cpu': self.get_metric_stats('system.cpu_usage'),
                'memory': self.get_metric_stats('system.memory_mb'),
                'throughput': self.get_metric_stats('throughput.mbps'),
            },
            'recent_alerts': list(self.alert_history)[-10:],
            'operation_stats': {
                'indexing': {
                    'success': len(self.get_metric_values('operation.indexing.success', 3600)),
                    'failure': len(self.get_metric_values('operation.indexing.failure', 3600)),
                    'avg_duration': statistics.mean(self.get_metric_values('operation.indexing.duration', 3600) or [0])
                },
                'upload': {
                    'success': len(self.get_metric_values('operation.upload.success', 3600)),
                    'failure': len(self.get_metric_values('operation.upload.failure', 3600)),
                    'avg_duration': statistics.mean(self.get_metric_values('operation.upload.duration', 3600) or [0])
                }
            }
        }
        
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        with self._lock:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {}
            }
            
            for metric_name, metric_deque in self.metrics_store.items():
                export_data['metrics'][metric_name] = [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp.isoformat(),
                        'type': m.metric_type.value
                    }
                    for m in metric_deque
                ]
                
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Metrics exported to {filepath}")
        
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            for metric_name in list(self.metrics_store.keys()):
                # Remove old metrics
                while self.metrics_store[metric_name]:
                    if self.metrics_store[metric_name][0].timestamp < cutoff:
                        self.metrics_store[metric_name].popleft()
                    else:
                        break
                        
                # Remove empty metric stores
                if not self.metrics_store[metric_name]:
                    del self.metrics_store[metric_name]


class MonitoringIntegration:
    """Integration helper for monitoring with unified system"""
    
    def __init__(self, monitoring_system: MonitoringSystem):
        self.monitor = monitoring_system
        
    def wrap_operation(self, operation_name: str):
        """Decorator to monitor operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                result = None
                
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    success = False
                    self.monitor.record_error(
                        operation_name,
                        type(e).__name__,
                        str(e)
                    )
                    raise
                finally:
                    duration = time.time() - start_time
                    self.monitor.record_operation(
                        operation_name,
                        duration,
                        success
                    )
                    
                return result
            return wrapper
        return decorator


def test_monitoring_system():
    """Test monitoring system"""
    print("\n=== Testing Monitoring System ===\n")
    
    # Create monitoring system
    monitor = MonitoringSystem(retention_hours=1)
    
    # Add alerts
    monitor.add_alert(Alert(
        name="high_cpu",
        condition="system.cpu_usage > 80",
        threshold=80,
        severity="warning",
        message="CPU usage is above 80%"
    ))
    
    monitor.add_alert(Alert(
        name="high_memory",
        condition="system.memory_mb > 100",
        threshold=100,
        severity="warning",
        message="Memory usage is above 100MB"
    ))
    
    # Start monitoring
    monitor.start(prometheus_port=0)  # Don't start Prometheus server for test
    
    # Simulate some operations
    print("Simulating operations...")
    
    for i in range(5):
        # Record indexing operation
        monitor.record_operation('indexing', 0.5 + i * 0.1, success=True)
        
        # Record upload operation
        monitor.record_operation('upload', 1.0 + i * 0.2, success=(i != 2))
        
        # Record throughput
        monitor.record_throughput(100 + i * 10)
        
        time.sleep(0.5)
        
    # Get system status
    print("\nSystem Status:")
    status = monitor.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
        
    # Get metric statistics
    print("\nCPU Statistics (last 60 seconds):")
    cpu_stats = monitor.get_metric_stats('system.cpu_usage', 60)
    for key, value in cpu_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
            
    # Get dashboard data
    print("\nDashboard Summary:")
    dashboard = monitor.get_dashboard_data()
    print(f"  Indexing success: {dashboard['operation_stats']['indexing']['success']}")
    print(f"  Upload success: {dashboard['operation_stats']['upload']['success']}")
    print(f"  Upload failures: {dashboard['operation_stats']['upload']['failure']}")
    print(f"  Recent alerts: {len(dashboard['recent_alerts'])}")
    
    # Export metrics
    export_file = "/tmp/monitoring_test.json"
    monitor.export_metrics(export_file)
    print(f"\nMetrics exported to: {export_file}")
    
    # Stop monitoring
    monitor.stop()
    
    print("\n✓ Monitoring system test completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_monitoring_system()