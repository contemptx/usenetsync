#!/usr/bin/env python3
"""
Monitoring and Logging System for UsenetSync
Tracks performance, operations, and system health
"""

import os
import sys
import time
import json
import logging
import threading
import queue
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import gzip
import shutil
from collections import defaultdict, deque

# Performance metrics collection
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"      # Cumulative count
    GAUGE = "gauge"          # Current value
    HISTOGRAM = "histogram"  # Distribution
    RATE = "rate"           # Per-second rate

@dataclass
class Metric:
    """Individual metric"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class PerformanceSnapshot:
    """System performance snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    
@dataclass
class OperationLog:
    """Operation log entry"""
    operation: str
    status: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.retention_hours = retention_hours
        self._lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def record(self, name: str, value: float, type: MetricType = MetricType.COUNTER,
              tags: Optional[Dict[str, str]] = None):
        """Record a metric"""
        metric = Metric(
            name=name,
            type=type,
            value=value,
            tags=tags or {}
        )
        
        with self._lock:
            self.metrics[name].append(metric)
            
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        self.record(name, value, MetricType.COUNTER, tags)
        
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        self.record(name, value, MetricType.GAUGE, tags)
        
    def timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing"""
        self.record(name, duration, MetricType.HISTOGRAM, tags)
        
    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[Metric]:
        """Get metrics by name"""
        with self._lock:
            metrics = self.metrics.get(name, [])
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
                
            return metrics.copy()
            
    def get_aggregate(self, name: str, window_minutes: int = 5) -> Dict[str, float]:
        """Get aggregated metrics"""
        since = datetime.now() - timedelta(minutes=window_minutes)
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return {}
            
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'sum': sum(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1] if values else 0
        }
        
    def get_rate(self, name: str, window_seconds: int = 60) -> float:
        """Calculate rate per second"""
        since = datetime.now() - timedelta(seconds=window_seconds)
        metrics = self.get_metrics(name, since)
        
        if len(metrics) < 2:
            return 0.0
            
        total = sum(m.value for m in metrics)
        duration = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
        
        return total / duration if duration > 0 else 0.0
    
    def get_metric_value(self, name: str, default: float = 0) -> float:
        """Get the last value of a metric"""
        with self._lock:
            if name in self.metrics and self.metrics[name]:
                return self.metrics[name][-1].value
            return default
        
    def _cleanup_loop(self):
        """Clean up old metrics"""
        while True:
            time.sleep(3600)  # Run hourly
            
            cutoff = datetime.now() - timedelta(hours=self.retention_hours)
            
            with self._lock:
                for name in list(self.metrics.keys()):
                    self.metrics[name] = [
                        m for m in self.metrics[name] 
                        if m.timestamp > cutoff
                    ]
                    
                    if not self.metrics[name]:
                        del self.metrics[name]

class PerformanceMonitor:
    """Monitors system performance"""
    
    def __init__(self, interval_seconds: int = 10):
        self.interval = interval_seconds
        self.snapshots: deque[PerformanceSnapshot] = deque(maxlen=360)  # 1 hour at 10s
        self._monitoring = False
        self._thread = None
        self._process = psutil.Process()
        self._last_disk_io = None
        self._last_net_io = None
        
    def start(self):
        """Start monitoring"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=5)
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                snapshot = self._capture_snapshot()
                self.snapshots.append(snapshot)
            except Exception as e:
                logging.error(f"Performance monitoring error: {e}")
                
            time.sleep(self.interval)
            
    def _capture_snapshot(self) -> PerformanceSnapshot:
        """Capture current performance metrics"""
        # CPU and memory
        cpu_percent = self._process.cpu_percent()
        memory_info = self._process.memory_info()
        memory_percent = self._process.memory_percent()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if self._last_disk_io:
            disk_read_mb = (disk_io.read_bytes - self._last_disk_io.read_bytes) / 1024 / 1024
            disk_write_mb = (disk_io.write_bytes - self._last_disk_io.write_bytes) / 1024 / 1024
        else:
            disk_read_mb = disk_write_mb = 0
        self._last_disk_io = disk_io
        
        # Network I/O
        net_io = psutil.net_io_counters()
        if self._last_net_io:
            net_sent_mb = (net_io.bytes_sent - self._last_net_io.bytes_sent) / 1024 / 1024
            net_recv_mb = (net_io.bytes_recv - self._last_net_io.bytes_recv) / 1024 / 1024
        else:
            net_sent_mb = net_recv_mb = 0
        self._last_net_io = net_io
        
        # Thread count
        thread_count = threading.active_count()
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            active_threads=thread_count
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.snapshots:
            return {
                'cpu': {'current': 0, 'avg': 0},
                'memory': {'percent': 0, 'mb': 0},
                'disk': {'percent': 0}
            }
        
        latest = self.snapshots[-1]
        recent = list(self.snapshots)[-10:]  # Last 10 snapshots
        
        return {
            'cpu': {
                'current': latest.cpu_percent,
                'avg': sum(s.cpu_percent for s in recent) / len(recent)
            },
            'memory': {
                'percent': latest.memory_percent,
                'mb': latest.memory_mb
            },
            'disk': {
                'percent': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                'read_mb': latest.disk_io_read_mb,
                'write_mb': latest.disk_io_write_mb
            },
            'network': {
                'sent_mb': latest.network_sent_mb,
                'recv_mb': latest.network_recv_mb
            },
            'threads': latest.active_threads
        }
        
    def get_current_stats(self) -> Optional[PerformanceSnapshot]:
        """Get most recent snapshot"""
        return self.snapshots[-1] if self.snapshots else None
        
    def get_average_stats(self, minutes: int = 5) -> Dict[str, float]:
        """Get average stats over time window"""
        if not self.snapshots:
            return {}
            
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [s for s in self.snapshots if s.timestamp > cutoff]
        
        if not recent:
            return {}
            
        return {
            'cpu_percent': sum(s.cpu_percent for s in recent) / len(recent),
            'memory_mb': sum(s.memory_mb for s in recent) / len(recent),
            'disk_read_mb': sum(s.disk_io_read_mb for s in recent),
            'disk_write_mb': sum(s.disk_io_write_mb for s in recent),
            'network_sent_mb': sum(s.network_sent_mb for s in recent),
            'network_recv_mb': sum(s.network_recv_mb for s in recent),
            'active_threads': sum(s.active_threads for s in recent) / len(recent)
        }

