#!/usr/bin/env python3
"""
Migration System for UsenetSync
Migrates data from old architecture to unified system
"""

import os
import sys
import logging
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.database_schema import UnifiedDatabaseSchema
from unified.unified_system import UnifiedDatabaseManager

logger = logging.getLogger(__name__)

class MigrationSystem:
    """Handles migration from old architecture to unified system"""
    
    def __init__(self, target_db_type: str = 'sqlite', **target_db_params):
        """
        Initialize migration system
        
        Args:
            target_db_type: Target database type ('sqlite' or 'postgresql')
            **target_db_params: Target database connection parameters
        """
        self.target_db_type = target_db_type
        self.target_db_params = target_db_params
        self.target_db = None
        self.migration_stats = {
            'files_migrated': 0,
            'segments_migrated': 0,
            'folders_migrated': 0,
            'shares_migrated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def migrate_from_old_system(self, old_db_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Migrate from old multi-database system to unified
        
        Args:
            old_db_paths: Dictionary of old database paths
                {
                    'indexing': 'path/to/indexing.db',
                    'upload': 'path/to/upload.db',
                    'download': 'path/to/download.db',
                    'security': 'path/to/security.db'
                }
                
        Returns:
            Migration statistics
        """
        logger.info("Starting migration from old system to unified architecture")
        self.migration_stats['start_time'] = datetime.now()
        
        try:
            # Create target database
            self._create_target_database()
            
            # Migrate each component
            if 'indexing' in old_db_paths:
                self._migrate_indexing_data(old_db_paths['indexing'])
                
            if 'upload' in old_db_paths:
                self._migrate_upload_data(old_db_paths['upload'])
                
            if 'download' in old_db_paths:
                self._migrate_download_data(old_db_paths['download'])
                
            if 'security' in old_db_paths:
                self._migrate_security_data(old_db_paths['security'])
                
            # Verify migration
            self._verify_migration()
            
            self.migration_stats['end_time'] = datetime.now()
            duration = (self.migration_stats['end_time'] - 
                       self.migration_stats['start_time']).total_seconds()
            self.migration_stats['duration'] = duration
            
            logger.info(f"Migration completed successfully in {duration:.2f} seconds")
            logger.info(f"Migrated: {self.migration_stats['files_migrated']} files, "
                       f"{self.migration_stats['segments_migrated']} segments, "
                       f"{self.migration_stats['folders_migrated']} folders, "
                       f"{self.migration_stats['shares_migrated']} shares")
            
            return self.migration_stats
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_stats['errors'] += 1
            raise
            
    def _create_target_database(self):
        """Create and initialize target unified database"""
        logger.info(f"Creating target {self.target_db_type} database")
        
        # Create schema
        schema = UnifiedDatabaseSchema(self.target_db_type, **self.target_db_params)
        schema.create_schema()
        
        # Initialize database manager
        self.target_db = UnifiedDatabaseManager(self.target_db_type, **self.target_db_params)
        self.target_db.connect()
        
    def _migrate_indexing_data(self, old_db_path: str):
        """Migrate data from old indexing database"""
        logger.info(f"Migrating indexing data from {old_db_path}")
        
        if not os.path.exists(old_db_path):
            logger.warning(f"Indexing database not found: {old_db_path}")
            return
            
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        cursor = old_conn.cursor()
        
        try:
            # Check which tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Migrate files table
            if 'files' in tables:
                self._migrate_files_table(cursor)
                
            # Migrate segments table
            if 'segments' in tables:
                self._migrate_segments_table(cursor)
                
            # Migrate folders if exists
            if 'folders' in tables:
                self._migrate_folders_table(cursor)
                
        finally:
            old_conn.close()
            
    def _migrate_files_table(self, old_cursor):
        """Migrate files from old database"""
        logger.info("Migrating files table")
        
        # Get column names from old table
        old_cursor.execute("PRAGMA table_info(files)")
        old_columns = {row[1] for row in old_cursor.fetchall()}
        
        # Build query based on available columns
        select_cols = []
        if 'file_id' in old_columns:
            select_cols.append('file_id')
        if 'folder_id' in old_columns:
            select_cols.append('folder_id')
        elif 'folder_path' in old_columns:
            # Generate folder_id from path
            select_cols.append("substr(hex(randomblob(32)), 1, 64) as folder_id")
            
        # Add other columns
        common_cols = ['file_path', 'file_hash', 'file_size', 'modified_time', 
                      'version', 'segment_count', 'state']
        for col in common_cols:
            if col in old_columns:
                select_cols.append(col)
                
        query = f"SELECT {', '.join(select_cols)} FROM files"
        old_cursor.execute(query)
        
        files = old_cursor.fetchall()
        
        for file_row in files:
            try:
                file_data = dict(file_row)
                
                # Generate folder_id if missing
                if 'folder_id' not in file_data or not file_data['folder_id']:
                    file_data['folder_id'] = hashlib.sha256(
                        f"migrated_{file_data.get('file_path', '')}".encode()
                    ).hexdigest()
                    
                # Ensure required fields
                file_data.setdefault('version', 1)
                file_data.setdefault('segment_count', 1)
                file_data.setdefault('state', 'indexed')
                
                # Convert timestamp if needed
                if 'modified_time' in file_data and isinstance(file_data['modified_time'], str):
                    try:
                        file_data['modified_time'] = datetime.fromisoformat(
                            file_data['modified_time']
                        )
                    except:
                        file_data['modified_time'] = datetime.now()
                        
                # Insert into unified database
                self.target_db.execute("""
                    INSERT INTO files 
                    (folder_id, file_path, file_hash, file_size, modified_time,
                     version, segment_count, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    file_data['folder_id'],
                    file_data.get('file_path', ''),
                    file_data.get('file_hash', ''),
                    file_data.get('file_size', 0),
                    file_data.get('modified_time', datetime.now()),
                    file_data.get('version', 1),
                    file_data.get('segment_count', 1),
                    file_data.get('state', 'indexed')
                ))
                
                self.migration_stats['files_migrated'] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate file: {e}")
                self.migration_stats['errors'] += 1
                
    def _migrate_segments_table(self, old_cursor):
        """Migrate segments from old database"""
        logger.info("Migrating segments table")
        
        old_cursor.execute("SELECT * FROM segments")
        segments = old_cursor.fetchall()
        
        for segment_row in segments:
            try:
                segment_data = dict(segment_row)
                
                # Map old file_id to new file_id if needed
                file_id = segment_data.get('file_id')
                
                if file_id:
                    # Insert segment
                    self.target_db.execute("""
                        INSERT INTO segments
                        (file_id, segment_index, segment_hash, segment_size,
                         message_id, usenet_subject, internal_subject,
                         upload_status, redundancy_level)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        file_id,
                        segment_data.get('segment_index', 0),
                        segment_data.get('segment_hash', ''),
                        segment_data.get('segment_size', 0),
                        segment_data.get('message_id'),
                        segment_data.get('usenet_subject'),
                        segment_data.get('internal_subject'),
                        segment_data.get('upload_status', 'pending'),
                        segment_data.get('redundancy_level', 0)
                    ))
                    
                    self.migration_stats['segments_migrated'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to migrate segment: {e}")
                self.migration_stats['errors'] += 1
                
    def _migrate_folders_table(self, old_cursor):
        """Migrate folders from old database"""
        logger.info("Migrating folders table")
        
        old_cursor.execute("SELECT * FROM folders")
        folders = old_cursor.fetchall()
        
        for folder_row in folders:
            try:
                folder_data = dict(folder_row)
                
                # Ensure folder_id exists
                if not folder_data.get('folder_id'):
                    folder_data['folder_id'] = hashlib.sha256(
                        f"{folder_data.get('folder_path', '')}_{datetime.now()}".encode()
                    ).hexdigest()
                    
                # Insert folder
                self.target_db.execute("""
                    INSERT INTO folders
                    (folder_id, folder_path, folder_name, owner_id,
                     public_key, private_key_encrypted, total_size,
                     file_count, segment_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    folder_data['folder_id'],
                    folder_data.get('folder_path', ''),
                    folder_data.get('folder_name', Path(folder_data.get('folder_path', '')).name),
                    folder_data.get('owner_id', 'migrated_user'),
                    folder_data.get('public_key', 'placeholder_public'),
                    folder_data.get('private_key_encrypted', 'placeholder_private'),
                    folder_data.get('total_size', 0),
                    folder_data.get('file_count', 0),
                    folder_data.get('segment_count', 0)
                ))
                
                self.migration_stats['folders_migrated'] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate folder: {e}")
                self.migration_stats['errors'] += 1
                
    def _migrate_upload_data(self, old_db_path: str):
        """Migrate data from old upload database"""
        logger.info(f"Migrating upload data from {old_db_path}")
        
        if not os.path.exists(old_db_path):
            logger.warning(f"Upload database not found: {old_db_path}")
            return
            
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        cursor = old_conn.cursor()
        
        try:
            # Check for upload_queue table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_queue'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM upload_queue WHERE status != 'completed'")
                queue_items = cursor.fetchall()
                
                for item in queue_items:
                    try:
                        item_data = dict(item)
                        
                        self.target_db.execute("""
                            INSERT INTO upload_queue
                            (segment_id, priority, attempt_count, status)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            item_data.get('segment_id'),
                            item_data.get('priority', 5),
                            item_data.get('attempt_count', 0),
                            item_data.get('status', 'pending')
                        ))
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate upload queue item: {e}")
                        
        finally:
            old_conn.close()
            
    def _migrate_download_data(self, old_db_path: str):
        """Migrate data from old download database"""
        logger.info(f"Migrating download data from {old_db_path}")
        
        if not os.path.exists(old_db_path):
            logger.warning(f"Download database not found: {old_db_path}")
            return
            
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        cursor = old_conn.cursor()
        
        try:
            # Check for downloads table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM downloads")
                downloads = cursor.fetchall()
                
                for download in downloads:
                    try:
                        dl_data = dict(download)
                        
                        self.target_db.execute("""
                            INSERT INTO downloads
                            (share_id, user_id, destination_path, total_files,
                             completed_files, total_segments, completed_segments,
                             total_size, downloaded_size, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            dl_data.get('share_id', ''),
                            dl_data.get('user_id'),
                            dl_data.get('destination_path', ''),
                            dl_data.get('total_files', 0),
                            dl_data.get('completed_files', 0),
                            dl_data.get('total_segments', 0),
                            dl_data.get('completed_segments', 0),
                            dl_data.get('total_size', 0),
                            dl_data.get('downloaded_size', 0),
                            dl_data.get('status', 'pending')
                        ))
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate download: {e}")
                        
        finally:
            old_conn.close()
            
    def _migrate_security_data(self, old_db_path: str):
        """Migrate data from old security database"""
        logger.info(f"Migrating security data from {old_db_path}")
        
        if not os.path.exists(old_db_path):
            logger.warning(f"Security database not found: {old_db_path}")
            return
            
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row
        cursor = old_conn.cursor()
        
        try:
            # Migrate users
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()
                
                for user in users:
                    try:
                        user_data = dict(user)
                        
                        self.target_db.execute("""
                            INSERT INTO users
                            (user_id, username, public_key, private_key_encrypted)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            user_data.get('user_id', ''),
                            user_data.get('username'),
                            user_data.get('public_key', ''),
                            user_data.get('private_key_encrypted')
                        ))
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate user: {e}")
                        
            # Migrate shares
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shares'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM shares")
                shares = cursor.fetchall()
                
                for share in shares:
                    try:
                        share_data = dict(share)
                        
                        self.target_db.execute("""
                            INSERT INTO shares
                            (share_id, folder_id, share_type, access_string,
                             encrypted_index, index_size, index_segments,
                             active)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            share_data.get('share_id', ''),
                            share_data.get('folder_id', ''),
                            share_data.get('share_type', 'PUBLIC'),
                            share_data.get('access_string', ''),
                            share_data.get('encrypted_index', '{}'),
                            share_data.get('index_size', 0),
                            share_data.get('index_segments', 1),
                            share_data.get('active', True)
                        ))
                        
                        self.migration_stats['shares_migrated'] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to migrate share: {e}")
                        
        finally:
            old_conn.close()
            
    def _verify_migration(self):
        """Verify migration was successful"""
        logger.info("Verifying migration integrity")
        
        # Check record counts
        checks = [
            ("files", "SELECT COUNT(*) as count FROM files"),
            ("segments", "SELECT COUNT(*) as count FROM segments"),
            ("folders", "SELECT COUNT(*) as count FROM folders"),
            ("shares", "SELECT COUNT(*) as count FROM shares")
        ]
        
        for table_name, query in checks:
            result = self.target_db.fetchone(query, ())
            count = result['count'] if hasattr(result, '__getitem__') else result[0]
            logger.info(f"  {table_name}: {count} records")
            
    def backup_old_databases(self, old_db_paths: Dict[str, str], backup_dir: str):
        """Create backups of old databases before migration"""
        logger.info(f"Creating backups in {backup_dir}")
        
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        for db_type, db_path in old_db_paths.items():
            if os.path.exists(db_path):
                backup_path = Path(backup_dir) / f"{db_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, backup_path)
                logger.info(f"  Backed up {db_type} to {backup_path}")


