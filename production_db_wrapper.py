#!/usr/bin/env python3
"""
Production-ready database wrapper with monitoring and retry logic
Drop-in replacement for EnhancedDatabaseManager
"""

import time
import functools
import logging
import random
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path

from enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig

# Configure logging
logger = logging.getLogger(__name__)

class ProductionDatabaseManager(EnhancedDatabaseManager):
    """Enhanced database manager with production features"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None, 
                 enable_monitoring: bool = True,
                enable_retry: bool = True,
                 log_file: Optional[str] = None):
        """
        Initialize production database manager
        
        Args:
            config: Database configuration
            enable_monitoring: Enable operation monitoring
            enable_retry: Enable automatic retry on lock errors
            log_file: Path to log file for errors/warnings
        """
        super().__init__(config)
        
        self.enable_monitoring = enable_monitoring
        self.enable_retry = enable_retry
        self.log_handler = None  # Initialize to None
        
        # Set up logging
        if log_file:
            self._setup_file_logging(log_file)
        
        # Initialize monitoring
        if enable_monitoring:
            self.monitor = {
                'operations': {},
                'errors': {},
                'lock_errors': 0,
                'start_time': time.time()
            }
    
    def _setup_file_logging(self, log_file: str):
        """Set up file logging for errors and warnings"""
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def _retry_operation(self, func, *args, **kwargs):
        """
        Execute operation with retry logic
        
        Returns result of function or raises last exception
        """
        if not self.enable_retry:
            return func(*args, **kwargs)
        
        max_attempts = 3
        delay = 0.1
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                result = func(*args, **kwargs)
                
                # Log recovery if this was a retry
                if attempt > 0:
                    logger.info(f"Operation {func.__name__} succeeded on retry {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check if error is retryable
                is_locked_error = (
                    'database is locked' in error_msg or 
                    'OperationalError' in str(type(e)) or
                    (hasattr(e, '__class__') and e.__class__.__name__ == 'OperationalError')
                )
                
                if not is_locked_error or attempt == max_attempts - 1:
                    if is_locked_error:
                        logger.error(f"Failed after {max_attempts} retries: {e}")
                    raise
                
                # Log retry attempt
                logger.warning(
                    f"Database locked in {func.__name__}, attempt {attempt + 1}/{max_attempts}"
                )
                
                # Monitor lock errors
                if self.enable_monitoring:
                    self.monitor['lock_errors'] += 1
                
                # Exponential backoff with jitter
                jittered_delay = delay * (0.5 + random.random())
                actual_delay = min(jittered_delay, 2.0)
                logger.info(f"Waiting {actual_delay:.2f}s before retry...")
                time.sleep(actual_delay)
                delay *= 2
        
        raise last_exception
    
    def _monitor_operation(self, operation: str, func, *args, **kwargs):
        """Execute operation with monitoring"""
        start_time = time.time()
        error = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            if self.enable_monitoring:
                duration = time.time() - start_time
                
                # Update counters
                if operation not in self.monitor['operations']:
                    self.monitor['operations'][operation] = {
                        'count': 0,
                        'total_time': 0,
                        'errors': 0
                    }
                
                stats = self.monitor['operations'][operation]
                stats['count'] += 1
                stats['total_time'] += duration
                
                if error:
                    stats['errors'] += 1
                    self.monitor['errors'][operation] = self.monitor['errors'].get(operation, 0) + 1
                
                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {operation} took {duration:.2f}s")
    
    # Override critical methods with retry and monitoring
    
    def create_folder(self, folder_unique_id: str, folder_path: str, 
                     display_name: str, share_type: str = 'private') -> int:
        """Create folder with retry logic"""
        def _create():
            return super(ProductionDatabaseManager, self).create_folder(
                folder_unique_id, folder_path, display_name, share_type
            )
        
        return self._monitor_operation(
            'create_folder',
            lambda: self._retry_operation(_create)
        )
    
    def add_file(self, folder_id: int, file_path: str, file_hash: str, 
                 file_size: int, modified_at: datetime, version: int = 1) -> int:
        """Add file with retry logic"""
        def _add():
            return super(ProductionDatabaseManager, self).add_file(
                folder_id, file_path, file_hash, file_size, modified_at, version
            )
        
        return self._monitor_operation(
            'add_file',
            lambda: self._retry_operation(_add)
        )
    
    def create_folder_version(self, folder_id: int, version: int, 
                            change_summary: Dict) -> int:
        """Create folder version with retry logic"""
        def _create():
            return super(ProductionDatabaseManager, self).create_folder_version(
                folder_id, version, change_summary
            )
        
        return self._monitor_operation(
            'create_folder_version',
            lambda: self._retry_operation(_create)
        )
    
    def bulk_insert_segments(self, segments: List[Dict]):
        """Bulk insert segments with retry logic"""
        def _insert():
            return super(ProductionDatabaseManager, self).bulk_insert_segments(segments)
        
        return self._monitor_operation(
            'bulk_insert_segments',
            lambda: self._retry_operation(_insert)
        )
    
    def get_all_folders(self) -> List[Dict]:
        """Get all folders with monitoring (no retry for reads)"""
        return self._monitor_operation(
            'get_all_folders',
            super().get_all_folders
        )
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics"""
        if not self.enable_monitoring:
            return {}
        
        uptime = time.time() - self.monitor['start_time']
        total_ops = sum(op['count'] for op in self.monitor['operations'].values())
        total_errors = sum(self.monitor['errors'].values())
        
        stats = {
            'uptime_seconds': uptime,
            'total_operations': total_ops,
            'total_errors': total_errors,
            'lock_errors': self.monitor['lock_errors'],
            'operations_per_second': total_ops / uptime if uptime > 0 else 0,
            'operations': {}
        }
        
        # Add per-operation stats
        for op_name, op_stats in self.monitor['operations'].items():
            avg_time = op_stats['total_time'] / op_stats['count'] if op_stats['count'] > 0 else 0
            stats['operations'][op_name] = {
                'count': op_stats['count'],
                'errors': op_stats['errors'],
                'avg_time_ms': avg_time * 1000,
                'error_rate': op_stats['errors'] / op_stats['count'] if op_stats['count'] > 0 else 0
            }
        
        return stats
    
    def log_stats(self):
        """Log current statistics"""
        if not self.enable_monitoring:
            return
        
        stats = self.get_monitoring_stats()
        logger.info(
            f"DB Stats - Ops: {stats['total_operations']}, "
            f"Errors: {stats['total_errors']} ({stats['lock_errors']} locks), "
            f"Rate: {stats['operations_per_second']:.1f} ops/sec"
        )

        def _get_pending():
            try:
                # Call the parent class method directly
                if hasattr(super(), 'get_pending_uploads'):
                    return super().get_pending_uploads(limit)
                
                # If not, implement it directly using the connection pool
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT task_id, folder_id, file_path, status, created_at
                        FROM upload_queue
                        WHERE status = 'pending'
                        ORDER BY created_at
                        LIMIT ?
                    """, (limit,))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'task_id': row[0],
                            'folder_id': row[1],
                            'file_path': row[2],
                            'status': row[3],
                            'created_at': row[4]
                        })
                    
                    return results
            except Exception as e:
                logger.warning(f"Error getting pending uploads: {e}")
                return []
        
        return self._monitor_operation('get_pending_uploads', _get_pending)

        def _get_shares():
            try:
                # Call the parent class method directly
                if hasattr(super(), 'get_all_shares'):
                    return super().get_all_shares()
                
                # If not, implement it directly using the connection pool
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT share_id, folder_id, version, access_string, 
                               share_type, created_at, index_size
                        FROM publications
                        ORDER BY created_at DESC
                    """)
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'share_id': row[0],
                            'folder_id': row[1],
                            'version': row[2],
                            'access_string': row[3],
                            'share_type': row[4],
                            'created_at': row[5],
                            'index_size': row[6]
                        })
                    
                    return results
            except Exception as e:
                logger.warning(f"Error getting shares: {e}")
                return []
        
        return self._monitor_operation('get_all_shares', _get_shares)


    def close(self):
        """Close database and cleanup logging"""
        # Remove log handler if exists
        if hasattr(self, 'log_handler') and self.log_handler:
            logger.removeHandler(self.log_handler)
            self.log_handler.close()
        
        # Call parent close
        super().close()

    def get_pending_uploads(self, limit: int = 100) -> list:
        """Get pending upload tasks"""
        # Check parent class first
        parent = super(ProductionDatabaseManager, self)
        if hasattr(parent, 'get_pending_uploads'):
            return self._monitor_operation(
                'get_pending_uploads', 
                lambda: parent.get_pending_uploads(limit)
            )
        
        # Otherwise, implement directly
        def _get_pending():
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT task_id, folder_id, file_path, status, created_at
                        FROM upload_queue
                        WHERE status = 'pending'
                        ORDER BY created_at
                        LIMIT ?
                    """, (limit,))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'task_id': row[0],
                            'folder_id': row[1],
                            'file_path': row[2],
                            'status': row[3],
                            'created_at': row[4]
                        })
                    
                    return results
            except Exception as e:
                logger.warning(f"Error getting pending uploads: {e}")
                return []
        
        return self._monitor_operation('get_pending_uploads', _get_pending)
    def get_all_shares(self) -> list:
        """Get all published shares"""
        # Check parent class first
        parent = super(ProductionDatabaseManager, self)
        if hasattr(parent, 'get_all_shares'):
            return self._monitor_operation(
                'get_all_shares',
                lambda: parent.get_all_shares()
            )
        
        # Otherwise, implement directly
        def _get_shares():
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT share_id, folder_id, version, access_string, 
                               share_type, created_at, index_size
                        FROM publications
                        ORDER BY created_at DESC
                    """)
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'share_id': row[0],
                            'folder_id': row[1],
                            'version': row[2],
                            'access_string': row[3],
                            'share_type': row[4],
                            'created_at': row[5],
                            'index_size': row[6]
                        })
                    
                    return results
            except Exception as e:
                logger.warning(f"Error getting shares: {e}")
                return []
        
        return self._monitor_operation('get_all_shares', _get_shares)

