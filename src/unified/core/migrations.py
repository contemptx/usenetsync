#!/usr/bin/env python3
"""
Database Migration Manager - Handle schema migrations
Production-ready with version tracking and rollback support
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class UnifiedMigrations:
    """Manage database schema migrations"""
    
    def __init__(self, db):
        """Initialize migration manager"""
        self.db = db
        self._ensure_migration_table()
        self.migrations = self._load_migrations()
    
    def _ensure_migration_table(self):
        """Ensure migration tracking table exists"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
    
    def _load_migrations(self) -> List[Dict[str, Any]]:
        """Load migration definitions"""
        return [
            {
                'version': '001',
                'name': 'initial_schema',
                'up': self._migration_001_up,
                'down': self._migration_001_down
            },
            {
                'version': '002',
                'name': 'add_user_commitments',
                'up': self._migration_002_up,
                'down': self._migration_002_down
            },
            {
                'version': '003',
                'name': 'add_performance_indexes',
                'up': self._migration_003_up,
                'down': self._migration_003_down
            }
        ]
    
    def _migration_001_up(self):
        """Initial schema creation"""
        from .schema import UnifiedSchema
        schema = UnifiedSchema(self.db)
        schema.create_all_tables()
    
    def _migration_001_down(self):
        """Drop initial schema"""
        from .schema import UnifiedSchema
        schema = UnifiedSchema(self.db)
        schema.drop_all_tables()
    
    def _migration_002_up(self):
        """Add user commitments table"""
        # Already included in initial schema
        pass
    
    def _migration_002_down(self):
        """Drop user commitments table"""
        self.db.execute("DROP TABLE IF EXISTS user_commitments")
    
    def _migration_003_up(self):
        """Add performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)",
            "CREATE INDEX IF NOT EXISTS idx_segments_hash ON segments(hash)",
            "CREATE INDEX IF NOT EXISTS idx_messages_subject ON messages(subject)",
        ]
        for index in indexes:
            self.db.execute(index)
    
    def _migration_003_down(self):
        """Drop performance indexes"""
        indexes = [
            "DROP INDEX IF EXISTS idx_files_hash",
            "DROP INDEX IF EXISTS idx_segments_hash",
            "DROP INDEX IF EXISTS idx_messages_subject",
        ]
        for index in indexes:
            self.db.execute(index)
    
    def get_current_version(self) -> Optional[str]:
        """Get current schema version"""
        result = self.db.fetch_one(
            "SELECT version FROM schema_migrations WHERE success = 1 ORDER BY id DESC LIMIT 1"
        )
        return result['version'] if result else None
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations"""
        current = self.get_current_version()
        
        if current is None:
            return self.migrations
        
        pending = []
        found_current = False
        
        for migration in self.migrations:
            if found_current:
                pending.append(migration)
            elif migration['version'] == current:
                found_current = True
        
        return pending
    
    def migrate(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run migrations up to target version"""
        results = {
            'success': True,
            'migrations_applied': [],
            'errors': []
        }
        
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return results
        
        for migration in pending:
            if target_version and migration['version'] > target_version:
                break
            
            try:
                logger.info(f"Applying migration {migration['version']}: {migration['name']}")
                
                start_time = datetime.now()
                
                # Run migration
                migration['up']()
                
                # Record migration
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                checksum = hashlib.sha256(
                    f"{migration['version']}:{migration['name']}".encode()
                ).hexdigest()
                
                self.db.insert('schema_migrations', {
                    'version': migration['version'],
                    'name': migration['name'],
                    'checksum': checksum,
                    'execution_time_ms': execution_time,
                    'success': True
                })
                
                results['migrations_applied'].append(migration['version'])
                logger.info(f"Migration {migration['version']} applied successfully")
                
            except Exception as e:
                logger.error(f"Migration {migration['version']} failed: {e}")
                
                # Record failure
                self.db.insert('schema_migrations', {
                    'version': migration['version'],
                    'name': migration['name'],
                    'checksum': '',
                    'success': False,
                    'error_message': str(e)
                })
                
                results['success'] = False
                results['errors'].append({
                    'version': migration['version'],
                    'error': str(e)
                })
                
                # Stop on error
                break
        
        return results
    
    def rollback(self, target_version: str) -> Dict[str, Any]:
        """Rollback to target version"""
        results = {
            'success': True,
            'migrations_rolled_back': [],
            'errors': []
        }
        
        current = self.get_current_version()
        
        if not current or current <= target_version:
            logger.info("Nothing to rollback")
            return results
        
        # Get migrations to rollback
        to_rollback = []
        for migration in reversed(self.migrations):
            if migration['version'] <= target_version:
                break
            if migration['version'] <= current:
                to_rollback.append(migration)
        
        for migration in to_rollback:
            try:
                logger.info(f"Rolling back migration {migration['version']}: {migration['name']}")
                
                # Run rollback
                migration['down']()
                
                # Remove migration record
                self.db.delete(
                    'schema_migrations',
                    'version = ?',
                    (migration['version'],)
                )
                
                results['migrations_rolled_back'].append(migration['version'])
                logger.info(f"Migration {migration['version']} rolled back successfully")
                
            except Exception as e:
                logger.error(f"Rollback of {migration['version']} failed: {e}")
                results['success'] = False
                results['errors'].append({
                    'version': migration['version'],
                    'error': str(e)
                })
                break
        
        return results
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        return self.db.fetch_all(
            "SELECT * FROM schema_migrations ORDER BY id DESC"
        )