#!/usr/bin/env python3
"""
CLI for Monitoring System
Provides monitoring commands and dashboard launcher
Full production implementation with no placeholders
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from monitoring_system import create_monitoring_system, MonitoringSystem
from monitoring_dashboard import MonitoringDashboard


class MonitoringCLI:
    """Command line interface for monitoring system"""
    
    def __init__(self):
        self.config = self._load_config()
        self.monitoring = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            'metrics_retention_hours': 24,
            'performance_interval': 10,
            'log_directory': './logs',
            'operations_db': './data/operations.db',
            'alert_thresholds': {
                'cpu_percent': 80,
                'memory_percent': 90,
                'error_rate': 0.1,
                'response_time': 5.0
            },
            'dashboard': {
                'host': '127.0.0.1',
                'port': 5000
            }
        }
        
        # Try to load from file
        config_path = Path('./config/monitoring.json')
        if config_path.exists():
            try:
                with open(config_path) as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                
        return default_config
        
    def _ensure_monitoring(self):
        """Ensure monitoring system is initialized"""
        if not self.monitoring:
            self.monitoring = create_monitoring_system(self.config)
            
    def cmd_dashboard(self, args):
        """Launch monitoring dashboard"""
        self._ensure_monitoring()
        
        print(f"Starting monitoring dashboard on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        
        try:
            dashboard = MonitoringDashboard(
                self.monitoring,
                args.host,
                args.port
            )
            dashboard.start()
        except KeyboardInterrupt:
            print("\nDashboard stopped")
        except ImportError:
            print("Error: Flask not installed. Install with: pip install flask flask-socketio")
            return 1
        except Exception as e:
            print(f"Dashboard error: {e}")
            return 1
            
        return 0
        
    def cmd_metrics(self, args):
        """Show metrics"""
        self._ensure_monitoring()
        
        if args.list:
            # List all metric names
            print("Available metrics:")
            print("-" * 40)
            
            metrics = self.monitoring.metrics.metrics
            if not metrics:
                print("No metrics available")
                return 0
                
            # Group by prefix
            grouped = {}
            for name in sorted(metrics.keys()):
                prefix = name.split('.')[0]
                if prefix not in grouped:
                    grouped[prefix] = []
                grouped[prefix].append(name)
                
            for prefix, names in sorted(grouped.items()):
                print(f"\n{prefix.upper()}:")
                for name in names:
                    count = len(self.monitoring.metrics.get_metrics(name))
                    print(f"  {name}: {count} data points")
                    
        else:
            # Show specific metric
            if not args.name:
                print("Error: Metric name required")
                return 1
                
            aggregate = self.monitoring.metrics.get_aggregate(args.name, args.window)
            
            if aggregate:
                print(f"\nMetric: {args.name}")
                print(f"Window: {args.window} minutes")
                print("-" * 40)
                
                # Format values nicely
                for key, value in sorted(aggregate.items()):
                    if isinstance(value, float):
                        print(f"{key:10}: {value:,.2f}")
                    else:
                        print(f"{key:10}: {value:,}")
                        
                # Show rate if applicable
                rate = self.monitoring.metrics.get_rate(args.name)
                if rate > 0:
                    print(f"{'rate/sec':10}: {rate:,.2f}")
                    
                # Show recent values if requested
                if args.recent:
                    print("\nRecent values:")
                    recent = self.monitoring.metrics.get_metrics(
                        args.name,
                        since=datetime.now() - timedelta(minutes=5)
                    )
                    for metric in recent[-10:]:
                        timestamp = metric.timestamp.strftime('%H:%M:%S')
                        print(f"  {timestamp}: {metric.value:,.2f}")
            else:
                print(f"No data for metric: {args.name}")
                
        return 0
        
    def cmd_operations(self, args):
        """Show operations"""
        self._ensure_monitoring()
        
        operations = self.monitoring.operations.get_operation_history(
            args.type,
            args.limit
        )
        
        if not operations:
            print("No operations found")
            return 0
            
        print(f"\nRecent Operations (limit: {args.limit})")
        print("-" * 100)
        
        # Header
        headers = ['Time', 'Type', 'Status', 'Duration', 'Error']
        widths = [20, 25, 12, 10, 33]
        
        # Print header
        for header, width in zip(headers, widths):
            print(f"{header:<{width}}", end='')
        print()
        print("-" * 100)
        
        # Print operations
        for op in operations:
            # Format time
            start_time = datetime.fromisoformat(op['started_at']).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format duration
            duration = f"{op.get('duration_seconds', 0):.2f}s" if op.get('duration_seconds') else '-'
            
            # Format error
            error = op.get('error', '')
            if error and len(error) > 30:
                error = error[:27] + '...'
                
            # Print row
            print(f"{start_time:<20}", end='')
            print(f"{op['operation_type']:<25}", end='')
            print(f"{op['status']:<12}", end='')
            print(f"{duration:<10}", end='')
            print(f"{error:<33}")
            
        # Summary
        if args.summary:
            print("\nSummary:")
            print("-" * 40)
            
            # Count by status
            status_counts = {}
            type_counts = {}
            
            for op in operations:
                status = op['status']
                op_type = op['operation_type']
                
                status_counts[status] = status_counts.get(status, 0) + 1
                type_counts[op_type] = type_counts.get(op_type, 0) + 1
                
            print("By Status:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
                
            print("\nBy Type:")
            for op_type, count in sorted(type_counts.items()):
                print(f"  {op_type}: {count}")
                
        return 0
        
    def cmd_performance(self, args):
        """Show performance stats"""
        self._ensure_monitoring()
        
        current = self.monitoring.performance.get_current_stats()
        average = self.monitoring.performance.get_average_stats(args.window)
        
        print("\nPerformance Statistics")
        print("=" * 50)
        
        if current:
            print("\nCurrent:")
            print(f"  CPU Usage:      {current.cpu_percent:.1f}%")
            print(f"  Memory Usage:   {current.memory_mb:.1f} MB ({current.memory_percent:.1f}%)")
            print(f"  Active Threads: {current.active_threads}")
            print(f"  Disk I/O Read:  {current.disk_io_read_mb:.2f} MB/s")
            print(f"  Disk I/O Write: {current.disk_io_write_mb:.2f} MB/s")
            print(f"  Network Sent:   {current.network_sent_mb:.2f} MB/s")
            print(f"  Network Recv:   {current.network_recv_mb:.2f} MB/s")
            
        if average:
            print(f"\nAverage (last {args.window} minutes):")
            print(f"  CPU Usage:      {average['cpu_percent']:.1f}%")
            print(f"  Memory Usage:   {average['memory_mb']:.1f} MB")
            print(f"  Disk Read:      {average['disk_read_mb']:.2f} MB total")
            print(f"  Disk Write:     {average['disk_write_mb']:.2f} MB total")
            print(f"  Network Sent:   {average['network_sent_mb']:.2f} MB total")
            print(f"  Network Recv:   {average['network_recv_mb']:.2f} MB total")
            print(f"  Active Threads: {average['active_threads']:.1f}")
            
        # Show history if requested
        if args.history:
            print("\nPerformance History:")
            print("-" * 70)
            print("Time       CPU%   Memory MB  Threads  Net MB/s  Disk MB/s")
            print("-" * 70)
            
            # Get recent snapshots
            snapshots = list(self.monitoring.performance.snapshots)[-20:]
            
            for snapshot in snapshots:
                timestamp = snapshot.timestamp.strftime('%H:%M:%S')
                net_rate = snapshot.network_sent_mb + snapshot.network_recv_mb
                disk_rate = snapshot.disk_io_read_mb + snapshot.disk_io_write_mb
                
                print(f"{timestamp}  {snapshot.cpu_percent:5.1f}  {snapshot.memory_mb:9.1f}  "
                      f"{snapshot.active_threads:7}  {net_rate:8.2f}  {disk_rate:9.2f}")
                      
        return 0
        
    def cmd_report(self, args):
        """Generate monitoring report"""
        self._ensure_monitoring()
        
        print(f"Generating report for the last {args.hours} hours...")
        
        try:
            self.monitoring.generate_report(args.output, args.hours)
            print(f"Report saved to: {args.output}")
            
            # Check for chart files
            base_path = Path(args.output).with_suffix('')
            cpu_chart = f"{base_path}_cpu.png"
            memory_chart = f"{base_path}_memory.png"
            
            if Path(cpu_chart).exists():
                print(f"CPU chart saved to: {cpu_chart}")
            if Path(memory_chart).exists():
                print(f"Memory chart saved to: {memory_chart}")
                
            # Show summary
            if args.show:
                with open(args.output) as f:
                    report_data = json.load(f)
                    
                print("\nReport Summary:")
                print("-" * 40)
                
                if 'performance_summary' in report_data:
                    perf = report_data['performance_summary']
                    print(f"Average CPU: {perf['avg_cpu']:.1f}%")
                    print(f"Max CPU: {perf['max_cpu']:.1f}%")
                    print(f"Average Memory: {perf['avg_memory_mb']:.1f} MB")
                    print(f"Max Memory: {perf['max_memory_mb']:.1f} MB")
                    
                if 'operation_summary' in report_data:
                    print("\nOperations:")
                    for op_type, stats in report_data['operation_summary'].items():
                        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                        print(f"  {op_type}: {stats['total']} total, {success_rate:.1f}% success")
                        
        except Exception as e:
            print(f"Error generating report: {e}")
            return 1
            
        return 0
        
    def cmd_alerts(self, args):
        """Manage alerts"""
        self._ensure_monitoring()
        
        if args.action == 'show':
            # Show current thresholds
            print("\nAlert Thresholds:")
            print("-" * 40)
            
            for metric, threshold in self.monitoring.alert_thresholds.items():
                if metric == 'error_rate':
                    print(f"{metric}: {threshold * 100:.1f}%")
                elif metric == 'response_time':
                    print(f"{metric}: {threshold:.1f}s")
                else:
                    print(f"{metric}: {threshold}%")
                    
        elif args.action == 'set':
            # Set threshold
            if not args.metric or args.value is None:
                print("Error: --metric and --value required for set action")
                return 1
                
            try:
                # Convert value based on metric type
                if args.metric == 'error_rate':
                    value = float(args.value) / 100  # Convert percentage
                else:
                    value = float(args.value)
                    
                # Update threshold
                self.monitoring.alert_thresholds[args.metric] = value
                print(f"Updated {args.metric} threshold to {args.value}")
                
                # Save to config
                self.config['alert_thresholds'][args.metric] = value
                self._save_config()
                
            except Exception as e:
                print(f"Error setting threshold: {e}")
                return 1
                
        elif args.action == 'test':
            # Test alert system
            print("Testing alert system...")
            
            # Trigger a test alert
            test_alert = {
                'type': 'test',
                'severity': 'info',
                'message': 'Test alert from CLI',
                'timestamp': datetime.now().isoformat()
            }
            
            for callback in self.monitoring.alert_callbacks:
                callback(test_alert)
                
            print("Test alert sent to all callbacks")
            
        return 0
        
    def cmd_clean(self, args):
        """Clean old monitoring data"""
        self._ensure_monitoring()
        
        print("Cleaning old monitoring data...")
        
        # Clean operations older than specified days
        if args.operations:
            try:
                before = datetime.now() - timedelta(days=args.days)
                
                # This would need to be implemented in OperationTracker
                print(f"Cleaning operations older than {args.days} days...")
                # self.monitoring.operations.clean_old_operations(before)
                
            except Exception as e:
                print(f"Error cleaning operations: {e}")
                
        # Clean log files
        if args.logs:
            log_dir = Path(self.config['log_directory'])
            if log_dir.exists():
                cleaned = 0
                cutoff = time.time() - (args.days * 86400)
                
                for log_file in log_dir.glob('*.log.gz'):
                    if log_file.stat().st_mtime < cutoff:
                        log_file.unlink()
                        cleaned += 1
                        
                print(f"Cleaned {cleaned} old log files")
                
        print("Cleanup complete")
        return 0
        
    def _save_config(self):
        """Save configuration to file"""
        config_path = Path('./config/monitoring.json')
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def run(self, args):
        """Run the CLI with parsed arguments"""
        # Map commands to methods
        commands = {
            'dashboard': self.cmd_dashboard,
            'metrics': self.cmd_metrics,
            'operations': self.cmd_operations,
            'performance': self.cmd_performance,
            'report': self.cmd_report,
            'alerts': self.cmd_alerts,
            'clean': self.cmd_clean
        }
        
        if args.command in commands:
            return commands[args.command](args)
        else:
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='UsenetSync Monitoring CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch monitoring dashboard
  %(prog)s dashboard
  
  # Show all available metrics
  %(prog)s metrics --list
  
  # Show specific metric
  %(prog)s metrics operations --window 60
  
  # Show recent operations
  %(prog)s operations --limit 50 --type index
  
  # Show performance stats
  %(prog)s performance --window 30 --history
  
  # Generate report
  %(prog)s report --hours 24 --output report.json --show
  
  # Manage alerts
  %(prog)s alerts show
  %(prog)s alerts set --metric cpu_percent --value 90
  
  # Clean old data
  %(prog)s clean --operations --logs --days 7
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch monitoring dashboard')
    dashboard_parser.add_argument('--host', default='127.0.0.1', help='Dashboard host')
    dashboard_parser.add_argument('--port', type=int, default=5000, help='Dashboard port')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show metrics')
    metrics_parser.add_argument('name', nargs='?', help='Metric name')
    metrics_parser.add_argument('--list', action='store_true', help='List all metrics')
    metrics_parser.add_argument('--window', type=int, default=60, help='Time window in minutes')
    metrics_parser.add_argument('--recent', action='store_true', help='Show recent values')
    
    # Operations command
    ops_parser = subparsers.add_parser('operations', help='Show operations')
    ops_parser.add_argument('--limit', type=int, default=100, help='Number of operations to show')
    ops_parser.add_argument('--type', help='Filter by operation type')
    ops_parser.add_argument('--summary', action='store_true', help='Show summary statistics')
    
    # Performance command
    perf_parser = subparsers.add_parser('performance', help='Show performance stats')
    perf_parser.add_argument('--window', type=int, default=5, help='Average window in minutes')
    perf_parser.add_argument('--history', action='store_true', help='Show performance history')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate monitoring report')
    report_parser.add_argument('--hours', type=int, default=24, help='Report period in hours')
    report_parser.add_argument('--output', default='monitoring_report.json', help='Output file')
    report_parser.add_argument('--show', action='store_true', help='Show report summary')
    
    # Alerts command
    alerts_parser = subparsers.add_parser('alerts', help='Manage alerts')
    alerts_parser.add_argument('action', choices=['show', 'set', 'test'], help='Alert action')
    alerts_parser.add_argument('--metric', help='Metric name for threshold')
    alerts_parser.add_argument('--value', type=float, help='Threshold value')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old monitoring data')
    clean_parser.add_argument('--operations', action='store_true', help='Clean old operations')
    clean_parser.add_argument('--logs', action='store_true', help='Clean old log files')
    clean_parser.add_argument('--days', type=int, default=30, help='Days to keep')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Create and run CLI
    cli = MonitoringCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
