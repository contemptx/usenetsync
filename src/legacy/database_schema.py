#!/usr/bin/env python3
"""
Unified Database Schema for UsenetSync
Consolidates all database tables into a single, optimized schema
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
import json

logger = logging.getLogger(__name__)

class UnifiedDatabaseSchema:
    """Manages the unified database schema for both SQLite and PostgreSQL"""
    
    # Unified schema definitions
    TABLES = {
        # Core file indexing table
        'files': """
            CREATE TABLE IF NOT EXISTS files (
                file_id SERIAL PRIMARY KEY,
                folder_id VARCHAR(64) NOT NULL,
                file_path TEXT NOT NULL,
                file_hash VARCHAR(64) NOT NULL,
                file_size BIGINT NOT NULL,
                modified_time TIMESTAMP NOT NULL,
                version INTEGER DEFAULT 1,
                segment_count INTEGER NOT NULL,
                state VARCHAR(20) DEFAULT 'indexed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                UNIQUE(folder_id, file_path, version)
            )
        """,
        
        # Segment information table
        'segments': """
            CREATE TABLE IF NOT EXISTS segments (
                segment_id SERIAL PRIMARY KEY,
                file_id INTEGER NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
                segment_index INTEGER NOT NULL,
                segment_hash VARCHAR(64) NOT NULL,
                segment_size INTEGER NOT NULL,
                packed_with TEXT[],  -- Array of other segment IDs packed together
                redundancy_level INTEGER DEFAULT 0,
                encrypted_location TEXT,  -- Encrypted Usenet location
                message_id VARCHAR(255),  -- Obfuscated message ID
                internal_subject VARCHAR(64),  -- For verification
                usenet_subject VARCHAR(40),  -- Obfuscated subject
                upload_status VARCHAR(20) DEFAULT 'pending',
                uploaded_at TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_id, segment_index, redundancy_level)
            )
        """,
        
        # Folder management table
        'folders': """
            CREATE TABLE IF NOT EXISTS folders (
                folder_id VARCHAR(64) PRIMARY KEY,
                folder_path TEXT NOT NULL,
                folder_name VARCHAR(255) NOT NULL,
                owner_id VARCHAR(64) NOT NULL,
                public_key TEXT NOT NULL,
                private_key_encrypted TEXT NOT NULL,
                total_size BIGINT DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                segment_count INTEGER DEFAULT 0,
                index_version INTEGER DEFAULT 1,
                last_indexed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """,
        
        # Share publishing table
        'shares': """
            CREATE TABLE IF NOT EXISTS shares (
                share_id VARCHAR(32) PRIMARY KEY,
                folder_id VARCHAR(64) NOT NULL REFERENCES folders(folder_id) ON DELETE CASCADE,
                share_type VARCHAR(20) NOT NULL,  -- PUBLIC, PRIVATE, PROTECTED
                access_string TEXT NOT NULL,
                encrypted_index TEXT NOT NULL,
                index_size INTEGER NOT NULL,
                index_segments INTEGER NOT NULL,
                authorized_users TEXT[],  -- For PRIVATE shares
                access_commitments JSONB,  -- Zero-knowledge proofs
                password_salt VARCHAR(64),  -- For PROTECTED shares
                password_iterations INTEGER,  -- For PROTECTED shares
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT TRUE,
                metadata JSONB
            )
        """,
        
        # User management table
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(64) PRIMARY KEY,
                username VARCHAR(100),
                public_key TEXT NOT NULL,
                private_key_encrypted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                metadata JSONB
            )
        """,
        
        # Upload queue table
        'upload_queue': """
            CREATE TABLE IF NOT EXISTS upload_queue (
                queue_id SERIAL PRIMARY KEY,
                segment_id INTEGER REFERENCES segments(segment_id) ON DELETE CASCADE,
                priority INTEGER DEFAULT 5,
                attempt_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                next_retry TIMESTAMP,
                error_message TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        # Download tracking table
        'downloads': """
            CREATE TABLE IF NOT EXISTS downloads (
                download_id SERIAL PRIMARY KEY,
                share_id VARCHAR(32) NOT NULL,
                user_id VARCHAR(64),
                destination_path TEXT NOT NULL,
                total_files INTEGER NOT NULL,
                completed_files INTEGER DEFAULT 0,
                total_segments INTEGER NOT NULL,
                completed_segments INTEGER DEFAULT 0,
                total_size BIGINT NOT NULL,
                downloaded_size BIGINT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                metadata JSONB
            )
        """,
        
        # Server health tracking
        'server_health': """
            CREATE TABLE IF NOT EXISTS server_health (
                server_id SERIAL PRIMARY KEY,
                hostname VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_response_time FLOAT DEFAULT 0,
                last_success TIMESTAMP,
                last_failure TIMESTAMP,
                health_score FLOAT DEFAULT 100.0,
                enabled BOOLEAN DEFAULT TRUE,
                UNIQUE(hostname, port)
            )
        """,
        
        # System configuration
        'configuration': """
            CREATE TABLE IF NOT EXISTS configuration (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT NOT NULL,
                category VARCHAR(50),
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        # User commitments table
        'user_commitments': """
            CREATE TABLE IF NOT EXISTS user_commitments (
                commitment_id SERIAL PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL,
                folder_id VARCHAR(100) NOT NULL,
                commitment_type VARCHAR(50) NOT NULL,
                data_size BIGINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                metadata JSONB,
                UNIQUE(user_id, folder_id, commitment_type)
            )
        """,
        
        # Publications table for file sharing
        'publications': """
            CREATE TABLE IF NOT EXISTS publications (
                publication_id VARCHAR(64) PRIMARY KEY,
                file_hash VARCHAR(64) NOT NULL,
                access_level VARCHAR(20) NOT NULL DEFAULT 'public',
                password_hash VARCHAR(64),
                published_by VARCHAR(64),
                published_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_time TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                metadata JSONB,
                FOREIGN KEY (file_hash) REFERENCES files(file_hash) ON DELETE CASCADE
            )
        """
    }
    
    # Indexes for performance
    INDEXES = {
        'idx_files_folder': 'CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id)',
        'idx_files_hash': 'CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)',
        'idx_files_state': 'CREATE INDEX IF NOT EXISTS idx_files_state ON files(state)',
        'idx_segments_file': 'CREATE INDEX IF NOT EXISTS idx_segments_file ON segments(file_id)',
        'idx_segments_status': 'CREATE INDEX IF NOT EXISTS idx_segments_status ON segments(upload_status)',
        'idx_segments_message': 'CREATE INDEX IF NOT EXISTS idx_segments_message ON segments(message_id)',
        'idx_shares_folder': 'CREATE INDEX IF NOT EXISTS idx_shares_folder ON shares(folder_id)',
        'idx_shares_active': 'CREATE INDEX IF NOT EXISTS idx_shares_active ON shares(active)',
        'idx_upload_queue_status': 'CREATE INDEX IF NOT EXISTS idx_upload_queue_status ON upload_queue(status)',
        'idx_downloads_share': 'CREATE INDEX IF NOT EXISTS idx_downloads_share ON downloads(share_id)',
        'idx_downloads_status': 'CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)'
    }
    
    def __init__(self, db_type: str = 'sqlite', **kwargs):
        """
        Initialize unified database schema
        
        Args:
            db_type: 'sqlite' or 'postgresql'
            **kwargs: Database connection parameters
        """
        self.db_type = db_type.lower()
        self.connection_params = kwargs
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            if self.db_type == 'postgresql':
                self.connection = psycopg2.connect(
                    host=self.connection_params.get('host', 'localhost'),
                    port=self.connection_params.get('port', 5432),
                    database=self.connection_params.get('database', 'usenetsync'),
                    user=self.connection_params.get('user', 'usenetsync'),
                    password=self.connection_params.get('password', 'usenetsync123'),
                    cursor_factory=RealDictCursor
                )
                self.connection.autocommit = False
                logger.info("Connected to PostgreSQL database")
                
            else:  # SQLite
                db_path = self.connection_params.get('path', 'usenetsync.db')
                self.connection = sqlite3.connect(
                    db_path,
                    check_same_thread=False,
                    isolation_level=None  # Autocommit mode
                )
                self.connection.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                self.connection.execute("PRAGMA journal_mode=WAL")
                self.connection.execute("PRAGMA synchronous=NORMAL")
                self.connection.execute("PRAGMA cache_size=10000")
                self.connection.execute("PRAGMA temp_store=MEMORY")
                
                logger.info(f"Connected to SQLite database: {db_path}")
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def create_schema(self):
        """Create all tables and indexes"""
        if not self.connection:
            self.connect()
            
        cursor = self.connection.cursor()
        
        try:
            # Create tables
            for table_name, table_sql in self.TABLES.items():
                # Adjust SQL for SQLite compatibility
                if self.db_type == 'sqlite':
                    table_sql = self._convert_to_sqlite(table_sql)
                    
                cursor.execute(table_sql)
                logger.info(f"Created/verified table: {table_name}")
                
            # Create indexes
            for index_name, index_sql in self.INDEXES.items():
                cursor.execute(index_sql)
                logger.info(f"Created/verified index: {index_name}")
                
            if self.db_type == 'postgresql':
                self.connection.commit()
                
            logger.info("Database schema created successfully")
            
        except Exception as e:
            if self.db_type == 'postgresql':
                self.connection.rollback()
            logger.error(f"Failed to create schema: {e}")
            raise
            
    def _convert_to_sqlite(self, sql: str) -> str:
        """Convert PostgreSQL SQL to SQLite compatible SQL"""
        # Replace SERIAL with INTEGER PRIMARY KEY AUTOINCREMENT
        sql = sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        sql = sql.replace('SERIAL', 'INTEGER')
        
        # Replace JSONB with TEXT (will store JSON strings)
        sql = sql.replace('JSONB', 'TEXT')
        
        # Replace TEXT[] with TEXT (will store JSON arrays)
        sql = sql.replace('TEXT[]', 'TEXT')
        
        # Replace TIMESTAMP with DATETIME
        sql = sql.replace('TIMESTAMP', 'DATETIME')
        
        # Replace CURRENT_TIMESTAMP with datetime('now')
        sql = sql.replace('CURRENT_TIMESTAMP', "datetime('now')")
        
        # Remove ON DELETE CASCADE (SQLite needs foreign keys enabled)
        sql = sql.replace('ON DELETE CASCADE', '')
        
        # Replace BOOLEAN with INTEGER
        sql = sql.replace('BOOLEAN', 'INTEGER')
        
        return sql
        
    def migrate_from_existing(self, old_db_path: str):
        """Migrate data from existing database to unified schema"""
        logger.info(f"Starting migration from {old_db_path}")
        
        # This would contain migration logic from old schema to new
        # For now, we'll just log the intent
        logger.info("Migration logic would be implemented here")
        
    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connect()
        return self.connection
        
    def close(self):
        """Close database connection"""
        if self.connection:
            if self.db_type == 'postgresql':
                self.connection.close()
            else:
                self.connection.close()
            self.connection = None
            logger.info("Database connection closed")


def test_schema_creation():
    """Test schema creation with both SQLite and PostgreSQL"""
    print("\n=== Testing Unified Database Schema ===\n")
    
    # Test SQLite
    print("Testing SQLite schema...")
    sqlite_schema = UnifiedDatabaseSchema('sqlite', path='test_unified.db')
    sqlite_schema.create_schema()
    
    # Verify tables exist
    cursor = sqlite_schema.get_connection().cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"SQLite tables created: {tables}")
    sqlite_schema.close()
    
    # Test PostgreSQL
    print("\nTesting PostgreSQL schema...")
    pg_schema = UnifiedDatabaseSchema(
        'postgresql',
        host='localhost',
        database='usenetsync',
        user='usenetsync',
        password='usenetsync123'
    )
    pg_schema.create_schema()
    
    # Verify tables exist
    cursor = pg_schema.get_connection().cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row['table_name'] for row in cursor.fetchall()]
    print(f"PostgreSQL tables created: {tables}")
    pg_schema.close()
    
    print("\n✓ Schema creation test completed successfully")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_schema_creation()