def test_migration():
    """Test migration system"""
    print("\n=== Testing Migration System ===\n")
    
    # Create test old databases
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="migration_test_")
    
    # Create sample old database
    old_db_path = Path(temp_dir) / "old_indexing.db"
    old_conn = sqlite3.connect(old_db_path)
    
    # Create old schema
    old_conn.execute("""
        CREATE TABLE files (
            file_id INTEGER PRIMARY KEY,
            file_path TEXT,
            file_hash TEXT,
            file_size INTEGER,
            modified_time TEXT,
            version INTEGER,
            segment_count INTEGER,
            state TEXT
        )
    """)
    
    old_conn.execute("""
        CREATE TABLE segments (
            segment_id INTEGER PRIMARY KEY,
            file_id INTEGER,
            segment_index INTEGER,
            segment_hash TEXT,
            segment_size INTEGER
        )
    """)
    
    # Insert test data
    old_conn.execute("""
        INSERT INTO files (file_path, file_hash, file_size, modified_time, version, segment_count, state)
        VALUES ('test/file1.txt', 'hash1', 1024, datetime('now'), 1, 2, 'indexed')
    """)
    
    old_conn.execute("""
        INSERT INTO segments (file_id, segment_index, segment_hash, segment_size)
        VALUES (1, 0, 'seg_hash1', 512), (1, 1, 'seg_hash2', 512)
    """)
    
    old_conn.commit()
    old_conn.close()
    
    # Run migration
    print("Running migration...")
    
    migrator = MigrationSystem('sqlite', path=Path(temp_dir) / 'unified.db')
    
    stats = migrator.migrate_from_old_system({
        'indexing': str(old_db_path)
    })
    
    print(f"\nMigration Results:")
    print(f"  Files migrated: {stats['files_migrated']}")
    print(f"  Segments migrated: {stats['segments_migrated']}")
    print(f"  Errors: {stats['errors']}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\n✓ Migration test completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_migration()