class StructuredLogger:
    """Structured logging with JSON output"""
    
    def __init__(self, name: str, log_dir: str, max_size_mb: int = 50):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        self._setup_file_handler()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
    def _setup_file_handler(self):
        """Setup file handler with rotation"""
        log_file = self.log_dir / f"{self.name}.log"
        
        # Check if rotation needed
        if log_file.exists() and log_file.stat().st_size > self.max_size_mb * 1024 * 1024:
            self._rotate_log(log_file)
            
        # Create handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # JSON formatter
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)
        
    def _rotate_log(self, log_file: Path):
        """Rotate log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{self.name}_{timestamp}.log.gz"
        archive_path = self.log_dir / archive_name
        
        # Compress old log
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
        # Clear log file
        log_file.unlink()
        
        # Clean old archives
        self._clean_old_archives()
        
    def _clean_old_archives(self, keep_days: int = 7):
        """Clean old log archives"""
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        for archive in self.log_dir.glob(f"{self.name}_*.log.gz"):
            if archive.stat().st_mtime < cutoff.timestamp():
                archive.unlink()
                
    def log_operation(self, operation: str, status: str, duration: float,
                     details: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Log an operation"""
        log_entry = OperationLog(
            operation=operation,
            status=status,
            duration=duration,
            details=details or {},
            error=error
        )
        
        log_data = asdict(log_entry)
        log_data['timestamp'] = log_entry.timestamp.isoformat()
        
        if status == 'success':
            self.logger.info(json.dumps(log_data))
        elif status == 'failed':
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.warning(json.dumps(log_data))

class JsonFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

class OperationTracker:
    """Tracks long-running operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize operations database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE,
                    operation_type TEXT,
                    status TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds REAL,
                    details TEXT,
                    error TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_operations_type 
                ON operations(operation_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_operations_status 
                ON operations(status)
            """)
            
    def start_operation(self, operation_id: str, operation_type: str,
                       details: Optional[Dict[str, Any]] = None):
        """Start tracking an operation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO operations 
                (operation_id, operation_type, status, started_at, details)
                VALUES (?, ?, 'running', ?, ?)
            """, (
                operation_id,
                operation_type,
                datetime.now(),
                json.dumps(details or {})
            ))
            
    def complete_operation(self, operation_id: str, status: str = 'completed',
                          error: Optional[str] = None):
        """Complete an operation"""
        with sqlite3.connect(self.db_path) as conn:
            # Get start time
            cursor = conn.execute("""
                SELECT started_at FROM operations WHERE operation_id = ?
            """, (operation_id,))
            
            row = cursor.fetchone()
            if row:
                started_at = datetime.fromisoformat(row[0])
                duration = (datetime.now() - started_at).total_seconds()
                
                conn.execute("""
                    UPDATE operations 
                    SET status = ?, completed_at = ?, duration_seconds = ?, error = ?
                    WHERE operation_id = ?
                """, (status, datetime.now(), duration, error, operation_id))
                
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM operations WHERE operation_id = ?
            """, (operation_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
    def get_operation_history(self, operation_type: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get operation history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if operation_type:
                cursor = conn.execute("""
                    SELECT * FROM operations 
                    WHERE operation_type = ?
                    ORDER BY started_at DESC
                    LIMIT ?
                """, (operation_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM operations 
                    ORDER BY started_at DESC
                    LIMIT ?
                """, (limit,))
                
            return [dict(row) for row in cursor]

