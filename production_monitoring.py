#!/usr/bin/env python3
"""
Production Monitoring System for UsenetSync
Real-time system monitoring, alerting, and automatic recovery
"""

import os
import sys
import json
import time
import psutil
import threading
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics to monitor"""
    SYSTEM = "system"
    APPLICATION = "application"
    USENET = "usenet"
    DATABASE = "database"
    PERFORMANCE = "performance"

@dataclass
class Alert:
    """System alert"""
    timestamp: datetime
    level: AlertLevel
    category: str
    message: str
    metric_name: str
    current_value: Any
    threshold: Any
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class Metric:
    """System metric"""
    name: str
    value: Any
    timestamp: datetime
    metric_type: MetricType
    unit: str = ""
    tags: Dict[str, str] = None

class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_percent': 85.0,
            'memory_percent': 90.0,
            'disk_percent': 85.0,
            'disk_io_read_mb_s': 100.0,
            'disk_io_write_mb_s': 100.0,
            'network_io_mb_s': 50.0,
            'process_memory_mb': 1024.0,
            'process_cpu_percent': 50.0
        }
    
    def get_system_metrics(self) -> List[Metric]:
        """Get current system metrics"""
        metrics = []
        now = datetime.now()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(Metric(
                name="cpu_percent",
                value=cpu_percent,
                timestamp=now,
                metric_type=MetricType.SYSTEM,
                unit="%"
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append(Metric(
                name="memory_percent",
                value=memory.percent,
                timestamp=now,
                metric_type=MetricType.SYSTEM,
                unit="%"
            ))
            
            metrics.append(Metric(
                name="memory_available_gb",
                value=memory.available / (1024**3),
                timestamp=now,
                metric_type=MetricType.SYSTEM,
                unit="GB"
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(Metric(
                name="disk_percent",
                value=disk_percent,
                timestamp=now,
                metric_type=MetricType.SYSTEM,
                unit="%"
            ))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # Calculate rates (simplified)
                metrics.append(Metric(
                    name="disk_read_bytes",
                    value=disk_io.read_bytes,
                    timestamp=now,
                    metric_type=MetricType.SYSTEM,
                    unit="bytes"
                ))
                
                metrics.append(Metric(
                    name="disk_write_bytes",
                    value=disk_io.write_bytes,
                    timestamp=now,
                    metric_type=MetricType.SYSTEM,
                    unit="bytes"
                ))
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.append(Metric(
                    name="network_bytes_sent",
                    value=network_io.bytes_sent,
                    timestamp=now,
                    metric_type=MetricType.SYSTEM,
                    unit="bytes"
                ))
                
                metrics.append(Metric(
                    name="network_bytes_recv",
                    value=network_io.bytes_recv,
                    timestamp=now,
                    metric_type=MetricType.SYSTEM,
                    unit="bytes"
                ))
            
            # Process-specific metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info().rss / (1024**2)  # MB
            process_cpu = current_process.cpu_percent()
            
            metrics.append(Metric(
                name="process_memory_mb",
                value=process_memory,
                timestamp=now,
                metric_type=MetricType.APPLICATION,
                unit="MB"
            ))
            
            metrics.append(Metric(
                name="process_cpu_percent",
                value=process_cpu,
                timestamp=now,
                metric_type=MetricType.APPLICATION,
                unit="%"
            ))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def check_thresholds(self, metrics: List[Metric]) -> List[Alert]:
        """Check metrics against thresholds"""
        alerts = []
        
        for metric in metrics:
            if metric.name in self.thresholds:
                threshold = self.thresholds[metric.name]
                
                if isinstance(metric.value, (int, float)) and metric.value > threshold:
                    level = AlertLevel.WARNING
                    if metric.value > threshold * 1.2:  # 20% over threshold
                        level = AlertLevel.ERROR
                    if metric.value > threshold * 1.5:  # 50% over threshold
                        level = AlertLevel.CRITICAL
                    
                    alert = Alert(
                        timestamp=metric.timestamp,
                        level=level,
                        category="system",
                        message=f"{metric.name} is {metric.value}{metric.unit} (threshold: {threshold}{metric.unit})",
                        metric_name=metric.name,
                        current_value=metric.value,
                        threshold=threshold
                    )
                    alerts.append(alert)
        
        return alerts

class ApplicationMonitor:
    """Monitors UsenetSync application health"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.health_checks = []
        self.setup_health_checks()
    
    def setup_health_checks(self):
        """Setup application health checks"""
        self.health_checks = [
            {
                'name': 'database_connection',
                'function': self.check_database_connection,
                'critical': True
            },
            {
                'name': 'nntp_connection',
                'function': self.check_nntp_connection,
                'critical': True
            },
            {
                'name': 'file_system_access',
                'function': self.check_file_system_access,
                'critical': True
            },
            {
                'name': 'upload_queue_health',
                'function': self.check_upload_queue_health,
                'critical': False
            },
            {
                'name': 'download_system_health',
                'function': self.check_download_system_health,
                'critical': False
            },
            {
                'name': 'security_system_health',
                'function': self.check_security_system_health,
                'critical': True
            }
        ]
    
    def check_database_connection(self) -> Dict:
        """Check database connectivity"""
        try:
            db_path = self.project_root / "data" / "usenetsync.db"
            if not db_path.exists():
                return {'healthy': False, 'error': 'Database file not found'}
            
            with sqlite3.connect(str(db_path), timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                if table_count < 5:  # Expect at least 5 core tables
                    return {'healthy': False, 'error': f'Insufficient tables: {table_count}'}
                
                return {'healthy': True, 'tables': table_count}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def check_nntp_connection(self) -> Dict:
        """Check NNTP server connectivity"""
        try:
            # Try to import and test NNTP client
            sys.path.insert(0, str(self.project_root))
            
            try:
                from production_nntp_client import ProductionNNTPClient
                # Quick connection test (would need actual config)
                return {'healthy': True, 'status': 'NNTP client available'}
            except ImportError:
                return {'healthy': False, 'error': 'NNTP client not available'}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def check_file_system_access(self) -> Dict:
        """Check file system access"""
        try:
            # Check critical directories
            critical_dirs = ['data', 'logs', 'temp']
            
            for dir_name in critical_dirs:
                dir_path = self.project_root / dir_name
                
                # Check if directory exists and is writable
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                
                # Test write access
                test_file = dir_path / f"health_check_{int(time.time())}.tmp"
                try:
                    test_file.write_text("health check")
                    test_file.unlink()
                except Exception as e:
                    return {'healthy': False, 'error': f'Cannot write to {dir_name}: {e}'}
            
            return {'healthy': True, 'directories_checked': len(critical_dirs)}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def check_upload_queue_health(self) -> Dict:
        """Check upload queue health"""
        try:
            # This would integrate with your upload queue manager
            # For now, just check if the module can be imported
            sys.path.insert(0, str(self.project_root))
            
            try:
                from upload_queue_manager import SmartQueueManager
                return {'healthy': True, 'status': 'Upload queue manager available'}
            except ImportError:
                return {'healthy': False, 'error': 'Upload queue manager not available'}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def check_download_system_health(self) -> Dict:
        """Check download system health"""
        try:
            sys.path.insert(0, str(self.project_root))
            
            try:
                from enhanced_download_system import EnhancedDownloadSystem
                return {'healthy': True, 'status': 'Download system available'}
            except ImportError:
                return {'healthy': False, 'error': 'Download system not available'}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def check_security_system_health(self) -> Dict:
        """Check security system health"""
        try:
            sys.path.insert(0, str(self.project_root))
            
            try:
                from enhanced_security_system import EnhancedSecuritySystem
                return {'healthy': True, 'status': 'Security system available'}
            except ImportError:
                return {'healthy': False, 'error': 'Security system not available'}
        
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    def run_health_checks(self) -> Dict:
        """Run all health checks"""
        results = {
            'overall_healthy': True,
            'timestamp': datetime.now(),
            'checks': {},
            'critical_failures': 0,
            'total_checks': len(self.health_checks)
        }
        
        for check in self.health_checks:
            try:
                result = check['function']()
                results['checks'][check['name']] = {
                    'healthy': result['healthy'],
                    'critical': check['critical'],
                    'result': result
                }
                
                if not result['healthy']:
                    if check['critical']:
                        results['critical_failures'] += 1
                        results['overall_healthy'] = False
                    logger.warning(f"Health check failed: {check['name']} - {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                results['checks'][check['name']] = {
                    'healthy': False,
                    'critical': check['critical'],
                    'result': {'healthy': False, 'error': f'Health check exception: {e}'}
                }
                
                if check['critical']:
                    results['critical_failures'] += 1
                    results['overall_healthy'] = False
                
                logger.error(f"Health check exception: {check['name']} - {e}")
        
        return results

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.alerts_db = self.setup_alerts_database()
        self.notification_handlers = []
        self.setup_notification_handlers()
    
    def setup_alerts_database(self) -> str:
        """Setup alerts database"""
        db_path = Path("monitoring_alerts.db")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_name TEXT,
                current_value TEXT,
                threshold TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    def setup_notification_handlers(self):
        """Setup notification handlers"""
        # Email notifications
        if self.config.get('email', {}).get('enabled', False):
            self.notification_handlers.append(self.send_email_notification)
        
        # File logging
        self.notification_handlers.append(self.log_alert_to_file)
        
        # Console output
        self.notification_handlers.append(self.log_alert_to_console)
    
    def store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.alerts_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts (
                    timestamp, level, category, message, metric_name,
                    current_value, threshold, resolved, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.category,
                alert.message,
                alert.metric_name,
                str(alert.current_value),
                str(alert.threshold),
                1 if alert.resolved else 0,
                alert.resolved_at.isoformat() if alert.resolved_at else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    def send_alert(self, alert: Alert):
        """Send alert through all configured channels"""
        self.store_alert(alert)
        
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {handler.__name__}: {e}")
    
    def send_email_notification(self, alert: Alert):
        """Send email notification"""
        email_config = self.config.get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = email_config['to_address']
            msg['Subject'] = f"UsenetSync Alert - {alert.level.value.upper()}: {alert.category}"
            
            body = f"""
            Alert Details:
            - Level: {alert.level.value.upper()}
            - Category: {alert.category}
            - Message: {alert.message}
            - Time: {alert.timestamp}
            - Metric: {alert.metric_name}
            - Current Value: {alert.current_value}
            - Threshold: {alert.threshold}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls', True):
                server.starttls()
            
            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def log_alert_to_file(self, alert: Alert):
        """Log alert to file"""
        try:
            log_file = Path("monitoring_alerts.log")
            
            with open(log_file, 'a') as f:
                f.write(f"{alert.timestamp.isoformat()} - {alert.level.value.upper()} - {alert.category} - {alert.message}\n")
        
        except Exception as e:
            logger.error(f"Failed to log alert to file: {e}")
    
    def log_alert_to_console(self, alert: Alert):
        """Log alert to console"""
        level_colors = {
            AlertLevel.INFO: '\033[94m',      # Blue
            AlertLevel.WARNING: '\033[93m',   # Yellow
            AlertLevel.ERROR: '\033[91m',     # Red
            AlertLevel.CRITICAL: '\033[95m'   # Magenta
        }
        
        reset_color = '\033[0m'
        color = level_colors.get(alert.level, reset_color)
        
        print(f"{color}[{alert.level.value.upper()}] {alert.timestamp.strftime('%H:%M:%S')} - {alert.category}: {alert.message}{reset_color}")

class ProductionMonitoringSystem:
    """Main production monitoring system"""
    
    def __init__(self, project_root: str = None, config_file: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config = self.load_config(config_file)
        
        self.system_monitor = SystemMonitor()
        self.app_monitor = ApplicationMonitor(self.project_root)
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        
        self.monitoring = False
        self.monitor_thread = None
        
        # Performance tracking
        self.metrics_history = []
        self.max_history_size = 1000
    
    def load_config(self, config_file: str = None) -> Dict:
        """Load monitoring configuration"""
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            'monitoring': {
                'interval_seconds': 30,
                'system_monitoring': True,
                'application_monitoring': True,
                'auto_recovery': True
            },
            'alerts': {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_tls': True,
                    'from_address': '',
                    'to_address': '',
                    'username': '',
                    'password': ''
                }
            },
            'thresholds': {
                'cpu_percent': 85.0,
                'memory_percent': 90.0,
                'disk_percent': 85.0
            },
            'recovery': {
                'restart_on_critical': False,
                'max_restart_attempts': 3,
                'restart_cooldown_minutes': 5
            }
        }
    
    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring:
            logger.warning("Monitoring already running")
            return
        
        logger.info("Starting production monitoring system...")
        self.monitoring = True
        
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Production monitoring system started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.monitoring:
            return
        
        logger.info("Stopping production monitoring system...")
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Production monitoring system stopped")
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        interval = self.config['monitoring']['interval_seconds']
        
        while self.monitoring:
            try:
                # Collect system metrics
                if self.config['monitoring']['system_monitoring']:
                    system_metrics = self.system_monitor.get_system_metrics()
                    self.metrics_history.extend(system_metrics)
                    
                    # Check thresholds
                    system_alerts = self.system_monitor.check_thresholds(system_metrics)
                    for alert in system_alerts:
                        self.alert_manager.send_alert(alert)
                
                # Run application health checks
                if self.config['monitoring']['application_monitoring']:
                    health_results = self.app_monitor.run_health_checks()
                    
                    if not health_results['overall_healthy']:
                        alert = Alert(
                            timestamp=datetime.now(),
                            level=AlertLevel.CRITICAL if health_results['critical_failures'] > 0 else AlertLevel.WARNING,
                            category="application",
                            message=f"Application health check failed: {health_results['critical_failures']} critical failures",
                            metric_name="health_check",
                            current_value=health_results['critical_failures'],
                            threshold=0
                        )
                        self.alert_manager.send_alert(alert)
                        
                        # Auto-recovery attempt
                        if self.config['monitoring']['auto_recovery']:
                            self.attempt_auto_recovery(health_results)
                
                # Cleanup old metrics
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
            
            time.sleep(interval)
    
    def attempt_auto_recovery(self, health_results: Dict):
        """Attempt automatic recovery from health check failures"""
        logger.info("Attempting auto-recovery...")
        
        recovery_actions = {
            'database_connection': self.recover_database_connection,
            'file_system_access': self.recover_file_system_access
        }
        
        for check_name, check_result in health_results['checks'].items():
            if not check_result['healthy'] and check_name in recovery_actions:
                try:
                    recovery_actions[check_name]()
                    logger.info(f"Auto-recovery attempted for {check_name}")
                except Exception as e:
                    logger.error(f"Auto-recovery failed for {check_name}: {e}")
    
    def recover_database_connection(self):
        """Attempt to recover database connection"""
        db_path = self.project_root / "data" / "usenetsync.db"
        
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to create/repair database
        try:
            with sqlite3.connect(str(db_path), timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                logger.info("Database connection recovered")
        except Exception as e:
            logger.error(f"Failed to recover database connection: {e}")
    
    def recover_file_system_access(self):
        """Attempt to recover file system access"""
        critical_dirs = ['data', 'logs', 'temp']
        
        for dir_name in critical_dirs:
            dir_path = self.project_root / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                # Set permissions if needed (Unix-like systems)
                if hasattr(os, 'chmod'):
                    os.chmod(dir_path, 0o755)
            except Exception as e:
                logger.error(f"Failed to recover access to {dir_name}: {e}")
    
    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        # Run health checks
        health_results = self.app_monitor.run_health_checks()
        
        # Get recent metrics
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(minutes=5)]
        
        # Get recent alerts
        recent_alerts = self.get_recent_alerts(hours=1)
        
        return {
            'monitoring_active': self.monitoring,
            'timestamp': datetime.now().isoformat(),
            'health_check': health_results,
            'recent_metrics_count': len(recent_metrics),
            'recent_alerts_count': len(recent_alerts),
            'system_status': 'healthy' if health_results['overall_healthy'] else 'unhealthy'
        }
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts from database"""
        try:
            conn = sqlite3.connect(self.alert_manager.alerts_db)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            columns = [desc[0] for desc in cursor.description]
            alerts = []
            
            for row in cursor.fetchall():
                alert_dict = dict(zip(columns, row))
                alerts.append(alert_dict)
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Monitoring System')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start monitoring
    start_parser = subparsers.add_parser('start', help='Start monitoring')
    start_parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    start_parser.add_argument('--config', help='Configuration file')
    
    # Status check
    status_parser = subparsers.add_parser('status', help='Get status report')
    status_parser.add_argument('--config', help='Configuration file')
    
    # Health check
    health_parser = subparsers.add_parser('health', help='Run health checks')
    health_parser.add_argument('--config', help='Configuration file')
    
    # Alerts
    alerts_parser = subparsers.add_parser('alerts', help='Show recent alerts')
    alerts_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    
    # Global options
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        monitor = ProductionMonitoringSystem(
            project_root=args.project_root,
            config_file=getattr(args, 'config', None)
        )
        
        if args.command == 'start':
            monitor.start_monitoring()
            
            if args.daemon:
                logger.info("Running in daemon mode - press Ctrl+C to stop")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                logger.info("Monitoring started - use 'stop' or Ctrl+C to stop")
                input("Press Enter to stop monitoring...")
            
            monitor.stop_monitoring()
            
        elif args.command == 'status':
            status = monitor.get_status_report()
            print(json.dumps(status, indent=2, default=str))
            
        elif args.command == 'health':
            health = monitor.app_monitor.run_health_checks()
            print(json.dumps(health, indent=2, default=str))
            print(f"\nOverall Health: {'HEALTHY' if health['overall_healthy'] else 'UNHEALTHY'}")
            
        elif args.command == 'alerts':
            alerts = monitor.get_recent_alerts(args.hours)
            print(f"Recent alerts ({args.hours} hours):")
            for alert in alerts:
                print(f"  {alert['timestamp']} - {alert['level'].upper()} - {alert['message']}")
        
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
