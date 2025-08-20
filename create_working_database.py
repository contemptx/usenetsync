#!/usr/bin/env python3
"""
Create a working database with all required tables
"""

import sqlite3
import os

db_path = '/tmp/test_usenetsync.db'

# Remove old database
if os.path.exists(db_path):
    os.remove(db_path)

# Create new database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create all tables with correct schema
tables = [
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
    
    '''CREATE TABLE IF NOT EXISTS folders (
        folder_id TEXT PRIMARY KEY,
        folder_name TEXT NOT NULL,
        folder_path TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        updated_at REAL,
        access_type TEXT DEFAULT 'private',
        total_size INTEGER DEFAULT 0,
        file_count INTEGER DEFAULT 0,
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS files (
        file_id TEXT PRIMARY KEY,
        folder_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        size INTEGER NOT NULL,
        hash TEXT,
        created_at REAL NOT NULL,
        updated_at REAL,
        segment_count INTEGER DEFAULT 0,
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS segments (
        segment_id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        segment_index INTEGER NOT NULL,
        segment_hash TEXT NOT NULL,
        size INTEGER NOT NULL,
        created_at REAL NOT NULL,
        compressed_size INTEGER,
        message_id TEXT,
        FOREIGN KEY (file_id) REFERENCES files(file_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS shares (
        share_id TEXT PRIMARY KEY,
        folder_id TEXT,
        owner_id TEXT NOT NULL,
        share_type TEXT NOT NULL,
        password_hash TEXT,
        created_at REAL NOT NULL,
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
    
    '''CREATE TABLE IF NOT EXISTS publications (
        publication_id TEXT PRIMARY KEY,
        folder_id TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        access_level TEXT NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL,
        message_ids TEXT,
        total_segments INTEGER DEFAULT 0,
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS folder_authorizations (
        folder_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        authorized_at REAL NOT NULL,
        permissions TEXT DEFAULT 'read',
        PRIMARY KEY (folder_id, user_id),
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS uploads (
        upload_id TEXT PRIMARY KEY,
        folder_id TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at REAL NOT NULL,
        started_at REAL,
        completed_at REAL,
        progress REAL DEFAULT 0,
        total_segments INTEGER DEFAULT 0,
        uploaded_segments INTEGER DEFAULT 0,
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS downloads (
        download_id TEXT PRIMARY KEY,
        share_id TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at REAL NOT NULL,
        started_at REAL,
        completed_at REAL,
        progress REAL DEFAULT 0,
        destination TEXT,
        FOREIGN KEY (share_id) REFERENCES shares(share_id)
    )'''
]

# Create all tables
for sql in tables:
    cursor.execute(sql)
    
# Create indexes for performance
indexes = [
    'CREATE INDEX IF NOT EXISTS idx_folders_owner ON folders(owner_id)',
    'CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id)',
    'CREATE INDEX IF NOT EXISTS idx_segments_file ON segments(file_id)',
    'CREATE INDEX IF NOT EXISTS idx_shares_owner ON shares(owner_id)',
    'CREATE INDEX IF NOT EXISTS idx_publications_folder ON publications(folder_id)',
]

for sql in indexes:
    cursor.execute(sql)

conn.commit()

# Verify tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("✅ Database created successfully!")
print(f"✅ Location: {db_path}")
print(f"✅ Created {len(tables)} tables:")
for table in tables:
    print(f"   - {table[0]}")
    
# Check folders table columns specifically
cursor.execute("PRAGMA table_info(folders)")
columns = cursor.fetchall()
print("\n✅ Folders table has all required columns:")
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

conn.close()

print("\n✅ Database is ready for testing!")