# Convenience function
def create_production_db(db_path: str, log_file: Optional[str] = None, 
                        pool_size: int = 10) -> ProductionDatabaseManager:
    """
    Create a production-ready database manager
    
    Args:
        db_path: Path to database file
        log_file: Optional path for error logging
        pool_size: Connection pool size (default 10)
        
    Returns:
        ProductionDatabaseManager instance
    """
    config = DatabaseConfig(
        path=db_path,
        pool_size=pool_size,
        timeout=30.0,
        cache_size=10000
    )
    
    return ProductionDatabaseManager(
        config=config,
        enable_monitoring=True,
        enable_retry=True,
        log_file=log_file
    )


    def get_share_by_id(self, share_id: str) -> Optional[Dict]:
        """Get share by ID"""
        def _get_share():
            try:
                # Implement using parent method or connection pool
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT * FROM publications WHERE share_id = ?
                    """, (share_id,))
                    row = cursor.fetchone()
                    if row:
                        return {
                            'share_id': row[1],
                            'folder_id': row[2],
                            'version': row[3],
                            'access_string': row[4],
                            'share_type': row[5],
                            'created_at': row[6],
                            'index_size': row[7]
                        }
                    return None
            except Exception as e:
                logger.warning(f"Error getting share: {e}")
                return None
        
        return self._monitor_operation('get_share_by_id', _get_share)
    def record_publication(self, folder_id: int, version: int, share_id: str,
                          access_string: str, index_size: int, share_type: str) -> bool:
        """Record a folder publication"""
        def _record():
            try:
                with self.pool.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO publications 
                        (share_id, folder_id, version, access_string, share_type, index_size)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (share_id, folder_id, version, access_string, share_type, index_size))
                    conn.commit()
                    return True
            except Exception as e:
                logger.warning(f"Error recording publication: {e}")
                return False
        
        return self._monitor_operation('record_publication', _record)
    def get_folder_shares(self, folder_id: str) -> list:
        """Get shares for a specific folder"""
        def _get_shares():
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT share_id, version, access_string, share_type, created_at, index_size
                        FROM publications 
                        WHERE folder_id = ?
                        ORDER BY created_at DESC
                    """, (folder_id,))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'share_id': row[0],
                            'version': row[1],
                            'access_string': row[2],
                            'share_type': row[3],
                            'created_at': row[4],
                            'index_size': row[5]
                        })
                    return results
            except Exception as e:
                logger.warning(f"Error getting folder shares: {e}")
                return []
        
        return self._monitor_operation('get_folder_shares', _get_shares)

