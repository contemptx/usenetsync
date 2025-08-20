#!/usr/bin/env python3
"""
Fix ALL schema mismatches between code and database
"""

import os
import sys
import sqlite3

sys.path.insert(0, '/workspace/src')

def fix_schema():
    """Fix all schema issues"""
    print("FIXING ALL SCHEMA ISSUES...")
    print("=" * 80)
    
    # Remove old database
    db_path = '/tmp/test_usenetsync.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed old database")
    
    # Create new database with CORRECT schema matching the code
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables that match what the code expects
    tables = [
        # Users table - matches authentication.py
        '''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            created_at REAL NOT NULL,
            public_key TEXT,
            encrypted_private_key TEXT,
            api_key TEXT,
            display_name TEXT
        )''',
        
        # Folders table - matches what Folder model expects
        '''CREATE TABLE IF NOT EXISTS folders (
            folder_id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            name TEXT NOT NULL,
            owner_id TEXT,
            private_key TEXT,
            public_key TEXT,
            total_size INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            segment_count INTEGER DEFAULT 0,
            version INTEGER DEFAULT 1,
            last_indexed REAL,
            last_modified REAL,
            encryption_enabled INTEGER DEFAULT 1,
            compression_enabled INTEGER DEFAULT 1,
            redundancy_level INTEGER DEFAULT 3,
            status TEXT DEFAULT 'active',
            metadata TEXT,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            updated_at REAL,
            access_type TEXT DEFAULT 'private',
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''',
        
        # Files table - matches what File model expects
        '''CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            path TEXT NOT NULL,
            name TEXT NOT NULL,
            size INTEGER NOT NULL,
            hash TEXT,
            mime_type TEXT,
            version INTEGER DEFAULT 1,
            previous_version TEXT,
            status TEXT DEFAULT 'pending',
            change_type TEXT,
            total_segments INTEGER DEFAULT 0,
            uploaded_segments INTEGER DEFAULT 0,
            segment_size INTEGER DEFAULT 768000,
            compression_ratio REAL DEFAULT 1.0,
            encryption_key TEXT,
            internal_subject TEXT,
            error_message TEXT,
            metadata TEXT,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            modified_at REAL,
            indexed_at REAL,
            uploaded_at REAL,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
        )''',
        
        # Segments table - matches what Segment model expects
        '''CREATE TABLE IF NOT EXISTS segments (
            segment_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            segment_index INTEGER NOT NULL,
            redundancy_index INTEGER DEFAULT 0,
            size INTEGER NOT NULL,
            compressed_size INTEGER,
            hash TEXT NOT NULL,
            offset_start INTEGER,
            offset_end INTEGER,
            message_id TEXT,
            internal_subject TEXT,
            subject TEXT,
            newsgroup TEXT,
            server TEXT,
            packed_segment_id TEXT,
            packing_index INTEGER,
            encryption_iv TEXT,
            upload_status TEXT DEFAULT 'pending',
            upload_attempts INTEGER DEFAULT 0,
            error_message TEXT,
            metadata TEXT,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            uploaded_at REAL,
            data BLOB,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        )''',
        
        # Shares table - for create_share methods
        '''CREATE TABLE IF NOT EXISTS shares (
            share_id TEXT PRIMARY KEY,
            folder_id TEXT,
            owner_id TEXT NOT NULL,
            share_type TEXT NOT NULL,
            password_hash TEXT,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            expires_at REAL,
            access_count INTEGER DEFAULT 0,
            name TEXT,
            size INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            folder_count INTEGER DEFAULT 0,
            allowed_users TEXT,
            download_count INTEGER DEFAULT 0,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''',
        
        # Publications table - for publish_folder
        '''CREATE TABLE IF NOT EXISTS publications (
            publication_id TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            access_level TEXT NOT NULL,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            expires_at REAL,
            message_ids TEXT,
            total_segments INTEGER DEFAULT 0,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''',
        
        # Folder authorizations
        '''CREATE TABLE IF NOT EXISTS folder_authorizations (
            folder_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            authorized_at REAL DEFAULT (strftime('%s', 'now')),
            permissions TEXT DEFAULT 'read',
            PRIMARY KEY (folder_id, user_id),
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''',
        
        # Uploads table
        '''CREATE TABLE IF NOT EXISTS uploads (
            upload_id TEXT PRIMARY KEY,
            folder_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at REAL DEFAULT (strftime('%s', 'now')),
            started_at REAL,
            completed_at REAL,
            progress REAL DEFAULT 0,
            total_segments INTEGER DEFAULT 0,
            uploaded_segments INTEGER DEFAULT 0,
            FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
        )''',
        
        # Downloads table
        '''CREATE TABLE IF NOT EXISTS downloads (
            download_id TEXT PRIMARY KEY,
            share_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at REAL DEFAULT (strftime('%s', 'now')),
            started_at REAL,
            completed_at REAL,
            progress REAL DEFAULT 0,
            destination TEXT,
            FOREIGN KEY (share_id) REFERENCES shares(share_id)
        )''',
        
        # Additional tables the schema.py creates
        '''CREATE TABLE IF NOT EXISTS entities (
            entity_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            parent_id TEXT,
            name TEXT NOT NULL,
            metadata TEXT,
            created_at REAL DEFAULT (strftime('%s', 'now')),
            updated_at REAL
        )''',
        
        '''CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            segment_id TEXT,
            newsgroup TEXT,
            subject TEXT,
            posted_at REAL,
            size INTEGER,
            FOREIGN KEY (segment_id) REFERENCES segments(segment_id)
        )''',
        
        '''CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY,
            operation_type TEXT,
            entity_id TEXT,
            status TEXT,
            started_at REAL,
            completed_at REAL,
            progress REAL,
            error TEXT
        )'''
    ]
    
    # Create all tables
    for sql in tables:
        try:
            cursor.execute(sql)
            # Extract table name for logging
            table_name = sql.split('CREATE TABLE IF NOT EXISTS ')[1].split(' ')[0]
            print(f"✅ Created table: {table_name}")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
    
    # Create indexes for performance
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_folders_owner ON folders(owner_id)',
        'CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path)',
        'CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id)',
        'CREATE INDEX IF NOT EXISTS idx_segments_file ON segments(file_id)',
        'CREATE INDEX IF NOT EXISTS idx_shares_owner ON shares(owner_id)',
        'CREATE INDEX IF NOT EXISTS idx_publications_folder ON publications(folder_id)',
    ]
    
    for sql in indexes:
        try:
            cursor.execute(sql)
        except:
            pass  # Ignore index errors
    
    conn.commit()
    
    # Verify the schema
    print("\nVERIFYING SCHEMA...")
    print("-" * 40)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"✅ Created {len(tables)} tables")
    
    # Check critical columns
    cursor.execute("PRAGMA table_info(folders)")
    folder_cols = [col[1] for col in cursor.fetchall()]
    print(f"✅ Folders columns: {', '.join(folder_cols[:5])}...")
    
    if 'path' in folder_cols and 'name' in folder_cols:
        print("✅ Folders table has correct columns (path, name)")
    else:
        print("❌ Folders table missing required columns!")
    
    cursor.execute("PRAGMA table_info(files)")
    file_cols = [col[1] for col in cursor.fetchall()]
    if 'path' in file_cols and 'name' in file_cols:
        print("✅ Files table has correct columns (path, name)")
    else:
        print("❌ Files table missing required columns!")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ SCHEMA FIXED AND READY FOR USE!")
    print("=" * 80)
    
    return db_path

if __name__ == '__main__':
    fix_schema()