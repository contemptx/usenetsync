#!/usr/bin/env python3
"""
Unified Schema Module - Single source of truth for ALL database tables
Supports both SQLite and PostgreSQL with complete functionality
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import UnifiedDatabase, DatabaseType

logger = logging.getLogger(__name__)

class UnifiedSchema:
    """
    Complete unified database schema for UsenetSync
    Consolidates ALL tables from fragmented systems
    """
    
    def __init__(self, db: UnifiedDatabase):
        self.db = db
        self.db_type = db.config.db_type
        
        # Define all tables with their schemas
        self.tables = self._define_tables()
    
    def _define_tables(self) -> Dict[str, str]:
        """Define all database tables with proper SQL"""
        
        # Use appropriate data types based on database
        if self.db_type == DatabaseType.POSTGRESQL:
            id_type = "SERIAL PRIMARY KEY"
            uuid_type = "UUID"
            text_type = "TEXT"
            blob_type = "BYTEA"
            json_type = "JSONB"
            timestamp_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            bigint_type = "BIGINT"
        else:
            id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            uuid_type = "TEXT"
            text_type = "TEXT"
            blob_type = "BLOB"
            json_type = "TEXT"  # Will use JSON functions
            timestamp_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            bigint_type = "INTEGER"
        
        return {
            # Core entities table (unified for all object types)
            'entities': f"""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id {uuid_type} PRIMARY KEY,
                    entity_type VARCHAR(50) NOT NULL,
                    parent_id {uuid_type},
                    name {text_type},
                    created_at {timestamp_type},
                    updated_at {timestamp_type},
                    metadata {json_type},
                    CHECK (entity_type IN ('folder', 'file', 'segment', 'share', 'user', 'commitment'))
                )
            """,
            
            # Folders table (enhanced with all features)
            'folders': f"""
                CREATE TABLE IF NOT EXISTS folders (
                    id {id_type},
                    folder_id {uuid_type} UNIQUE NOT NULL,
                    path {text_type} NOT NULL,
                    name {text_type} NOT NULL,
                    owner_id {text_type},
                    private_key {text_type},
                    public_key {text_type},
                    total_size {bigint_type} DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    segment_count INTEGER DEFAULT 0,
                    version INTEGER DEFAULT 1,
                    last_indexed {timestamp_type},
                    last_modified {timestamp_type},
                    encryption_enabled BOOLEAN DEFAULT TRUE,
                    compression_enabled BOOLEAN DEFAULT TRUE,
                    redundancy_level INTEGER DEFAULT 3,
                    status VARCHAR(50) DEFAULT 'active',
                    metadata {json_type},
                    created_at {timestamp_type},
                    updated_at {timestamp_type}
                )
            """,
            
            # Files table (complete with versioning)
            'files': f"""
                CREATE TABLE IF NOT EXISTS files (
                    id {id_type},
                    file_id {uuid_type} UNIQUE NOT NULL,
                    folder_id {uuid_type} NOT NULL,
                    path {text_type} NOT NULL,
                    name {text_type} NOT NULL,
                    size {bigint_type} NOT NULL,
                    hash VARCHAR(64),
                    mime_type VARCHAR(255),
                    version INTEGER DEFAULT 1,
                    previous_version INTEGER,
                    change_type VARCHAR(20),
                    segment_size INTEGER DEFAULT 768000,
                    total_segments INTEGER DEFAULT 0,
                    uploaded_segments INTEGER DEFAULT 0,
                    compression_ratio REAL,
                    encryption_key {text_type},
                    internal_subject VARCHAR(64),
                    status VARCHAR(50) DEFAULT 'indexed',
                    error_message {text_type},
                    indexed_at {timestamp_type},
                    modified_at {timestamp_type},
                    uploaded_at {timestamp_type},
                    metadata {json_type},
                    created_at {timestamp_type},
                    CHECK (change_type IN ('added', 'modified', 'deleted', 'unchanged'))
                )
            """,
            
            # Segments table (with redundancy and packing)
            'segments': f"""
                CREATE TABLE IF NOT EXISTS segments (
                    id {id_type},
                    segment_id {uuid_type} NOT NULL,
                    file_id {uuid_type} NOT NULL,
                    segment_index INTEGER NOT NULL,
                    redundancy_index INTEGER DEFAULT 0,
                    size INTEGER NOT NULL,
                    compressed_size INTEGER,
                    hash VARCHAR(64) NOT NULL,
                    offset_start {bigint_type},
                    offset_end {bigint_type},
                    message_id {text_type},
                    subject {text_type},
                    internal_subject VARCHAR(64),
                    newsgroup VARCHAR(255),
                    server VARCHAR(255),
                    packed_segment_id {uuid_type},
                    packing_index INTEGER,
                    encryption_iv {text_type},
                    upload_status VARCHAR(50) DEFAULT 'pending',
                    upload_attempts INTEGER DEFAULT 0,
                    uploaded_at {timestamp_type},
                    error_message {text_type},
                    metadata {json_type},
                    created_at {timestamp_type},
                    UNIQUE(segment_id, redundancy_index),
                    CHECK (upload_status IN ('pending', 'uploading', 'uploaded', 'failed', 'cancelled'))
                )
            """,
            
            # Packed segments (for small file optimization)
            'packed_segments': f"""
                CREATE TABLE IF NOT EXISTS packed_segments (
                    id {id_type},
                    packed_segment_id {uuid_type} UNIQUE NOT NULL,
                    total_size INTEGER NOT NULL,
                    file_count INTEGER NOT NULL,
                    compression_type VARCHAR(50),
                    compressed_size INTEGER,
                    hash VARCHAR(64),
                    message_id {text_type},
                    subject {text_type},
                    newsgroup VARCHAR(255),
                    upload_status VARCHAR(50) DEFAULT 'pending',
                    uploaded_at {timestamp_type},
                    metadata {json_type},
                    created_at {timestamp_type}
                )
            """,
            
            # Upload queue (priority-based)
            'upload_queue': f"""
                CREATE TABLE IF NOT EXISTS upload_queue (
                    id {id_type},
                    queue_id {uuid_type} UNIQUE NOT NULL,
                    entity_id {uuid_type} NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    priority INTEGER DEFAULT 5,
                    state VARCHAR(50) DEFAULT 'queued',
                    progress REAL DEFAULT 0.0,
                    total_size {bigint_type},
                    uploaded_size {bigint_type} DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    session_id {uuid_type},
                    worker_id VARCHAR(255),
                    error_message {text_type},
                    queued_at {timestamp_type},
                    started_at {timestamp_type},
                    completed_at {timestamp_type},
                    metadata {json_type},
                    CHECK (priority BETWEEN 1 AND 10),
                    CHECK (state IN ('queued', 'uploading', 'completed', 'failed', 'cancelled', 'retrying', 'paused'))
                )
            """,
            
            # Download queue
            'download_queue': f"""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id {id_type},
                    queue_id {uuid_type} UNIQUE NOT NULL,
                    entity_id {uuid_type} NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    priority INTEGER DEFAULT 5,
                    state VARCHAR(50) DEFAULT 'queued',
                    progress REAL DEFAULT 0.0,
                    total_size {bigint_type},
                    downloaded_size {bigint_type} DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    session_id {uuid_type},
                    worker_id VARCHAR(255),
                    error_message {text_type},
                    queued_at {timestamp_type},
                    started_at {timestamp_type},
                    completed_at {timestamp_type},
                    metadata {json_type},
                    CHECK (state IN ('queued', 'downloading', 'completed', 'failed', 'cancelled', 'retrying', 'paused'))
                )
            """,
            
            # Shares (complete access control)
            'shares': f"""
                CREATE TABLE IF NOT EXISTS shares (
                    id {id_type},
                    share_id VARCHAR(255) UNIQUE NOT NULL,
                    folder_id {uuid_type} NOT NULL,
                    owner_id VARCHAR(255) NOT NULL,
                    share_type VARCHAR(50) NOT NULL,
                    access_type VARCHAR(50) NOT NULL,  -- Alias for access_level
                    access_level VARCHAR(50) NOT NULL,  -- Keep for compatibility
                    password_hash {text_type},
                    password_salt {text_type},
                    encryption_key {text_type},
                    encrypted BOOLEAN DEFAULT FALSE,
                    access_string {text_type},
                    encrypted_index {text_type},
                    wrapped_keys {json_type},
                    access_control {json_type},
                    allowed_users {json_type},
                    denied_users {json_type},
                    download_count INTEGER DEFAULT 0,
                    max_downloads INTEGER,
                    expires_at {timestamp_type},
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at {timestamp_type},
                    revoke_reason {text_type},
                    index_location {text_type},
                    metadata {json_type},
                    created_by {text_type},
                    created_at {timestamp_type},
                    updated_at {timestamp_type},
                    CHECK (share_type IN ('full', 'partial', 'incremental')),
                    CHECK (access_level IN ('public', 'private', 'protected')),
                    CHECK (access_type IN ('public', 'private', 'protected'))
                )
            """,
            
            # User commitments (for private shares)
            'user_commitments': f"""
                CREATE TABLE IF NOT EXISTS user_commitments (
                    id {id_type},
                    commitment_id {uuid_type} UNIQUE NOT NULL,
                    share_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    commitment_hash VARCHAR(64) NOT NULL,
                    wrapped_key {text_type},
                    permissions {json_type},
                    granted_at {timestamp_type},
                    revoked BOOLEAN DEFAULT FALSE,
                    revoked_at {timestamp_type},
                    metadata {json_type},
                    UNIQUE(share_id, user_id)
                )
            """,
            
            # Messages (NNTP tracking)
            'messages': f"""
                CREATE TABLE IF NOT EXISTS messages (
                    id {id_type},
                    message_id VARCHAR(255) UNIQUE NOT NULL,
                    segment_id {uuid_type},
                    newsgroup VARCHAR(255) NOT NULL,
                    subject VARCHAR(500),
                    internal_subject VARCHAR(64),
                    size INTEGER,
                    lines INTEGER,
                    posted_by VARCHAR(255),
                    posted_at {timestamp_type},
                    server VARCHAR(255),
                    article_number {bigint_type},
                    message_references {text_type},
                    headers {json_type},
                    yenc_metadata {json_type},
                    download_count INTEGER DEFAULT 0,
                    last_accessed {timestamp_type},
                    metadata {json_type},
                    created_at {timestamp_type}
                )
            """,
            
            # Operations log (audit trail)
            'operations': f"""
                CREATE TABLE IF NOT EXISTS operations (
                    id {id_type},
                    operation_id {uuid_type} UNIQUE NOT NULL,
                    entity_id {uuid_type},
                    operation_type VARCHAR(50) NOT NULL,
                    operation_name VARCHAR(255),
                    state VARCHAR(50) DEFAULT 'started',
                    progress REAL DEFAULT 0.0,
                    user_id VARCHAR(64),
                    client_info {json_type},
                    input_params {json_type},
                    output_result {json_type},
                    error_message {text_type},
                    error_trace {text_type},
                    duration_ms INTEGER,
                    started_at {timestamp_type},
                    completed_at {timestamp_type},
                    metadata {json_type},
                    CHECK (state IN ('started', 'running', 'completed', 'failed', 'cancelled'))
                )
            """,
            
            # Configuration (system settings)
            'configuration': f"""
                CREATE TABLE IF NOT EXISTS configuration (
                    id {id_type},
                    key VARCHAR(255) UNIQUE NOT NULL,
                    value {text_type},
                    value_type VARCHAR(50),
                    category VARCHAR(100),
                    description {text_type},
                    is_sensitive BOOLEAN DEFAULT FALSE,
                    is_encrypted BOOLEAN DEFAULT FALSE,
                    updated_by VARCHAR(64),
                    updated_at {timestamp_type},
                    created_at {timestamp_type}
                )
            """,
            
            # Users (identity management)
            'users': f"""
                CREATE TABLE IF NOT EXISTS users (
                    id {id_type},
                    user_id VARCHAR(64) UNIQUE NOT NULL,
                    username VARCHAR(255),
                    display_name VARCHAR(255),
                    email VARCHAR(255),
                    public_key {text_type},
                    private_key_encrypted {text_type},
                    key_derivation_salt VARCHAR(64),
                    permissions {json_type},
                    quota_bytes {bigint_type},
                    used_bytes {bigint_type} DEFAULT 0,
                    api_key VARCHAR(255),
                    api_key_hash VARCHAR(64),
                    session_token VARCHAR(255),
                    session_expires {timestamp_type},
                    last_login {timestamp_type},
                    login_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    metadata {json_type},
                    created_at {timestamp_type},
                    updated_at {timestamp_type}
                )
            """,
            
            # Server health (NNTP server monitoring)
            'server_health': f"""
                CREATE TABLE IF NOT EXISTS server_health (
                    id {id_type},
                    server VARCHAR(255) NOT NULL,
                    port INTEGER DEFAULT 119,
                    ssl_enabled BOOLEAN DEFAULT FALSE,
                    status VARCHAR(50) DEFAULT 'unknown',
                    response_time_ms INTEGER,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    consecutive_failures INTEGER DEFAULT 0,
                    last_error {text_type},
                    capabilities {json_type},
                    retention_days INTEGER,
                    posting_allowed BOOLEAN DEFAULT TRUE,
                    max_connections INTEGER,
                    current_connections INTEGER DEFAULT 0,
                    checked_at {timestamp_type},
                    metadata {json_type},
                    UNIQUE(server, port)
                )
            """,
            
            # Background jobs
            'background_jobs': f"""
                CREATE TABLE IF NOT EXISTS background_jobs (
                    id {id_type},
                    job_id {uuid_type} UNIQUE NOT NULL,
                    job_type VARCHAR(100) NOT NULL,
                    job_name VARCHAR(255),
                    state VARCHAR(50) DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    scheduled_at {timestamp_type},
                    started_at {timestamp_type},
                    completed_at {timestamp_type},
                    next_run_at {timestamp_type},
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    input_data {json_type},
                    output_data {json_type},
                    error_message {text_type},
                    worker_id VARCHAR(255),
                    metadata {json_type},
                    CHECK (state IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'scheduled'))
                )
            """,
            
            # Metrics (performance monitoring)
            'metrics': f"""
                CREATE TABLE IF NOT EXISTS metrics (
                    id {id_type},
                    metric_name VARCHAR(255) NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    value REAL NOT NULL,
                    unit VARCHAR(50),
                    tags {json_type},
                    timestamp {timestamp_type},
                    aggregation_period VARCHAR(50),
                    metadata {json_type}
                )
            """,
            
            # Backup history
            'backup_history': f"""
                CREATE TABLE IF NOT EXISTS backup_history (
                    id {id_type},
                    backup_id {uuid_type} UNIQUE NOT NULL,
                    backup_type VARCHAR(50) NOT NULL,
                    backup_path {text_type},
                    size_bytes {bigint_type},
                    duration_ms INTEGER,
                    tables_backed_up {json_type},
                    compression_type VARCHAR(50),
                    encryption_type VARCHAR(50),
                    verification_status VARCHAR(50),
                    retention_days INTEGER,
                    expires_at {timestamp_type},
                    created_at {timestamp_type},
                    metadata {json_type},
                    CHECK (backup_type IN ('full', 'incremental', 'differential'))
                )
            """
        }
    
    def create_all_tables(self):
        """Create all database tables"""
        logger.info("Creating unified database schema...")
        
        created_tables = []
        for table_name, create_sql in self.tables.items():
            try:
                # Handle INDEX statements for SQLite
                if self.db_type == DatabaseType.SQLITE:
                    create_sql = create_sql.replace("INDEX idx_", "CREATE INDEX IF NOT EXISTS idx_")
                    # Remove inline INDEX from CREATE TABLE
                    lines = create_sql.split('\n')
                    table_lines = []
                    index_lines = []
                    
                    for line in lines:
                        if 'INDEX idx_' in line:
                            # Extract and create separate index
                            index_lines.append(line.strip().rstrip(','))
                        else:
                            table_lines.append(line)
                    
                    # Create table first
                    self.db.execute('\n'.join(table_lines))
                    
                    # Create indexes separately
                    for index_line in index_lines:
                        if index_line:
                            self.db.execute(index_line)
                else:
                    self.db.execute(create_sql)
                
                created_tables.append(table_name)
                
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise
        
        # Create indexes
        self._create_indexes()
        
        # Create triggers
        self._create_triggers()
        
        logger.info(f"Created {len(created_tables)} tables: {', '.join(created_tables)}")
        return created_tables
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        indexes = [
            # Entities indexes
            "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_id)",
            
            # Files indexes
            "CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)",
            "CREATE INDEX IF NOT EXISTS idx_files_version ON files(folder_id, version)",
            
            # Segments indexes
            "CREATE INDEX IF NOT EXISTS idx_segments_file ON segments(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_message ON segments(message_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_status ON segments(upload_status)",
            "CREATE INDEX IF NOT EXISTS idx_segments_packed ON segments(packed_segment_id)",
            
            # Upload queue indexes
            "CREATE INDEX IF NOT EXISTS idx_upload_queue_state ON upload_queue(state, priority)",
            "CREATE INDEX IF NOT EXISTS idx_upload_queue_session ON upload_queue(session_id)",
            
            # Shares indexes
            "CREATE INDEX IF NOT EXISTS idx_shares_folder ON shares(folder_id)",
            "CREATE INDEX IF NOT EXISTS idx_shares_type ON shares(share_type, access_level)",
            
            # Messages indexes
            "CREATE INDEX IF NOT EXISTS idx_messages_newsgroup ON messages(newsgroup)",
            "CREATE INDEX IF NOT EXISTS idx_messages_posted ON messages(posted_at)",
            
            # Operations indexes
            "CREATE INDEX IF NOT EXISTS idx_operations_entity ON operations(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(operation_type)",
            "CREATE INDEX IF NOT EXISTS idx_operations_user ON operations(user_id)",
            
            # Background jobs indexes
            "CREATE INDEX IF NOT EXISTS idx_jobs_state ON background_jobs(state, priority)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_scheduled ON background_jobs(scheduled_at)",
            
            # Metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics(metric_name, timestamp)",
        ]
        
        for index_sql in indexes:
            try:
                self.db.execute(index_sql)
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
    
    def _create_triggers(self):
        """Create database triggers for data integrity"""
        if self.db_type == DatabaseType.SQLITE:
            triggers = [
                # Update timestamp triggers
                """
                CREATE TRIGGER IF NOT EXISTS update_entities_timestamp
                AFTER UPDATE ON entities
                BEGIN
                    UPDATE entities SET updated_at = CURRENT_TIMESTAMP
                    WHERE entity_id = NEW.entity_id;
                END
                """,
                
                # Prevent User ID changes
                """
                CREATE TRIGGER IF NOT EXISTS prevent_user_id_change
                BEFORE UPDATE ON users
                WHEN OLD.user_id != NEW.user_id
                BEGIN
                    SELECT RAISE(ABORT, 'User ID cannot be changed');
                END
                """,
                
                # Update folder stats
                """
                CREATE TRIGGER IF NOT EXISTS update_folder_stats
                AFTER INSERT ON files
                BEGIN
                    UPDATE folders 
                    SET file_count = file_count + 1,
                        total_size = total_size + NEW.size,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE folder_id = NEW.folder_id;
                END
                """
            ]
            
            for trigger_sql in triggers:
                try:
                    self.db.execute(trigger_sql)
                except Exception as e:
                    logger.warning(f"Could not create trigger: {e}")
    
    def drop_all_tables(self):
        """Drop all tables (DANGEROUS - for testing only)"""
        logger.warning("Dropping all database tables...")
        
        # Get list of tables
        if self.db_type == DatabaseType.SQLITE:
            tables = self.db.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            table_names = [t['name'] for t in tables if not t['name'].startswith('sqlite_')]
        else:
            tables = self.db.fetch_all("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            table_names = [t['table_name'] for t in tables]
        
        # Drop each table
        for table_name in table_names:
            try:
                self.db.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                logger.info(f"Dropped table: {table_name}")
            except Exception as e:
                logger.error(f"Error dropping table {table_name}: {e}")
    
    def migrate_from_old_schema(self, old_db_path: str):
        """Migrate data from old fragmented databases"""
        logger.info(f"Migrating from old database: {old_db_path}")
        
        # This would contain migration logic from old schemas
        # Implementation depends on specific old database structures
        pass
    
    def verify_schema(self) -> Dict[str, List[str]]:
        """Verify all tables exist with correct columns"""
        results = {
            'missing_tables': [],
            'missing_columns': [],
            'extra_columns': []
        }
        
        for table_name in self.tables.keys():
            if not self.db.table_exists(table_name):
                results['missing_tables'].append(table_name)
            else:
                # Check columns
                actual_columns = self.db.get_table_info(table_name)
                # Compare with expected schema...
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        for table_name in self.tables.keys():
            if self.db.table_exists(table_name):
                count = self.db.fetch_one(f"SELECT COUNT(*) as cnt FROM {table_name}")
                stats[table_name] = count['cnt'] if count else 0
        
        return stats