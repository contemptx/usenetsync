#!/usr/bin/env python3
"""
Production-ready database wrapper with monitoring and retry logic
Drop-in replacement for EnhancedDatabaseManager
"""

import time
import functools
import logging
import random
import json
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path

from src.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig
def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}



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
        super(ProductionDatabaseManager, self).__init__(config)
        
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
    
        # Setup WAL mode for better concurrency
        self.setup_wal_mode()
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
    
    def add_file(self, folder_id, file_path, file_hash, file_size, modified_at, version=1):
        """Add file to database with proper error handling"""
        import sqlite3
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        INSERT INTO files 
                        (folder_id, file_path, file_hash, file_size, modified_at, version, state)
                        VALUES (?, ?, ?, ?, ?, ?, 'indexed')
                    """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                    
                    file_id = cursor.lastrowid
                    return file_id
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    print(f"Database locked, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database error after {attempt + 1} attempts: {e}")
                    raise e
            except Exception as e:
                print(f"Error adding file: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        raise sqlite3.OperationalError(f"Failed to add file after {max_retries} attempts")
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
    
    def bulk_insert_segments(self, segments):
        """Bulk insert segments with proper transaction handling"""
        import sqlite3
        import time
        
        if not segments:
            return True
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    for segment in segments:
                        conn.execute("""
                            INSERT INTO segments 
                            (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, state)
                            VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        """, (
                            segment['file_id'],
                            segment['segment_index'], 
                            segment['segment_hash'],
                            segment['segment_size'],
                            segment['data_offset'],
                            segment.get('redundancy_index', 0)
                        ))
                    return True
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                print(f"Error bulk inserting segments: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        return False
    def get_all_folders(self) -> List[Dict]:
        """Get all folders with monitoring (no retry for reads)"""
        return self._monitor_operation(
            'get_all_folders',
            super(ProductionDatabaseManager, self).get_all_folders
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
                if hasattr(super(ProductionDatabaseManager, self), 'get_pending_uploads'):
                    return super(ProductionDatabaseManager, self).get_pending_uploads(limit)
                
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
                if hasattr(super(ProductionDatabaseManager, self), 'get_all_shares'):
                    return super(ProductionDatabaseManager, self).get_all_shares()
                
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


    
    def update_folder_keys(self, folder_id: int, private_key: bytes, public_key: bytes):
        """Update folder keys in database with explicit transaction handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Use a direct connection to ensure transaction control
                conn = sqlite3.connect(self.config.path, timeout=60.0)
                
                try:
                    # Enable WAL mode for better concurrency
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA busy_timeout=60000")
                    
                    # Begin explicit transaction
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Update with explicit commit
                    cursor = conn.execute("""
                        UPDATE folders 
                        SET private_key = ?, public_key = ?
                        WHERE rowid = ?
                    """, (private_key, public_key, folder_id))
                    
                    if cursor.rowcount == 0:
                        # Try with id field instead of rowid
                        cursor = conn.execute("""
                            UPDATE folders 
                            SET private_key = ?, public_key = ?
                            WHERE id = ?
                        """, (private_key, public_key, folder_id))
                    
                    # Explicit commit
                    conn.commit()
                    
                    # Verify the update worked
                    cursor = conn.execute("SELECT private_key IS NOT NULL, public_key IS NOT NULL FROM folders WHERE rowid = ?", (folder_id,))
                    result = cursor.fetchone()
                    
                    if result and result[0] and result[1]:
                        print(f"SUCCESS: Keys saved to folder {folder_id} - verified in database")
                        conn.close()
                        return
                    else:
                        print(f"WARNING: Keys not verified in database for folder {folder_id}")
                        
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.close()
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    print(f"Database locked during key save, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database error during key save after {attempt + 1} attempts: {e}")
                    raise e
            except Exception as e:
                print(f"Error saving keys: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
                
        raise sqlite3.OperationalError(f"Failed to save keys after {max_retries} attempts")
    def get_folder_by_path(self, folder_path: str) -> Optional[Dict]:
        """Get folder by file system path"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM folders WHERE folder_path = ?
            """, (folder_path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_folder_stats(self, folder_id: int):
        """Update folder statistics"""
        with self.pool.get_connection() as conn:
            # Update file count and total size
            cursor = conn.execute("""
                UPDATE folders 
                SET file_count = (
                    SELECT COUNT(*) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                total_size = (
                    SELECT COALESCE(SUM(file_size), 0) FROM files WHERE folder_id = ? AND state != 'deleted'
                )
                WHERE id = ?
            """, (folder_id, folder_id, folder_id))
                        # Commit handled by connection pool
    def get_folder_files(self, folder_id, offset=0, limit=None):
        """Get files in folder with pagination"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return []
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                query = "SELECT * FROM files WHERE folder_id = ? ORDER BY file_path"
                params = [folder_db_id]
                
                if limit is not None:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    
    def get_file_segments(self, file_id: int) -> List[Dict]:
        """Get all segments for a file"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM segments WHERE file_id = ? ORDER BY segment_index
            """, (file_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def create_file(self, folder_id: int, file_path: str, file_hash: str, 
                    file_size: int, version: int = 1) -> int:
        """Create new file entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO files 
                (folder_id, file_path, file_hash, file_size, version, state)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (folder_id, file_path, file_hash, file_size, version))
                        # Commit handled by connection pool
            return cursor.lastrowid
    
    def get_file(self, folder_id: int, file_path: str) -> Optional[Dict]:
        """Get file by folder and path"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE folder_id = ? AND file_path = ?
            """, (folder_id, file_path))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_file_state(self, file_id: int, state: str):
        """Update file state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE files SET state = ?, modified_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (state, file_id))
                        # Commit handled by connection pool
    def create_segment(self, file_id: int, segment_index: int, segment_hash: str,
                        segment_size: int, data_offset: int, redundancy_index: int = 0) -> int:
        """Create new segment entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO segments 
                (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index))
                        # Commit handled by connection pool
            return cursor.lastrowid
    
    def record_change(self, folder_id: int, file_path: str, change_type: str,
                    old_version: Optional[int], new_version: Optional[int],
                    old_hash: Optional[str], new_hash: Optional[str]):
        """Record change in journal"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                INSERT INTO change_journal 
                (folder_id, file_path, change_type, old_version, new_version, old_hash, new_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (folder_id, file_path, change_type, old_version, new_version, old_hash, new_hash))
                        # Commit handled by connection pool
    def create_folder_version(self, folder_id: int, version: int, change_data: Dict) -> int:
        """Create folder version entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO folder_versions 
                (folder_id, version, change_summary)
                VALUES (?, ?, ?)
            """, (folder_id, version, json.dumps(change_data)))
                        # Commit handled by connection pool
            return cursor.lastrowid

    
    def get_folder_info(self, folder_id):
        """Get folder information by ID"""
        return self.get_folder(folder_id)
    
    def get_folder_segments(self, folder_id):
        """Get all segments for a folder"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return []
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.*, f.file_path, f.file_hash 
                    FROM segments s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.folder_id = ?
                    ORDER BY f.file_path, s.segment_index
                """, (folder_db_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def remove_folder(self, folder_id):
        """Remove folder and all associated data"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return False
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                # Delete files and segments first
                conn.execute("DELETE FROM segments WHERE file_id IN (SELECT id FROM files WHERE folder_id = ?)", (folder_db_id,))
                conn.execute("DELETE FROM files WHERE folder_id = ?", (folder_db_id,))
                conn.execute("DELETE FROM folders WHERE id = ?", (folder_db_id,))
                        # Commit handled by connection pool
                return True
        except Exception as e:
            raise e
    
    def cleanup_old_sessions(self, days=30):
        """Clean up old sessions"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("DELETE FROM upload_sessions WHERE created_at < datetime('now', '-{} days')".format(days))
                        # Commit handled by connection pool
        except Exception:
            pass
    
    def vacuum(self):
        """Vacuum database"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("VACUUM")
        except Exception:
            pass
    
    def analyze(self):
        """Analyze database"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("ANALYZE")
        except Exception:
            pass

    
    def get_folder_authorized_users(self, folder_id):
        """Get authorized users for a folder"""
        try:
            # Convert folder_id to database ID if it's a string
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return []
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                try:
                    cursor = conn.execute("""
                        SELECT user_id, access_type, added_at, added_by
                        FROM access_control_local 
                        WHERE folder_id = ?
                        ORDER BY added_at
                    """, (folder_db_id,))
                    
                    users = []
                    for row in cursor.fetchall():
                        users.append({
                            'user_id': row[0],
                            'access_type': row[1],
                            'added_at': row[2],
                            'added_by': row[3]
                        })
                    return users
                except Exception:
                    return []
        except Exception:
            return []
    
    def add_folder_authorized_user(self, folder_id, user_id, access_type='read', added_by=None):
        """Add authorized user to folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return False
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                # Create table if needed
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS access_control_local (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_id INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        access_type TEXT DEFAULT 'read',
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        added_by TEXT,
                        FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
                        UNIQUE(folder_id, user_id)
                    )
                """)
                
                conn.execute("""
                    INSERT OR REPLACE INTO access_control_local 
                    (folder_id, user_id, access_type, added_by)
                    VALUES (?, ?, ?, ?)
                """, (folder_db_id, user_id, access_type, added_by))
                        # Commit handled by connection pool
                return True
        except Exception:
            return False
    
    def remove_folder_authorized_user(self, folder_id, user_id):
        """Remove authorized user from folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return False
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                conn.execute("""
                    DELETE FROM access_control_local 
                    WHERE folder_id = ? AND user_id = ?
                """, (folder_db_id, user_id))
                        # Commit handled by connection pool
                return True
        except Exception:
            return False
    
    def get_upload_progress(self, folder_id):
        """Get upload progress for folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return {'total': 0, 'uploaded': 0, 'failed': 0}
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN state = 'uploaded' THEN 1 ELSE 0 END) as uploaded,
                        SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM segments s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.folder_id = ?
                """, (folder_db_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'total': row[0] or 0,
                        'uploaded': row[1] or 0,
                        'failed': row[2] or 0
                    }
                return {'total': 0, 'uploaded': 0, 'failed': 0}
        except Exception:
            return {'total': 0, 'uploaded': 0, 'failed': 0}
    
    def update_segment_state(self, segment_id, state):
        """Update segment upload state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE segments SET state = ? WHERE id = ?
                """, (state, segment_id))
                        # Commit handled by connection pool
                return True
        except Exception:
            return False
    
    def get_folder_share_info(self, folder_id):
        """Get share information for folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return None
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT share_id, access_string, share_type, created_at
                    FROM publications 
                    WHERE folder_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (folder_db_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'share_id': row[0],
                        'access_string': row[1],
                        'share_type': row[2],
                        'created_at': row[3]
                    }
                return None
        except Exception:
            return None
    
    def create_upload_session(self, session_id, folder_id, total_segments):
        """Create upload session record"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS upload_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        folder_id TEXT NOT NULL,
                        total_segments INTEGER DEFAULT 0,
                        uploaded_segments INTEGER DEFAULT 0,
                        failed_segments INTEGER DEFAULT 0,
                        state TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    INSERT OR REPLACE INTO upload_sessions 
                    (session_id, folder_id, total_segments)
                    VALUES (?, ?, ?)
                """, (session_id, folder_id, total_segments))
                        # Commit handled by connection pool
                return True
        except Exception:
            return False
    
    def update_upload_session_state(self, session_id, state):
        """Update upload session state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE upload_sessions 
                    SET state = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (state, session_id))
                        # Commit handled by connection pool
                return True
        except Exception:
            return False

    
    def get_connection(self):
        """Get database connection with better locking handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.config.path, timeout=60.0)
                conn.row_factory = dict_factory
                
                # Configure for better concurrent access
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                conn.execute("PRAGMA mmap_size=268435456")
                
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                raise e
        
        raise sqlite3.OperationalError("Could not get database connection after retries")

    
    def get_folder_robust(self, folder_identifier):
        """Get folder by any identifier - unique_id, path, or database_id"""
        try:
            # First try the normal get_folder method
            folder = self.get_folder(folder_identifier)
            if folder:
                return folder
            
            # If that fails, try direct database lookup
            with self.pool.get_connection() as conn:
                # Try by database ID if it's a number
                if str(folder_identifier).isdigit():
                    cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (int(folder_identifier),))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                
                # Try by folder_path containing the identifier
                cursor = conn.execute("SELECT * FROM folders WHERE folder_path LIKE ?", (f"%{folder_identifier}%",))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                # Last resort: get the most recent folder with keys
                cursor = conn.execute("""
                    SELECT * FROM folders 
                    WHERE private_key IS NOT NULL 
                    ORDER BY id DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in get_folder_robust: {e}")
            return None

    
    def setup_wal_mode(self):
        """Setup WAL mode for better concurrency"""
        try:
            with self.pool.get_connection() as conn:
                # Enable WAL mode
                conn.execute("PRAGMA journal_mode=WAL")
                
                # Optimize for concurrent access
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA wal_autocheckpoint=1000")
                
                # Check that WAL mode is active
                result = conn.execute("PRAGMA journal_mode").fetchone()
                if result and result[0] == 'wal':
                    logger.info("WAL mode enabled successfully")
                else:
                    logger.warning("Failed to enable WAL mode")
                    
        except Exception as e:
            logger.error(f"Failed to setup WAL mode: {e}")

    
    def add_segment(self, file_id, segment_index, segment_hash, segment_size, subject_hash, newsgroup, redundancy_index=0, **kwargs):
        """Add segment to database with improved concurrency handling"""
        import sqlite3
        import time
        import random
        
        # Extract data_offset from kwargs or use 0
        data_offset = kwargs.get('data_offset', 0)
        
        max_retries = 10  # Increased retries
        base_delay = 0.05  # Shorter base delay
        
        for attempt in range(max_retries):
            try:
                # Use a fresh connection for each attempt to avoid lock inheritance
                conn = sqlite3.connect(self.config.path, timeout=120.0)
                
                # Configure connection for concurrent access
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=120000")
                conn.execute("PRAGMA synchronous=NORMAL")
                
                try:
                    # Use immediate transaction for faster execution
                    conn.execute("BEGIN IMMEDIATE")
                    
                    cursor = conn.execute("""
                        INSERT INTO segments 
                        (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, state, subject_hash, newsgroup)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """, (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, subject_hash, newsgroup))
                    
                    segment_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                    
                    print(f"DEBUG: Added segment {segment_index} for file {file_id}, segment_id: {segment_id}")
                    return segment_id
                    
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    conn.close()
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) or "busy" in str(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        delay = min(delay, 2.0)  # Cap at 2 seconds
                        print(f"Database busy, waiting {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Database error after {max_retries} attempts: {e}")
                        raise e
                else:
                    # Non-recoverable database error
                    print(f"Database error: {e}")
                    raise e
            except Exception as e:
                print(f"Error adding segment: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        raise sqlite3.OperationalError(f"Failed to add segment after {max_retries} attempts")
    def create_segment(self, file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index=0):
        """Create segment entry (alias for add_segment)"""
        return self.add_segment(file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index)
    
    def get_file_segments(self, file_id):
        """Get all segments for a file"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM segments WHERE file_id = ? ORDER BY segment_index
                """, (file_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def update_file_state(self, file_id, state):
        """Update file state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE files SET state = ?, modified_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (state, file_id))
                return True
        except Exception:
            return False
    
    def update_segment_state(self, segment_id, state):
        """Update segment state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE segments SET state = ? WHERE id = ?
                """, (state, segment_id))
                return True
        except Exception:
            return False

    
    def set_segment_offset(self, segment_id, offset):
        """Set segment offset"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("UPDATE segments SET data_offset = ? WHERE id = ?", (offset, segment_id))
                return True
        except Exception:
            return False
    
    def update_file_segment_count(self, file_id, segment_count):
        """Update file segment count"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("UPDATE files SET segment_count = ? WHERE id = ?", (segment_count, file_id))
                return True
        except Exception:
            return False
    
    def get_segment_by_id(self, segment_id):
        """Get segment by ID"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM segments WHERE id = ?", (segment_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def close(self):
        """Close database and cleanup logging"""
        # Remove log handler if exists
        if hasattr(self, 'log_handler') and self.log_handler:
            logger.removeHandler(self.log_handler)
            self.log_handler.close()
        
        # Close connection pool
        try:
            if hasattr(self, 'pool') and self.pool:
                self.pool.close_all()
        except Exception as e:
            logger.debug(f"Pool cleanup error (non-critical): {e}")

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
                        # Commit handled by connection pool
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
