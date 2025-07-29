#!/usr/bin/env python3
"""
Enhanced Database Manager for UsenetSync
Handles all database operations with connection pooling and optimization
"""

import os
import sqlite3
import json
import threading
import queue
import time
import logging
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import hashlib


# Fix for SQLite datetime deprecation warning (Python 3.12+)
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("timestamp", lambda b: datetime.fromisoformat(b.decode()))

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "data/usenetsync.db"
    pool_size: int = 10
    timeout: float = 30.0
    check_same_thread: bool = False
    enable_wal: bool = True
    cache_size: int = 10000
    
class ConnectionPool:
    """Thread-safe connection pool for SQLite"""
    
    def __init__(self, database_path: str, pool_size: int = 10):
        self.database_path = database_path
        self.pool_size = pool_size
        self._connections = queue.Queue(maxsize=pool_size)
        self._all_connections = []
        self._lock = threading.Lock()
        self._closed = False
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize connection pool"""
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._connections.put(conn)
            self._all_connections.append(conn)
            
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(
            self.database_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
        
        # Enable optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")
        
        return conn
        
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
            
        conn = None
        try:
            conn = self._connections.get(timeout=30)
            yield conn
        finally:
            if conn and not self._closed:
                self._connections.put(conn)
                
    def close_all(self):
        """Close all connections"""
        with self._lock:
            self._closed = True
            
            # Close all connections
            for conn in self._all_connections:
                try:
                    conn.close()
                except:
                    pass
                    
    def execute_script(self, script: str):
        """Execute SQL script"""
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()

def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


class EnhancedDatabaseManager:
    """Enhanced database manager with all operations"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool = ConnectionPool(self.config.path, self.config.pool_size)
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database with schema"""
        # Check if database is already initialized
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
                if cursor.fetchone():
                    # Database already initialized, update schema if needed
                    logging.info("Database already initialized, checking for schema updates")
                    self._update_schema()
                    self._create_views()
                    return
        except:
            pass  # Continue with initialization if check fails
        
        schema_path = Path(__file__).parent / "database_schema.sql"
        
        # If schema file exists, use it
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = f.read()
        else:
            # Use embedded schema
            schema = self._get_embedded_schema()
            
        # Remove CREATE VIEW statements from schema to handle them separately
        schema_without_views = self._remove_view_definitions(schema)
        
        try:
            self.pool.execute_script(schema_without_views)
        except Exception as e:
            logging.warning(f"Schema initialization warning: {e}")
            # Don't fail if schema already exists
            
        # Update schema for missing columns/tables
        self._update_schema()
            
        # Create views
        self._create_views()
        
    def _update_schema(self):
        """Update schema with missing columns/tables"""
        with self.pool.get_connection() as conn:
            # Check for missing columns in segments table
            cursor = conn.execute("PRAGMA table_info(segments)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add internal_subject column if missing
            if 'internal_subject' not in columns:
                logging.info("Adding internal_subject column to segments table")
                try:
                    conn.execute("ALTER TABLE segments ADD COLUMN internal_subject TEXT")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    logging.warning(f"Could not add internal_subject column: {e}")
            
            
            # Add offset column if missing
            if 'offset' not in columns:
                logging.info("Adding offset column to segments table")
                try:
                    conn.execute("ALTER TABLE segments ADD COLUMN offset INTEGER DEFAULT 0")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    logging.warning(f"Could not add offset column: {e}")
            
            # Check for upload_sessions table
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_sessions'")
            if not cursor.fetchone():
                logging.info("Creating upload_sessions table")
                conn.execute("""
                    CREATE TABLE upload_sessions (
                        session_id TEXT PRIMARY KEY,
                        folder_id INTEGER NOT NULL,
                        total_segments INTEGER NOT NULL,
                        uploaded_segments INTEGER DEFAULT 0,
                        state TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
                
            # Check for publications table (for backward compatibility)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publications'")
            if not cursor.fetchone():
                logging.info("Creating publications table for backward compatibility")
                conn.execute("""
                    CREATE TABLE publications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        share_id TEXT NOT NULL UNIQUE,
                        folder_id INTEGER NOT NULL,
                        version INTEGER NOT NULL,
                        access_string TEXT NOT NULL,
                        share_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        index_size INTEGER,
                        is_active BOOLEAN DEFAULT 1,
                        revoked_at TIMESTAMP,
                        revocation_note TEXT,
                        FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
            else:
                # Check if is_active column exists in publications table
                cursor = conn.execute("PRAGMA table_info(publications)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'is_active' not in columns:
                    logging.info("Adding is_active column to publications table")
                    try:
                        conn.execute("ALTER TABLE publications ADD COLUMN is_active BOOLEAN DEFAULT 1")
                        conn.commit()
                    except sqlite3.OperationalError as e:
                        logging.warning(f"Could not add is_active column: {e}")

    def _remove_view_definitions(self, schema: str) -> str:
        """Remove CREATE VIEW statements from schema"""
        lines = schema.split('\n')
        filtered_lines = []
        skip_view = False
        
        for line in lines:
            if 'CREATE VIEW' in line:
                skip_view = True
            elif skip_view and line.strip().endswith(';'):
                skip_view = False
                continue
            
            if not skip_view:
                filtered_lines.append(line)
                
        return '\n'.join(filtered_lines)
    
    def _create_views(self):
        """Create database views with the latest schema"""
        with self.pool.get_connection() as conn:
            # Drop existing views
            conn.execute("DROP VIEW IF EXISTS folder_statistics")
            conn.execute("DROP VIEW IF EXISTS upload_statistics")
            
            # Create views with updated schema
            conn.execute("""
                CREATE VIEW folder_statistics AS
                SELECT 
                    f.id,
                    f.folder_unique_id,
                    f.display_name,
                    f.share_type,
                    f.current_version,
                    f.state,
                    COUNT(DISTINCT fi.id) as file_count,
                    COALESCE(SUM(fi.file_size), 0) as total_size,
                    COUNT(DISTINCT s.id) as segment_count,
                    MAX(fi.modified_at) as last_modified
                FROM folders f
                LEFT JOIN files fi ON f.id = fi.folder_id AND fi.state != 'deleted'
                LEFT JOIN segments s ON fi.id = s.file_id
                GROUP BY f.id
            """)
            
            conn.execute("""
                CREATE VIEW upload_statistics AS
                SELECT 
                    f.folder_unique_id,
                    COUNT(CASE WHEN s.state = 'uploaded' THEN 1 END) as uploaded_segments,
                    COUNT(CASE WHEN s.state = 'pending' THEN 1 END) as pending_segments,
                    COUNT(CASE WHEN s.state = 'failed' THEN 1 END) as failed_segments,
                    COUNT(*) as total_segments
                FROM folders f
                JOIN files fi ON f.id = fi.folder_id
                JOIN segments s ON fi.id = s.file_id
                GROUP BY f.folder_unique_id
            """)
            
            conn.commit()

        
    def _get_embedded_schema(self) -> str:
        """Get embedded schema if file not found"""
        return """-- UsenetSync Database Schema
-- Optimized for millions of files with performance considerations
-- Single user profile system

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;
PRAGMA mmap_size=268435456;

-- User configuration (single user profile)
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT, -- JSON
    download_path TEXT DEFAULT '.downloads',
    temp_path TEXT DEFAULT '.temp',
    last_active TIMESTAMP
);

-- Folders being managed
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_unique_id TEXT NOT NULL UNIQUE,
    folder_path TEXT NOT NULL,
    display_name TEXT NOT NULL,
    share_type TEXT CHECK(share_type IN ('public', 'private', 'protected')),
    private_key BLOB,
    public_key BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP,
    last_published TIMESTAMP,
    current_version INTEGER DEFAULT 1,
    total_files INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    state TEXT DEFAULT 'active' CHECK(state IN ('active', 'deleted', 'archived'))
);

