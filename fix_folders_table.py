#!/usr/bin/env python3
"""
Fix the folders table issue by ensuring all tables are created
"""

import psycopg2
import sys
import os

def create_all_tables():
    """Create all required tables for folder management"""
    
    # Database connection
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="usenet",
            user="usenet",
            password="usenetsync"
        )
        cursor = conn.cursor()
        print("Connected to PostgreSQL")
        
        # Create folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                folder_id VARCHAR(255) PRIMARY KEY,
                path TEXT NOT NULL,
                name VARCHAR(255) NOT NULL,
                state VARCHAR(50) DEFAULT 'added',
                published BOOLEAN DEFAULT FALSE,
                share_id VARCHAR(255),
                access_type VARCHAR(50) DEFAULT 'public',
                total_files INTEGER DEFAULT 0,
                total_size BIGINT DEFAULT 0,
                total_segments INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created folders table")
        
        # Create files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id VARCHAR(255) PRIMARY KEY,
                folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size BIGINT,
                mime_type VARCHAR(255),
                hash VARCHAR(255),
                encrypted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created files table")
        
        # Create segments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                segment_id VARCHAR(255) PRIMARY KEY,
                file_id VARCHAR(255) REFERENCES files(file_id) ON DELETE CASCADE,
                segment_index INTEGER NOT NULL,
                size BIGINT,
                hash VARCHAR(255),
                message_id TEXT,
                uploaded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created segments table")
        
        # Create other required tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shares (
                share_id VARCHAR(255) PRIMARY KEY,
                folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                share_type VARCHAR(50) DEFAULT 'public',
                password_hash TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        print("✓ Created shares table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorized_users (
                id SERIAL PRIMARY KEY,
                folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                user_id VARCHAR(255) NOT NULL,
                permissions VARCHAR(50) DEFAULT 'read',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(folder_id, user_id)
            )
        """)
        print("✓ Created authorized_users table")
        
        # Commit all changes
        conn.commit()
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ All tables created successfully!")
        print("\nYou can now use the Folder Management feature.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing Folder Management Tables")
    print("=" * 60)
    print()
    
    create_all_tables()