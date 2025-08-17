#!/usr/bin/env python3
"""
Create complete database schema for testing
"""

import sqlite3
from pathlib import Path

def create_complete_schema(db_path):
    """Create all required tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # User config table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_config (
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
    
    # Folders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
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
    
    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER,
            filename TEXT,
            file_path TEXT,
            size INTEGER,
            file_size INTEGER,
            hash TEXT,
            file_hash TEXT,
            segment_count INTEGER,
            modified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Segments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS segments (
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
        CREATE TABLE IF NOT EXISTS shares (
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
        CREATE TABLE IF NOT EXISTS upload_sessions (
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
        CREATE TABLE IF NOT EXISTS download_sessions (
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
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT,
            metric_name TEXT,
            value REAL,
            metadata TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Folder versions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folder_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id INTEGER,
            version INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_folder_id ON folders(folder_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments(file_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_share_id ON shares(share_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_upload_sessions_session_id ON upload_sessions(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_download_sessions_session_id ON download_sessions(session_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created complete schema for {db_path}")

if __name__ == "__main__":
    # Create test database
    test_dir = Path("test_workspace")
    test_dir.mkdir(exist_ok=True)
    
    test_db = test_dir / "test.db"
    if test_db.exists():
        test_db.unlink()
    
    create_complete_schema(test_db)
    print("\n✅ Database ready for testing!")