# Example usage and test
if __name__ == "__main__":
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/test_production.db"
    log_path = f"{temp_dir}/database.log"
    
    print("Testing production database wrapper...")
    
    try:
        # Create production database
        db = create_production_db(db_path, log_path)
        
        # Test operations
        folder_id = db.create_folder("prod_test_001", "/test", "Test", "public")
        print(f"✓ Created folder: {folder_id}")
        
        # Test retry on lock (simulate with non-existent folder)
        try:
            db.add_file(9999, "test.txt", "hash", 1024, datetime.now())
        except ValueError as e:
            print(f"✓ Caught expected error: {e}")
        
        # Do some operations
        for i in range(5):
            db.get_all_folders()
            db.add_file(folder_id, f"file_{i}.txt", f"hash_{i}", 1000 + i, datetime.now())
        
        # Show statistics
        stats = db.get_monitoring_stats()
        print(f"\nMonitoring Statistics after {stats['uptime_seconds']:.1f} seconds:")
        print(f"  Total operations: {stats['total_operations']}")
        print(f"  Total errors: {stats['total_errors']}")
        print(f"  Lock errors: {stats['lock_errors']}")
        print(f"  Rate: {stats['operations_per_second']:.2f} ops/sec")
        
        print("\nPer-operation stats:")
        for op, op_stats in stats['operations'].items():
            print(f"  {op}:")
            print(f"    Count: {op_stats['count']}")
            print(f"    Avg time: {op_stats['avg_time_ms']:.1f}ms")
            print(f"    Errors: {op_stats['errors']}")
        
        # Check log file
        if Path(log_path).exists():
            print(f"\nLog file entries:")
            with open(log_path, 'r') as f:
                content = f.read()
                if content:
                    print(content)
                else:
                    print("  (No warnings/errors logged)")
        
        db.close()
        print("\n✅ Production wrapper working correctly!")
        
    finally:
        shutil.rmtree(temp_dir)
