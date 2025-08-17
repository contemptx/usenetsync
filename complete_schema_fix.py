#!/usr/bin/env python3
"""
Complete database schema for UsenetSync
"""

import sqlite3
from pathlib import Path

def create_complete_schema(db_path):
    """Create all required tables with all columns"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables to start fresh
    tables = ['user_config', 'folders', 'files', 'segments', 'shares', 
              'upload_sessions', 'download_sessions', 'metrics', 'folder_versions']
    
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # User config table
    cursor.execute("""
        CREATE TABLE user_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            display_name TEXT,
            private_key BLOB,
            public_key BLOB,
            config TEXT,
            preferences TEXT,
            last_active TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Folders table - comprehensive
    cursor.execute("""
        CREATE TABLE folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id TEXT,
            folder_unique_id TEXT UNIQUE NOT NULL,
            path TEXT,
            folder_path TEXT,
            display_name TEXT,
            share_type TEXT,
            state TEXT,
            total_files INTEGER DEFAULT 0,
            total_size INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            private_key BLOB,
            public_key BLOB,
            keys_updated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Files table - comprehensive
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER,
            filename TEXT,
            file_path TEXT,
            size INTEGER,
            file_size INTEGER,
            hash TEXT,
            file_hash TEXT,
            segment_count INTEGER,
            version INTEGER DEFAULT 1,
            state TEXT DEFAULT 'pending',
            modified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Segments table
    cursor.execute("""
        CREATE TABLE segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            segment_index INTEGER,
            message_id TEXT,
            size INTEGER,
            hash TEXT,
            internal_subject TEXT,
            offset INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    """)
    
    # Shares table
    cursor.execute("""
        CREATE TABLE shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            share_id TEXT UNIQUE NOT NULL,
            folder_id INTEGER,
            access_type TEXT,
            access_string TEXT,
            encryption_key BLOB,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Upload sessions table
    cursor.execute("""
        CREATE TABLE upload_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            folder_id INTEGER,
            status TEXT,
            progress REAL,
            total_segments INTEGER,
            uploaded_segments INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Download sessions table
    cursor.execute("""
        CREATE TABLE download_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            share_id TEXT,
            status TEXT,
            progress REAL,
            total_segments INTEGER,
            downloaded_segments INTEGER,
            output_path TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Metrics table
    cursor.execute("""
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT,
            metric_name TEXT,
            value REAL,
            metadata TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Folder versions table - comprehensive
    cursor.execute("""
        CREATE TABLE folder_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER,
            version INTEGER,
            change_summary TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Create all indexes
    cursor.execute("CREATE INDEX idx_folders_folder_id ON folders(folder_id)")
    cursor.execute("CREATE INDEX idx_folders_unique ON folders(folder_unique_id)")
    cursor.execute("CREATE INDEX idx_files_folder_id ON files(folder_id)")
    cursor.execute("CREATE INDEX idx_segments_file_id ON segments(file_id)")
    cursor.execute("CREATE INDEX idx_shares_share_id ON shares(share_id)")
    cursor.execute("CREATE INDEX idx_upload_sessions ON upload_sessions(session_id)")
    cursor.execute("CREATE INDEX idx_download_sessions ON download_sessions(session_id)")
    cursor.execute("CREATE INDEX idx_folder_versions ON folder_versions(folder_id, version)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created complete schema for {db_path}")

if __name__ == "__main__":
    # Create test database
    test_dir = Path("test_workspace")
    test_dir.mkdir(exist_ok=True)
    
    test_db = test_dir / "test.db"
    create_complete_schema(test_db)
    
    print("\n🎉 Database ready with complete schema!")