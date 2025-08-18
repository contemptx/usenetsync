#!/usr/bin/env python3
"""
Initialize PostgreSQL database schema for UsenetSync
Creates all required tables for the application
"""

import psycopg2
from psycopg2 import sql
import sys
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'usenet',
    'user': 'usenet',
    'password': 'usenetsync'
}

def create_schema():
    """Create all required database tables"""
    
    conn = None
    cursor = None
    
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating database schema...")
        
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
        
        # Create shares table
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
        
        # Create authorized_users table for private shares
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
        
        # Create uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                upload_id VARCHAR(255) PRIMARY KEY,
                folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                status VARCHAR(50) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                total_segments INTEGER,
                uploaded_segments INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        print("✓ Created uploads table")
        
        # Create activity_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                folder_id VARCHAR(255),
                action VARCHAR(100),
                details JSONB,
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created activity_log table")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments(file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_folder_id ON shares(folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authorized_users_folder_id ON authorized_users(folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploads_folder_id ON uploads(folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_log_folder_id ON activity_log(folder_id)")
        print("✓ Created indexes")
        
        # Commit the changes
        conn.commit()
        print("\n✅ Database schema created successfully!")
        
        # Show table count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        print(f"Total tables created: {table_count}")
        
        # List all tables
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
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]} ({count} rows)")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return True

def test_connection():
    """Test the database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"Connected to: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Schema Initialization for UsenetSync")
    print("=" * 60)
    print()
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print()
    
    # Test connection first
    print("Testing database connection...")
    if not test_connection():
        print("\n⚠️  Cannot connect to PostgreSQL!")
        print("Make sure PostgreSQL is running and the database exists.")
        print("\nTo start PostgreSQL:")
        print("  cd C:\\Users\\socon\\AppData\\Local\\UsenetSync\\postgresql\\bin")
        print("  .\\pg_ctl start -D \"C:\\Users\\socon\\AppData\\Local\\UsenetSync\\pgdata\"")
        sys.exit(1)
    
    print()
    
    # Create schema
    if create_schema():
        print("\n✅ Schema initialization complete!")
        print("\nYou can now use the Folder Management feature.")
    else:
        print("\n❌ Schema initialization failed!")
        print("Please check the error messages above.")
        sys.exit(1)