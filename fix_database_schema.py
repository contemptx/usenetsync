#!/usr/bin/env python3
"""
Fix database schema issues
"""

import sqlite3
import os
import sys

sys.path.insert(0, '/workspace/src')

from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType

# Create a test database and fix schema
db_path = '/tmp/test_usenetsync.db'

# Remove if exists
if os.path.exists(db_path):
    os.remove(db_path)

# Create database with correct schema
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create all required tables with correct columns
sql_commands = [
    '''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        created_at REAL NOT NULL,
        public_key TEXT,
        encrypted_private_key TEXT,
        api_key TEXT
    )''',
    
    '''CREATE TABLE IF NOT EXISTS folders (
        folder_id TEXT PRIMARY KEY,
        folder_name TEXT NOT NULL,
        folder_path TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        updated_at REAL,
        access_type TEXT DEFAULT 'private',
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
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS segments (
        segment_id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        segment_index INTEGER NOT NULL,
        segment_hash TEXT NOT NULL,
        size INTEGER NOT NULL,
        created_at REAL NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(file_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS shares (
        share_id TEXT PRIMARY KEY,
        folder_id TEXT NOT NULL,
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
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS folder_authorizations (
        folder_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        authorized_at REAL NOT NULL,
        PRIMARY KEY (folder_id, user_id),
        FOREIGN KEY (folder_id) REFERENCES folders(folder_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )'''
]

for sql in sql_commands:
    cursor.execute(sql)

conn.commit()
conn.close()

print("✅ Created database with correct schema")
print(f"✅ Database at: {db_path}")
print("✅ All required tables created:")
print("   - users")
print("   - folders (with folder_name column)")
print("   - files")
print("   - segments")
print("   - shares")
print("   - publications")
print("   - folder_authorizations")