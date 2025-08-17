#!/usr/bin/env python3
"""
Fix database schema - add missing columns
"""

import sqlite3
import sys
from pathlib import Path

def fix_schema(db_path):
    """Add missing columns to database"""
    print(f"Fixing schema for: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if folders table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        if not cursor.fetchone():
            print("Creating folders table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id TEXT UNIQUE NOT NULL,
                    path TEXT,
                    private_key BLOB,
                    public_key BLOB,
                    keys_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Add keys_updated_at column if it doesn't exist
            cursor.execute("PRAGMA table_info(folders)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'keys_updated_at' not in columns:
                print("Adding keys_updated_at column to folders table...")
                cursor.execute("""
                    ALTER TABLE folders 
                    ADD COLUMN keys_updated_at TIMESTAMP
                """)
                # Update existing rows with current timestamp
                cursor.execute("""
                    UPDATE folders 
                    SET keys_updated_at = datetime('now')
                    WHERE keys_updated_at IS NULL
                """)
                print("✅ Added keys_updated_at column")
            else:
                print("✅ keys_updated_at column already exists")
        
        # Check segments table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='segments'")
        if not cursor.fetchone():
            print("Creating segments table...")
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
            print("✅ Created segments table")
        
        # Ensure files table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        if not cursor.fetchone():
            print("Creating files table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER,
                    filename TEXT,
                    size INTEGER,
                    hash TEXT,
                    segment_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id)
                )
            """)
            print("✅ Created files table")
        
        conn.commit()
        print("✅ Schema fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    # Fix test database
    test_db = Path("test_workspace/test.db")
    if test_db.exists():
        fix_schema(test_db)
    
    # Fix main database if it exists
    main_db = Path("usenetsync.db")
    if main_db.exists():
        fix_schema(main_db)
    
    print("\n✅ All database schemas updated!")