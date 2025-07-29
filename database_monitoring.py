"""
Database monitoring utilities
"""
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from database_config import get_db

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Database monitoring utilities"""
    
    @staticmethod
    def log_stats(db=None):
        """Log current database statistics"""
        if db is None:
            db = get_db()
            
        stats = db.get_monitoring_stats()
        
        logger.info(
            f"DB Stats - Operations: {stats['total_operations']}, "
            f"Errors: {stats['total_errors']}, "
            f"Lock errors: {stats['lock_errors']}, "
            f"Rate: {stats['operations_per_second']:.1f} ops/sec"
        )
        
        return stats
    
    @staticmethod
    def check_health(db=None) -> Dict:
        """
        Check database health
        
        Returns:
            Dict with health status
        """
        if db is None:
            db = get_db()
            
        stats = db.get_monitoring_stats()
        
        health = {
            'status': 'healthy',
            'issues': [],
            'metrics': {
                'total_operations': stats['total_operations'],
                'error_rate': (stats['total_errors'] / stats['total_operations'] * 100) 
                              if stats['total_operations'] > 0 else 0,
                'lock_error_rate': (stats['lock_errors'] / stats['total_operations'] * 100) 
                                   if stats['total_operations'] > 0 else 0,
                'operations_per_second': stats['operations_per_second']
            }
        }
        
        # Check for issues
        if health['metrics']['error_rate'] > 5:
            health['status'] = 'warning'
            health['issues'].append(f"High error rate: {health['metrics']['error_rate']:.1f}%")
            
        if health['metrics']['lock_error_rate'] > 2:
            health['status'] = 'warning'
            health['issues'].append(f"High lock error rate: {health['metrics']['lock_error_rate']:.1f}%")
            
        if stats['operations_per_second'] < 1 and stats['total_operations'] > 100:
            health['status'] = 'warning'
            health['issues'].append("Low operation rate")
            
        return health
    
    @staticmethod
    def get_performance_report(db=None) -> str:
        """Generate performance report"""
        if db is None:
            db = get_db()
            
        stats = db.get_monitoring_stats()
        
        report = [
            f"Database Performance Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"Uptime: {stats['uptime_seconds']:.1f} seconds",
            f"Total Operations: {stats['total_operations']:,}",
            f"Total Errors: {stats['total_errors']:,}",
            f"Lock Errors: {stats['lock_errors']:,}",
            f"Operations/sec: {stats['operations_per_second']:.2f}",
            "",
            "Operation Breakdown:",
            "-" * 40
        ]
        
        for op_name, op_stats in sorted(stats['operations'].items()):
            report.append(
                f"{op_name:<25} {op_stats['count']:>8} calls, "
                f"{op_stats['avg_time_ms']:>6.1f}ms avg, "
                f"{op_stats['error_rate']*100:>5.1f}% errors"
            )
        
        return "\n".join(report)
    
    @staticmethod
    def save_stats_to_file(filepath: str = "logs/db_stats.json", db=None):
        """Save statistics to JSON file"""
        if db is None:
            db = get_db()
            
        stats = db.get_monitoring_stats()
        stats['timestamp'] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Saved database statistics to {filepath}")