class MonitoringSystem:
    """
    Main monitoring system integrating all components
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.metrics = MetricsCollector(
            retention_hours=config.get('metrics_retention_hours', 24)
        )
        
        self.performance = PerformanceMonitor(
            interval_seconds=config.get('performance_interval', 10)
        )
        
        self.logger = StructuredLogger(
            name='usenetsync',
            log_dir=config.get('log_directory', './logs'),
            max_size_mb=config.get('max_log_size_mb', 50)
        )
        
        self.operations = OperationTracker(
            db_path=config.get('operations_db', './data/operations.db')
        )
        
        # Alert thresholds
        self.alert_thresholds = config.get('alert_thresholds', {
            'cpu_percent': 80,
            'memory_percent': 90,
            'error_rate': 0.1,
            'response_time': 5.0
        })
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Start monitoring
        self.performance.start()
        
        # Alert checking thread
        self._alert_thread = threading.Thread(target=self._check_alerts_loop, daemon=True)
        self._alert_thread.start()
        
    def record_metric(self, name: str, value: float, type: MetricType = MetricType.COUNTER,
                     tags: Optional[Dict[str, str]] = None):
        """Record a metric"""
        self.metrics.record(name, value, type, tags)
        
    def track_operation(self, operation_id: str, operation_type: str):
        """Context manager for tracking operations"""
        return OperationContext(self, operation_id, operation_type)
        
    def log_event(self, event: str, level: str = 'info', **kwargs):
        """Log an event"""
        log_method = getattr(self.logger.logger, level, self.logger.logger.info)
        log_data = {'event': event, **kwargs}
        log_method(json.dumps(log_data))
        
    def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics"""
        return {
            'total_uploads': self.metrics.get_metric_value('uploads.total', 0),
            'bytes_uploaded': self.metrics.get_metric_value('uploads.bytes', 0),
            'success_rate': self.metrics.get_metric_value('uploads.success_rate', 100.0),
            'active_sessions': self.metrics.get_metric_value('uploads.active_sessions', 0)
        }
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        return {
            'total_downloads': self.metrics.get_metric_value('downloads.total', 0),
            'bytes_downloaded': self.metrics.get_metric_value('downloads.bytes', 0),
            'success_rate': self.metrics.get_metric_value('downloads.success_rate', 100.0),
            'active_sessions': self.metrics.get_metric_value('downloads.active_sessions', 0)
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        perf_stats = self.performance.get_stats()
        return {
            'database': 'healthy',
            'nntp': 'healthy',
            'storage': 'healthy',
            'cpu_usage': perf_stats.get('cpu', {}).get('current', 0),
            'memory_usage': perf_stats.get('memory', {}).get('percent', 0),
            'disk_usage': perf_stats.get('disk', {}).get('percent', 0)
        }
        
    def _check_alerts_loop(self):
        """Check for alert conditions"""
        while True:
            try:
                self._check_alerts()
            except Exception as e:
                self.logger.logger.error(f"Alert check error: {e}")
                
            time.sleep(60)  # Check every minute
            
    def _check_alerts(self):
        """Check alert conditions"""
        alerts = []
        
        # Performance alerts
        current_perf = self.performance.get_current_stats()
        if current_perf:
            if current_perf.cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f"High CPU usage: {current_perf.cpu_percent:.1f}%",
                    'value': current_perf.cpu_percent
                })
                
            if current_perf.memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'critical',
                    'message': f"High memory usage: {current_perf.memory_percent:.1f}%",
                    'value': current_perf.memory_percent
                })
                
        # Error rate alerts
        error_rate = self.metrics.get_rate('errors', window_seconds=300)
        total_rate = self.metrics.get_rate('operations', window_seconds=300)
        
        if total_rate > 0:
            error_percentage = (error_rate / total_rate) * 100
            if error_percentage > self.alert_thresholds['error_rate'] * 100:
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'critical',
                    'message': f"High error rate: {error_percentage:.1f}%",
                    'value': error_percentage
                })
                
        # Trigger callbacks
        for alert in alerts:
            self.log_event('alert_triggered', level='warning', **alert)
            
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.logger.error(f"Alert callback error: {e}")
                    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        # Current performance
        current_perf = self.performance.get_current_stats()
        avg_perf = self.performance.get_average_stats(minutes=5)
        
        # Operation metrics
        operations_total = self.metrics.get_aggregate('operations', window_minutes=60)
        operations_success = self.metrics.get_aggregate('operations.success', window_minutes=60)
        operations_failed = self.metrics.get_aggregate('operations.failed', window_minutes=60)
        
        # Upload/Download metrics
        upload_bytes = self.metrics.get_aggregate('upload.bytes', window_minutes=60)
        download_bytes = self.metrics.get_aggregate('download.bytes', window_minutes=60)
        
        # Recent operations
        recent_ops = self.operations.get_operation_history(limit=10)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance': {
                'current': asdict(current_perf) if current_perf else None,
                'average': avg_perf
            },
            'operations': {
                'total': operations_total.get('count', 0),
                'success': operations_success.get('count', 0),
                'failed': operations_failed.get('count', 0),
                'success_rate': (
                    operations_success.get('count', 0) / operations_total.get('count', 1) * 100
                    if operations_total.get('count', 0) > 0 else 0
                )
            },
            'throughput': {
                'upload_mb': upload_bytes.get('sum', 0) / 1024 / 1024,
                'download_mb': download_bytes.get('sum', 0) / 1024 / 1024,
                'upload_rate_mbps': self.metrics.get_rate('upload.bytes') / 1024 / 1024,
                'download_rate_mbps': self.metrics.get_rate('download.bytes') / 1024 / 1024
            },
            'recent_operations': recent_ops
        }
        
    def generate_report(self, output_path: str, period_hours: int = 24):
        """Generate monitoring report"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'period_hours': period_hours,
            'system_info': {
                'platform': sys.platform,
                'python_version': sys.version,
                'process_id': os.getpid()
            }
        }
        
        # Performance summary
        since = datetime.now() - timedelta(hours=period_hours)
        perf_snapshots = [s for s in self.performance.snapshots if s.timestamp > since]
        
        if perf_snapshots:
            report_data['performance_summary'] = {
                'avg_cpu': sum(s.cpu_percent for s in perf_snapshots) / len(perf_snapshots),
                'max_cpu': max(s.cpu_percent for s in perf_snapshots),
                'avg_memory_mb': sum(s.memory_mb for s in perf_snapshots) / len(perf_snapshots),
                'max_memory_mb': max(s.memory_mb for s in perf_snapshots),
                'total_disk_read_mb': sum(s.disk_io_read_mb for s in perf_snapshots),
                'total_disk_write_mb': sum(s.disk_io_write_mb for s in perf_snapshots),
                'total_network_sent_mb': sum(s.network_sent_mb for s in perf_snapshots),
                'total_network_recv_mb': sum(s.network_recv_mb for s in perf_snapshots)
            }
            
        # Operation summary
        operations = self.operations.get_operation_history(limit=1000)
        recent_ops = [op for op in operations if op['started_at'] and 
                     datetime.fromisoformat(op['started_at']) > since]
        
        op_summary = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        for op in recent_ops:
            op_type = op['operation_type']
            op_summary[op_type]['total'] += 1
            if op['status'] == 'completed':
                op_summary[op_type]['success'] += 1
            elif op['status'] == 'failed':
                op_summary[op_type]['failed'] += 1
                
        report_data['operation_summary'] = dict(op_summary)
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Generate charts if matplotlib available
        if MATPLOTLIB_AVAILABLE:
            self._generate_charts(perf_snapshots, output_path)
            
    def _generate_charts(self, snapshots: List[PerformanceSnapshot], base_path: str):
        """Generate performance charts"""
        if not snapshots:
            return
            
        timestamps = [s.timestamp for s in snapshots]
        
        # CPU usage chart
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, [s.cpu_percent for s in snapshots])
        plt.title('CPU Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('CPU %')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(base_path.replace('.json', '_cpu.png'))
        plt.close()
        
        # Memory usage chart
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, [s.memory_mb for s in snapshots])
        plt.title('Memory Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Memory (MB)')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(base_path.replace('.json', '_memory.png'))
        plt.close()
        
    def shutdown(self):
        """Shutdown monitoring system"""
        self.performance.stop()

class OperationContext:
    """Context manager for operation tracking"""
    
    def __init__(self, monitor: MonitoringSystem, operation_id: str, operation_type: str):
        self.monitor = monitor
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.monitor.operations.start_operation(self.operation_id, self.operation_type)
        self.monitor.metrics.increment('operations')
        self.monitor.metrics.increment(f'operations.{self.operation_type}')
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            status = 'completed'
            self.monitor.metrics.increment('operations.success')
            self.monitor.metrics.increment(f'operations.{self.operation_type}.success')
        else:
            status = 'failed'
            self.monitor.metrics.increment('operations.failed')
            self.monitor.metrics.increment(f'operations.{self.operation_type}.failed')
            
        self.monitor.operations.complete_operation(
            self.operation_id,
            status,
            str(exc_val) if exc_val else None
        )
        
        self.monitor.metrics.timing('operation.duration', duration)
        self.monitor.metrics.timing(f'operation.{self.operation_type}.duration', duration)
        
        self.monitor.logger.log_operation(
            self.operation_type,
            status,
            duration,
            {'operation_id': self.operation_id},
            str(exc_val) if exc_val else None
        )

def create_monitoring_system(config: Dict[str, Any]) -> MonitoringSystem:
    """Create and configure monitoring system"""
    return MonitoringSystem(config)