-- Files within folders
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    segment_count INTEGER DEFAULT 0,
    state TEXT DEFAULT 'indexed' CHECK(state IN ('indexed', 'modified', 'deleted', 'uploading', 'uploaded')),
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, file_path, version)
);

-- Segments for files
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,
    segment_hash TEXT NOT NULL,
    segment_size INTEGER NOT NULL,
    offset INTEGER DEFAULT 0,
                    offset INTEGER DEFAULT 0,
    subject_hash TEXT NOT NULL,
    message_id TEXT,
    newsgroup TEXT NOT NULL,
    uploaded_at TIMESTAMP,
    redundancy_index INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending' CHECK(state IN ('pending', 'uploading', 'uploaded', 'failed')),
    retry_count INTEGER DEFAULT 0,
    internal_subject TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, segment_index, redundancy_index)
);

-- Folder versions for tracking
CREATE TABLE IF NOT EXISTS folder_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT, -- JSON
    segments_added INTEGER DEFAULT 0,
    segments_modified INTEGER DEFAULT 0,
    segments_deleted INTEGER DEFAULT 0,
    index_size INTEGER,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, version)
);

-- Change journal for incremental updates
CREATE TABLE IF NOT EXISTS change_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('added', 'modified', 'deleted')),
    old_version INTEGER,
    new_version INTEGER,
    old_hash TEXT,
    new_hash TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    segments_affected TEXT, -- JSON array
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Access control (local tracking only)
CREATE TABLE IF NOT EXISTS access_control_local (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, user_id)
);

