#!/usr/bin/env python3
"""
Ensure Database Schema is Complete and Correct
Creates all required tables and indexes for the usenet sync system
"""

import sqlite3
import time
from pathlib import Path

def create_complete_schema():
    """Create complete database schema with all required tables"""
    
    db_path = Path("data/usenetsync.db")
    db_path.parent.mkdir(exist_ok=True)
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60.0)
        
        # Enable WAL mode first
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        
        print("Creating database schema...")
        
        # Create folders table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                folder_hash TEXT,
                private_key BLOB,
                public_key BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keys_updated_at TIMESTAMP,
                version INTEGER DEFAULT 1,
                file_count INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                state TEXT DEFAULT 'active'
            )
        """)
        
        # Create files table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                modified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                state TEXT DEFAULT 'indexed',
                FOREIGN KEY (folder_id) REFERENCES folders (id),
                UNIQUE(folder_id, file_path)
            )
        """)
        
        # Create segments table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                segment_index INTEGER NOT NULL,
                segment_hash TEXT,
                segment_size INTEGER,
                data_offset INTEGER,
                redundancy_index INTEGER DEFAULT 0,
                state TEXT DEFAULT 'pending',
                article_id TEXT,
                upload_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id),
                UNIQUE(file_id, segment_index)
            )
        """)
        
        # Create folder_versions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS folder_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                change_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders (id),
                UNIQUE(folder_id, version)
            )
        """)
        
        # Create publications table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_id TEXT UNIQUE NOT NULL,
                folder_id INTEGER NOT NULL,
                version INTEGER DEFAULT 1,
                access_string TEXT,
                share_type TEXT DEFAULT 'read_only',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                index_size INTEGER,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (folder_id) REFERENCES folders (id)
            )
        """)
        
        # Create upload_queue table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                folder_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create upload_sessions table
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
        
        # Create authorized_users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorized_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                permission_level TEXT DEFAULT 'read',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders (id),
                UNIQUE(folder_id, user_id)
            )
        """)
        
        print("OK: Created all required tables")
        
        # Create indexes for better performance
        print("Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files (folder_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_state ON files (state)",
            "CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments (file_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_state ON segments (state)",
            "CREATE INDEX IF NOT EXISTS idx_upload_queue_status ON upload_queue (status)",
            "CREATE INDEX IF NOT EXISTS idx_publications_share_id ON publications (share_id)",
            "CREATE INDEX IF NOT EXISTS idx_authorized_users_folder ON authorized_users (folder_id)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        print("OK: Created all indexes")
        
        # Vacuum and analyze
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        
        conn.close()
        print("OK: Database schema complete and optimized")
        return True
        
    except Exception as e:
        print(f"ERROR: Could not create database schema: {e}")
        return False

def verify_schema():
    """Verify that all required tables and columns exist"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database does not exist")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        # Check required tables
        required_tables = [
            'folders', 'files', 'segments', 'folder_versions',
            'publications', 'upload_queue', 'upload_sessions', 'authorized_users'
        ]
        
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"ERROR: Missing tables: {missing_tables}")
            conn.close()
            return False
        
        # Check files table has required columns
        cursor = conn.execute("PRAGMA table_info(files)")
        files_columns = [row[1] for row in cursor.fetchall()]
        
        required_files_columns = ['id', 'folder_id', 'file_path', 'file_hash', 'file_size', 'modified_at', 'version', 'state']
        missing_columns = []
        for col in required_files_columns:
            if col not in files_columns:
                missing_columns.append(f"files.{col}")
        
        # Check segments table has required columns
        cursor = conn.execute("PRAGMA table_info(segments)")
        segments_columns = [row[1] for row in cursor.fetchall()]
        
        required_segments_columns = ['id', 'file_id', 'segment_index', 'segment_hash', 'segment_size', 'data_offset', 'state']
        for col in required_segments_columns:
            if col not in segments_columns:
                missing_columns.append(f"segments.{col}")
        
        if missing_columns:
            print(f"ERROR: Missing columns: {missing_columns}")
            conn.close()
            return False
        
        conn.close()
        print("OK: All required tables and columns exist")
        return True
        
    except Exception as e:
        print(f"ERROR: Could not verify schema: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database does not exist")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        # Test folder creation
        cursor = conn.execute("""
            INSERT OR IGNORE INTO folders (folder_path, folder_hash, version, state)
            VALUES (?, ?, ?, ?)
        """, ("test_folder", "test_hash", 1, "active"))
        
        folder_id = cursor.lastrowid or 1
        
        # Test file creation
        cursor = conn.execute("""
            INSERT OR IGNORE INTO files (folder_id, file_path, file_hash, file_size, version, state)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (folder_id, "test_file.txt", "file_hash", 1024, 1, "indexed"))
        
        file_id = cursor.lastrowid or 1
        
        # Test segment creation
        conn.execute("""
            INSERT OR IGNORE INTO segments (file_id, segment_index, segment_hash, segment_size, data_offset, state)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_id, 0, "segment_hash", 512, 0, "pending"))
        
        # Test queries
        cursor = conn.execute("SELECT COUNT(*) FROM folders WHERE state = 'active'")
        folder_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM files WHERE state = 'indexed'")
        file_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM segments WHERE state = 'pending'")
        segment_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"OK: Database operations working (folders: {folder_count}, files: {file_count}, segments: {segment_count})")
        return True
        
    except Exception as e:
        print(f"ERROR: Database operations test failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("Ensure Database Schema is Complete")
    print("=" * 50)
    
    success = True
    
    # Create complete schema
    if not create_complete_schema():
        print("ERROR: Could not create database schema")
        success = False
    
    # Verify schema
    if not verify_schema():
        print("ERROR: Schema verification failed")
        success = False
    
    # Test operations
    if not test_database_operations():
        print("ERROR: Database operations test failed")
        success = False
    
    print()
    if success:
        print("SUCCESS: Database schema is complete and working!")
        print()
        print("Database is ready for:")
        print("  ✓ Folder indexing")
        print("  ✓ File tracking")
        print("  ✓ Segment management")
        print("  ✓ Upload sessions")
        print("  ✓ Publishing system")
        print()
        print("You can now run your indexing operation.")
        return 0
    else:
        print("ERROR: Database schema issues found")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)