-- Published indexes
CREATE TABLE IF NOT EXISTS published_indexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    share_id TEXT NOT NULL UNIQUE,
    access_string TEXT NOT NULL,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_size INTEGER,
    segment_count INTEGER DEFAULT 1,
    share_type TEXT NOT NULL,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Publications table (for backward compatibility)
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id TEXT NOT NULL UNIQUE,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    access_string TEXT NOT NULL,
    share_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_size INTEGER,
    is_active BOOLEAN DEFAULT 1,
    revoked_at TIMESTAMP,
    revocation_note TEXT,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Upload sessions
CREATE TABLE IF NOT EXISTS upload_sessions (
    session_id TEXT PRIMARY KEY,
    folder_id INTEGER NOT NULL,
    total_segments INTEGER NOT NULL,
    uploaded_segments INTEGER DEFAULT 0,
    state TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Download sessions
CREATE TABLE IF NOT EXISTS download_sessions (
    session_id TEXT PRIMARY KEY,
    access_string TEXT NOT NULL,
    folder_name TEXT,
    total_files INTEGER,
    total_size INTEGER,
    downloaded_files INTEGER DEFAULT 0,
    downloaded_size INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Download progress tracking
CREATE TABLE IF NOT EXISTS download_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    downloaded_size INTEGER DEFAULT 0,
    segment_count INTEGER,
    completed_segments INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending',
    error_count INTEGER DEFAULT 0,
    FOREIGN KEY(session_id) REFERENCES download_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, file_path)
);

-- Server configurations
CREATE TABLE IF NOT EXISTS server_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT,
    password TEXT,
    use_ssl BOOLEAN DEFAULT TRUE,
    max_connections INTEGER DEFAULT 10,
    priority INTEGER DEFAULT 1,
    enabled BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0
);

-- Upload queue
CREATE TABLE IF NOT EXISTS upload_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5,
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY(segment_id) REFERENCES segments(id) ON DELETE CASCADE
);

        -- Segment upload queue (for segment-based uploads)
        CREATE TABLE IF NOT EXISTS segment_upload_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_id INTEGER NOT NULL,
            priority INTEGER DEFAULT 5,
            retry_count INTEGER DEFAULT 0,
            queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (segment_id) REFERENCES segments(id)
        );

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_files_folder_path ON files(folder_id, file_path);
CREATE INDEX IF NOT EXISTS idx_files_state ON files(state);
CREATE INDEX IF NOT EXISTS idx_segments_file_index ON segments(file_id, segment_index);
CREATE INDEX IF NOT EXISTS idx_segments_state ON segments(state);
CREATE INDEX IF NOT EXISTS idx_segments_message_id ON segments(message_id);
CREATE INDEX IF NOT EXISTS idx_change_journal_folder ON change_journal(folder_id, changed_at);
CREATE INDEX IF NOT EXISTS idx_download_progress_session ON download_progress(session_id, state);
CREATE INDEX IF NOT EXISTS idx_upload_queue_priority ON upload_queue(priority, queued_at);

        CREATE INDEX IF NOT EXISTS idx_segment_upload_queue_segment ON segment_upload_queue(segment_id);
        CREATE INDEX IF NOT EXISTS idx_segment_upload_queue_priority ON segment_upload_queue(priority, queued_at);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_folder ON upload_sessions(folder_id);
CREATE INDEX IF NOT EXISTS idx_publications_folder ON publications(folder_id);

-- Views for common queries
CREATE VIEW IF NOT EXISTS folder_statistics AS
SELECT 
    f.id,
    f.folder_unique_id,
    f.display_name,
    f.share_type,
    f.current_version,
    f.state,  -- Include the state column
    COUNT(DISTINCT fi.id) as file_count,
    COALESCE(SUM(fi.file_size), 0) as total_size,
    COUNT(DISTINCT s.id) as segment_count,
    MAX(fi.modified_at) as last_modified
FROM folders f
LEFT JOIN files fi ON f.id = fi.folder_id AND fi.state != 'deleted'
LEFT JOIN segments s ON fi.id = s.file_id
GROUP BY f.id;

CREATE VIEW IF NOT EXISTS upload_statistics AS
SELECT 
    f.folder_unique_id,
    COUNT(CASE WHEN s.state = 'uploaded' THEN 1 END) as uploaded_segments,
    COUNT(CASE WHEN s.state = 'pending' THEN 1 END) as pending_segments,
    COUNT(CASE WHEN s.state = 'failed' THEN 1 END) as failed_segments,
    COUNT(*) as total_segments
FROM folders f
JOIN files fi ON f.id = fi.folder_id
JOIN segments s ON fi.id = s.file_id
GROUP BY f.folder_unique_id;"""
        
    # User Management
    
    def initialize_user(self, user_id: str, display_name: Optional[str] = None) -> bool:
        """Initialize the single user profile"""
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO user_config 
                    (id, user_id, display_name, preferences)
                    VALUES (1, ?, ?, ?)
                """, (user_id, display_name or "User", json.dumps({})))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Failed to initialize user: {e}")
                return False
                
    def get_user_config(self) -> Optional[Dict]:
        """Get user configuration"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM user_config WHERE id = 1")
            row = cursor.fetchone()
            if row:
                config = dict(row)
                config['preferences'] = json.loads(config['preferences'] or '{}')
                return config
            return None
            
    def update_user_preferences(self, preferences: Dict) -> bool:
        """Update user preferences"""
        with self.pool.get_connection() as conn:
            try:
                conn.execute("""
                    UPDATE user_config 
                    SET preferences = ?, last_active = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (json.dumps(preferences),))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to update preferences: {e}")
                return False
                
    # Folder Management

    def create_folder(self, folder_unique_id: str, folder_path: str,
                     display_name: str, share_type: str = 'private') -> int:
        """Create new folder entry"""
        logger.info(f"FOLDER_DEBUG: Creating folder record: {folder_path}")
        # Validate share_type
        valid_share_types = ['public', 'private', 'protected']
        if share_type not in valid_share_types:
            raise ValueError(f"Invalid share_type: {share_type}. Must be one of {valid_share_types}")
            
        with self.pool.get_connection() as conn:
            logger.info(f"FOLDER_DEBUG: Inserting folder into database")
            cursor = conn.execute("""
                INSERT INTO folders 
                (folder_unique_id, folder_path, display_name, share_type)
                VALUES (?, ?, ?, ?)
            """, (folder_unique_id, folder_path, display_name, share_type))
            conn.commit()
            return cursor.lastrowid
    
    def get_folder(self, folder_id) -> Optional[Dict]:
        """Get folder by ID (supports both int and string)"""
        with self.pool.get_connection() as conn:
            if isinstance(folder_id, int):
                cursor = conn.execute("""
                    SELECT * FROM folders WHERE id = ?
                """, (folder_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM folders WHERE folder_unique_id = ?
                """, (folder_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_folder_by_id(self, folder_id: int) -> Optional[Dict]:
        """Get folder by numeric ID"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM folders WHERE id = ?
            """, (folder_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_all_folders(self) -> List[Dict]:
        """Get all active folders"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM folder_statistics 
                WHERE state = 'active'
                ORDER BY display_name
            """)
            return [dict(row) for row in cursor]
            
    def update_folder_keys(self, folder_id: int, private_key: bytes, public_key: bytes):
        """Update folder cryptographic keys"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE folders 
                SET private_key = ?, public_key = ?
                WHERE id = ?
            """, (private_key, public_key, folder_id))
            conn.commit()
            
    def update_folder_stats(self, folder_id: int):
        """Update folder statistics"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE folders SET
                    total_files = (
                        SELECT COUNT(*) FROM files 
                        WHERE folder_id = ? AND state != 'deleted'
                    ),
                    total_size = (
                        SELECT COALESCE(SUM(file_size), 0) FROM files 
                        WHERE folder_id = ? AND state != 'deleted'
                    ),
                    last_indexed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (folder_id, folder_id, folder_id))
            conn.commit()
            
    # File Management

    def add_file(self, folder_id: int, file_path: str, file_hash: str, 
                 file_size: int, modified_at: datetime, version: int = 1) -> int:
        """Add file to database"""
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO files 
                    (folder_id, file_path, file_hash, file_size, modified_at, version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                if "FOREIGN KEY constraint failed" in str(e):
                    raise ValueError(f"Folder with id {folder_id} does not exist")
                raise

    
    
    def get_file(self, folder_id: int, file_path: str, version: Optional[int] = None) -> Optional[Dict]:
        """Get file information"""
        with self.pool.get_connection() as conn:
            if version:
                cursor = conn.execute("""
                    SELECT * FROM files 
                    WHERE folder_id = ? AND file_path = ? AND version = ?
                """, (folder_id, file_path, version))
            else:
                cursor = conn.execute("""
                    SELECT * FROM files 
                    WHERE folder_id = ? AND file_path = ?
                    ORDER BY version DESC LIMIT 1
                """, (folder_id, file_path))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_file_by_id(self, file_id: int) -> Optional[Dict]:
        """Get file by ID"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE id = ?
            """, (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_folder_files(self, folder_id: int, state: Optional[str] = None) -> List[Dict]:
        """Get all files in folder"""
        with self.pool.get_connection() as conn:
            if state:
                cursor = conn.execute("""
                    SELECT * FROM files 
                    WHERE folder_id = ? AND state = ?
                    ORDER BY file_path
                """, (folder_id, state))
            else:
                cursor = conn.execute("""
                    SELECT * FROM files 
                    WHERE folder_id = ? AND state != 'deleted'
                    ORDER BY file_path
                """, (folder_id,))
            return [dict(row) for row in cursor]
            
    def get_folder_segments_to_upload(self, folder_id: int) -> list:
        """Get all segments that need to be uploaded for a folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.* FROM segments s
                JOIN files f ON s.file_id = f.id
                WHERE f.folder_id = ? 
                AND (s.state IS NULL OR s.state = 'pending')
                AND s.message_id IS NULL
                ORDER BY f.id, s.segment_index
            """, (folder_id,))
            
            segments = []
            for row in cursor:
                segments.append({
                    'segment_id': row['id'],
                    'file_id': row['file_id'],
                    'segment_index': row['segment_index'],
                    'segment_hash': row['segment_hash']
                })
                
            return segments

    def update_file_state(self, file_id: int, state: str):
        """Update file state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE files SET state = ? WHERE id = ?
            """, (state, file_id))
            conn.commit()
            
    def update_file_segment_count(self, file_id: int, segment_count: int):
        """Update file segment count"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE files SET segment_count = ? WHERE id = ?
            """, (segment_count, file_id))
            conn.commit()
            
    # Segment Management
    
    def add_segment(self, file_id: int, segment_index: int, segment_hash: str,
                   segment_size: int, subject_hash: str, newsgroup: str,
                   redundancy_index: int = 0) -> int:
        """Add segment to database"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO segments 
                (file_id, segment_index, segment_hash, segment_size, 
                 subject_hash, newsgroup, redundancy_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, segment_index, segment_hash, segment_size,
                  subject_hash, newsgroup, redundancy_index))
            conn.commit()
            return cursor.lastrowid
    
    def set_segment_offset(self, segment_id: int, offset: int):
        """Set the offset for a segment after creation"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE segments SET offset = ? WHERE id = ?
            """, (offset, segment_id))
            conn.commit()
            
    def bulk_insert_segments(self, segments: List[Dict]):
        """Bulk insert segments"""
        with self.pool.get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO segments 
                (file_id, segment_index, segment_hash, segment_size,
                 subject_hash, newsgroup, redundancy_index)
                VALUES (:file_id, :segment_index, :segment_hash, :segment_size,
                        :subject_hash, :newsgroup, :redundancy_index)
            """, segments)
            conn.commit()
            
    def get_file_segments(self, file_id: int) -> List[Dict]:
        """Get all segments for file"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM segments 
                WHERE file_id = ?
                ORDER BY segment_index, redundancy_index
            """, (file_id,))
            return [dict(row) for row in cursor]
            
    def get_folder_segments(self, folder_id: int) -> List[Dict]:
        """Get all segments for all files in a folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.*, f.file_path
                FROM segments s
                JOIN files f ON s.file_id = f.id
                WHERE f.folder_id = ? AND f.state != 'deleted'
                ORDER BY f.id, s.segment_index
            """, (folder_id,))
            return [dict(row) for row in cursor]
            
    def get_segment_by_id(self, segment_id: int) -> Optional[Dict]:
        """Get segment by ID"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM segments WHERE id = ?
            """, (segment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def update_segment_upload(self, segment_id: int, message_id: str):
        """Update segment after successful upload"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE segments 
                SET message_id = ?, uploaded_at = CURRENT_TIMESTAMP, state = 'uploaded'
                WHERE id = ?
            """, (message_id, segment_id))
            conn.commit()
            
    def update_segment_state(self, segment_id: int, state: str):
        """Update segment state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE segments SET state = ? WHERE id = ?
            """, (state, segment_id))
            conn.commit()
            
    # Version Management
    
    def create_folder_version(self, folder_id: int, version: int, 
                            change_summary: Dict) -> int:
        """Create new folder version"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO folder_versions 
                (folder_id, version, change_summary)
                VALUES (?, ?, ?)
            """, (folder_id, version, json.dumps(change_summary)))
            
            # Update folder current version
            conn.execute("""
                UPDATE folders SET current_version = ? WHERE id = ?
            """, (version, folder_id))
            
            conn.commit()
            return cursor.lastrowid
            
    def get_folder_versions(self, folder_id: int) -> List[Dict]:
        """Get all versions for folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM folder_versions 
                WHERE folder_id = ?
                ORDER BY version DESC
            """, (folder_id,))
            return [dict(row) for row in cursor]
            
    # Change Journal
    
    def record_change(self, folder_id: int, file_path: str, change_type: str,
                     old_version: Optional[int] = None, new_version: Optional[int] = None,
                     old_hash: Optional[str] = None, new_hash: Optional[str] = None):
        """Record file change in journal"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                INSERT INTO change_journal 
                (folder_id, file_path, change_type, old_version, new_version,
                 old_hash, new_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (folder_id, file_path, change_type, old_version, new_version,
                  old_hash, new_hash))
            conn.commit()
            
    def get_folder_changes(self, folder_id: int, since_version: Optional[int] = None) -> List[Dict]:
        """Get changes for folder"""
        with self.pool.get_connection() as conn:
            if since_version:
                cursor = conn.execute("""
                    SELECT * FROM change_journal 
                    WHERE folder_id = ? AND new_version > ?
                    ORDER BY changed_at
                """, (folder_id, since_version))
            else:
                cursor = conn.execute("""
                    SELECT * FROM change_journal 
                    WHERE folder_id = ?
                    ORDER BY changed_at
                """, (folder_id,))
            return [dict(row) for row in cursor]
            
    # Access Control
    
    def add_authorized_user(self, folder_id: int, user_id: str, added_by: str):
        """Add authorized user for private share"""
        with self.pool.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO access_control_local 
                    (folder_id, user_id, added_by)
                    VALUES (?, ?, ?)
                """, (folder_id, user_id, added_by))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Already exists
                
    def remove_authorized_user(self, folder_id: int, user_id: str) -> bool:
        """Remove authorized user"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM access_control_local 
                WHERE folder_id = ? AND user_id = ?
            """, (folder_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
            
    def get_authorized_users(self, folder_id: int) -> List[str]:
        """Get all authorized users for folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT user_id FROM access_control_local 
                WHERE folder_id = ?
                ORDER BY added_at
            """, (folder_id,))
            return [row['user_id'] for row in cursor]
            
    # Publishing
    
    def record_publication(self, folder_id: int, version: int, share_id: str,
                          access_string: str, index_size: int, share_type: str):
        """Record published index"""
        with self.pool.get_connection() as conn:
            # Insert into published_indexes
            conn.execute("""
                INSERT INTO published_indexes 
                (folder_id, version, share_id, access_string, index_size, share_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (folder_id, version, share_id, access_string, index_size, share_type))
            
            # Also insert into publications for backward compatibility
            conn.execute("""
                INSERT INTO publications 
                (share_id, folder_id, version, access_string, share_type, index_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (share_id, folder_id, version, access_string, share_type, index_size))
            
            # Update folder
            conn.execute("""
                UPDATE folders SET last_published = CURRENT_TIMESTAMP WHERE id = ?
            """, (folder_id,))
            
            conn.commit()
            
    def get_latest_publication(self, folder_id: int) -> Optional[Dict]:
        """Get latest publication for folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM published_indexes 
                WHERE folder_id = ?
                ORDER BY published_at DESC
                LIMIT 1
            """, (folder_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_all_shares(self) -> List[Dict]:
        """Get all published shares"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    share_id,
                    folder_id,
                    version,
                    access_string,
                    share_type,
                    created_at,
                    index_size,
                    is_active
                FROM publications
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor]
            
    def get_folder_shares(self, folder_id: int) -> List[Dict]:
        """Get all shares for a specific folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    share_id,
                    version,
                    access_string,
                    share_type,
                    published_at as created_at,
                    index_size,
                    segment_count
                FROM published_indexes
                WHERE folder_id = ?
                ORDER BY version DESC
            """, (folder_id,))
            return [dict(row) for row in cursor]
            
    def revoke_share(self, share_id: str) -> bool:
        """
        Mark a share as revoked locally.
        
        IMPORTANT: This does NOT remove anything from Usenet (impossible).
        It only:
        1. Marks the share as inactive in local database
        2. Prevents including revoked users in future publications
        3. Old index files on Usenet remain accessible forever
        """
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE publications 
                SET is_active = 0, 
                    revoked_at = CURRENT_TIMESTAMP,
                    revocation_note = 'Share marked inactive - old versions remain on Usenet'
                WHERE share_id = ?
            """, (share_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    # Upload Session Management
    
    def create_upload_session(self, session_id: str, folder_id: Union[int, str], 
                            total_segments: int):
        """Create upload session record"""
        with self.pool.get_connection() as conn:
            # Convert folder_id to int if it's a string
            if isinstance(folder_id, str):
                cursor = conn.execute("SELECT id FROM folders WHERE folder_unique_id = ?", 
                                    (folder_id,))
                row = cursor.fetchone()
                if row:
                    folder_id = row['id']
                else:
                    raise ValueError(f"Folder not found: {folder_id}")
                    
            conn.execute("""
                INSERT INTO upload_sessions 
                (session_id, folder_id, total_segments, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (session_id, folder_id, total_segments))
            conn.commit()
            
    def get_upload_session(self, session_id: str) -> Optional[Dict]:
        """Get upload session info"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM upload_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def update_upload_session_state(self, session_id: str, state: str):
        """Update upload session state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE upload_sessions 
                SET state = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (state, session_id))
            conn.commit()
            
    def cleanup_old_upload_sessions(self, older_than_hours: int):
        """Clean up old upload sessions"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                DELETE FROM upload_sessions 
                WHERE created_at < datetime('now', '-' || ? || ' hours')
            """, (older_than_hours,))
            conn.commit()
            
    # Download Management
    
    def create_download_session(self, session_id: str, access_string: str,
                              folder_name: str, total_files: int, total_size: int) -> bool:
        """Create new download session"""
        with self.pool.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO download_sessions 
                    (session_id, access_string, folder_name, total_files, total_size)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, access_string, folder_name, total_files, total_size))
                conn.commit()
                return True
            except:
                return False
                
    def update_download_progress(self, session_id: str, downloaded_files: int, 
                               downloaded_size: int):
        """Update download progress"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE download_sessions 
                SET downloaded_files = ?, downloaded_size = ?
                WHERE session_id = ?
            """, (downloaded_files, downloaded_size, session_id))
            conn.commit()
            
    def get_download_session(self, session_id: str) -> Optional[Dict]:
        """Get download session info"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM download_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def update_download_session_state(self, session_id: str, state: str):
        """Update download session state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE download_sessions 
                SET state = ?, 
                    completed_at = CASE 
                        WHEN ? IN ('completed', 'failed', 'cancelled') 
                        THEN CURRENT_TIMESTAMP 
                        ELSE completed_at 
                    END
                WHERE session_id = ?
            """, (state, state, session_id))
            conn.commit()
            
    # Server Configuration
    
    def add_server_config(self, server_name: str, hostname: str, port: int,
                         username: str, password: str, use_ssl: bool = True,
                         max_connections: int = 10) -> int:
        """Add server configuration"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO server_configs 
                (server_name, hostname, port, username, password, use_ssl, max_connections)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (server_name, hostname, port, username, password, use_ssl, max_connections))
            conn.commit()
            return cursor.lastrowid
            
    def get_server_configs(self, enabled_only: bool = True) -> List[Dict]:
        """Get server configurations"""
        with self.pool.get_connection() as conn:
            if enabled_only:
                cursor = conn.execute("""
                    SELECT * FROM server_configs 
                    WHERE enabled = TRUE
                    ORDER BY priority
                """)
            else:
                cursor = conn.execute("""
                    SELECT * FROM server_configs ORDER BY priority
                """)
            return [dict(row) for row in cursor]
            
    def update_server_stats(self, server_id: int, success: bool):
        """Update server statistics"""
        with self.pool.get_connection() as conn:
            if success:
                conn.execute("""
                    UPDATE server_configs 
                    SET success_count = success_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (server_id,))
            else:
                conn.execute("""
                    UPDATE server_configs 
                    SET failure_count = failure_count + 1
                    WHERE id = ?
                """, (server_id,))
            conn.commit()
            
    # Upload Queue
    
    def queue_upload(self, segment_id: int, priority: int = 5):
        """Add segment to upload queue"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                INSERT INTO upload_queue (segment_id, priority)
                VALUES (?, ?)
            """, (segment_id, priority))
            conn.commit()
            
    def get_next_upload(self) -> Optional[Dict]:
        """Get next segment to upload"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT uq.*, s.*, f.file_path, fo.folder_unique_id
                FROM upload_queue uq
                JOIN segments s ON uq.segment_id = s.id
                JOIN files f ON s.file_id = f.id
                JOIN folders fo ON f.folder_id = fo.id
                WHERE uq.completed_at IS NULL
                ORDER BY uq.priority DESC, uq.queued_at
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                # Mark as started
                conn.execute("""
                    UPDATE upload_queue SET started_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (row['id'],))
                conn.commit()
                
            return dict(row) if row else None
            
    def complete_upload(self, queue_id: int, success: bool, error_message: Optional[str] = None):
        """Mark upload as complete"""
        with self.pool.get_connection() as conn:
            if success:
                conn.execute("""
                    UPDATE upload_queue 
                    SET completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (queue_id,))
            else:
                conn.execute("""
                    UPDATE upload_queue 
                    SET retry_count = retry_count + 1, error_message = ?,
                        started_at = NULL
                    WHERE id = ?
                """, (error_message, queue_id))
            conn.commit()
            
    def get_pending_uploads(self, limit: int = 100) -> List[Dict]:
        """Get pending upload tasks"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    uq.id as task_id,
                    f.folder_id,
                    fi.file_path,
                    'pending' as status,
                    uq.queued_at as created_at
                FROM upload_queue uq
                JOIN segments s ON uq.segment_id = s.id
                JOIN files fi ON s.file_id = fi.id
                JOIN folders f ON fi.folder_id = f.id
                WHERE uq.completed_at IS NULL
                ORDER BY uq.priority DESC, uq.queued_at
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor]
            
    # Statistics and Monitoring
    
    def get_upload_statistics(self, folder_id: Optional[int] = None) -> Dict:
        """Get upload statistics"""
        with self.pool.get_connection() as conn:
            if folder_id:
                cursor = conn.execute("""
                    SELECT * FROM upload_statistics
                    WHERE folder_unique_id = (
                        SELECT folder_unique_id FROM folders WHERE id = ?
                    )
                """, (folder_id,))
            else:
                cursor = conn.execute("SELECT * FROM upload_statistics")
                
            stats = {}
            for row in cursor:
                stats[row['folder_unique_id']] = dict(row)
            return stats
            
    def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
        with self.pool.get_connection() as conn:
            stats = {}
            
            # Table sizes
            cursor = conn.execute("""
                SELECT name, COUNT(*) as count
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            for table in cursor:
                count_cursor = conn.execute(f"SELECT COUNT(*) as c FROM {table['name']}")
                stats[f"{table['name']}_count"] = count_cursor.fetchone()['c']
                
            # Database size
            cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            stats['database_size'] = cursor.fetchone()['size']
            
            return stats
            
    # Maintenance
    
    def vacuum(self):
        """Vacuum database to reclaim space"""
        with self.pool.get_connection() as conn:
            conn.execute("VACUUM")
            
    def analyze(self):
        """Analyze database for query optimization"""
        with self.pool.get_connection() as conn:
            conn.execute("ANALYZE")
            
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old download sessions"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                DELETE FROM download_sessions 
                WHERE started_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            conn.commit()
            
    # Compatibility methods
    
    def get_connection(self):
        """Get a database connection (compatibility method)"""
        # Return a connection that must be released with release_connection
        return self.pool._connections.get(timeout=30)
    
    def release_connection(self, conn):
        """Release a database connection back to the pool (compatibility method)"""
        if conn and not self.pool._closed:
            self.pool._connections.put(conn)

    def get_folder_by_unique_id(self, unique_id: str) -> Optional[Dict]:
        """Get folder by unique ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM folders WHERE folder_unique_id = ?",
                (unique_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


    def close(self):
        """Close database connections"""
        self.pool.close_all()

# Helper functions for common operations

def initialize_database(config: Optional[DatabaseConfig] = None) -> EnhancedDatabaseManager:
    """Initialize and return database manager"""
    return EnhancedDatabaseManager(config)

def get_default_db_path() -> str:
    """Get default database path"""
    return os.path.join(os.path.expanduser("~"), ".usenetsync", "usenetsync.db")
