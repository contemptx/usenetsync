"""Database migration system for UsenetSync."""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import shutil

@dataclass
class Migration:
    """Represents a database migration."""
    version: int
    name: str
    description: str
    up: Callable  # Function to apply migration
    down: Optional[Callable]  # Function to rollback migration
    checksum: str
    requires_backup: bool = True

class MigrationManager:
    """Manages database schema migrations."""
    
    def __init__(self, db_manager, backup_dir: Path = None):
        self.db = db_manager
        self.backup_dir = backup_dir or Path.home() / ".usenetsync" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.migrations: List[Migration] = []
        self._register_migrations()
        
    async def initialize(self):
        """Initialize migration system."""
        await self._create_migration_table()
        
    async def _create_migration_table(self):
        """Create migration tracking table."""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                status TEXT DEFAULT 'success'
            )
        """)
        
    def _register_migrations(self):
        """Register all available migrations."""
        # Migration 1: Add version control tables
        self.add_migration(
            version=1,
            name="add_version_control",
            description="Add file version control tables",
            up=self._migration_001_up,
            down=self._migration_001_down
        )
        
        # Migration 2: Add quota management
        self.add_migration(
            version=2,
            name="add_quota_management",
            description="Add storage quota management tables",
            up=self._migration_002_up,
            down=self._migration_002_down
        )
        
        # Migration 3: Add cache metadata
        self.add_migration(
            version=3,
            name="add_cache_metadata",
            description="Add cache metadata tracking",
            up=self._migration_003_up,
            down=self._migration_003_down
        )
        
        # Migration 4: Add server rotation
        self.add_migration(
            version=4,
            name="add_server_rotation",
            description="Add server rotation and health tracking",
            up=self._migration_004_up,
            down=self._migration_004_down
        )
        
        # Migration 5: Add analytics tables
        self.add_migration(
            version=5,
            name="add_analytics",
            description="Add analytics and statistics tables",
            up=self._migration_005_up,
            down=self._migration_005_down
        )
        
    def add_migration(
        self,
        version: int,
        name: str,
        description: str,
        up: Callable,
        down: Optional[Callable] = None,
        requires_backup: bool = True
    ):
        """Add a migration to the registry."""
        # Generate checksum for migration
        content = f"{version}:{name}:{description}"
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        migration = Migration(
            version=version,
            name=name,
            description=description,
            up=up,
            down=down,
            checksum=checksum,
            requires_backup=requires_backup
        )
        
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
        
    async def get_current_version(self) -> int:
        """Get current database schema version."""
        result = await self.db.fetch_one("""
            SELECT MAX(version) as version 
            FROM schema_migrations 
            WHERE status = 'success'
        """)
        
        return result['version'] if result and result['version'] else 0
        
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        current_version = await self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
        
    async def migrate(
        self,
        target_version: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run migrations up to target version.
        
        Args:
            target_version: Target version (None for latest)
            dry_run: If True, don't actually apply migrations
            
        Returns:
            Migration results
        """
        current_version = await self.get_current_version()
        
        if target_version is None:
            target_version = max(m.version for m in self.migrations) if self.migrations else 0
            
        results = {
            'from_version': current_version,
            'to_version': target_version,
            'migrations_applied': [],
            'errors': [],
            'dry_run': dry_run
        }
        
        if current_version >= target_version:
            results['message'] = 'Already at target version'
            return results
            
        # Get migrations to apply
        migrations_to_apply = [
            m for m in self.migrations 
            if current_version < m.version <= target_version
        ]
        
        if dry_run:
            results['migrations_to_apply'] = [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description
                }
                for m in migrations_to_apply
            ]
            return results
            
        # Create backup if needed
        backup_path = None
        if any(m.requires_backup for m in migrations_to_apply):
            backup_path = await self._backup_database()
            results['backup_path'] = str(backup_path)
            
        # Apply migrations
        for migration in migrations_to_apply:
            try:
                start_time = datetime.now()
                
                # Begin transaction
                await self.db.execute("BEGIN TRANSACTION")
                
                # Apply migration
                await migration.up(self.db)
                
                # Record migration
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                await self.db.execute("""
                    INSERT INTO schema_migrations 
                    (version, name, description, checksum, execution_time_ms, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    int(execution_time),
                    'success'
                ))
                
                # Commit transaction
                await self.db.execute("COMMIT")
                
                results['migrations_applied'].append({
                    'version': migration.version,
                    'name': migration.name,
                    'execution_time_ms': execution_time
                })
                
            except Exception as e:
                # Rollback transaction
                await self.db.execute("ROLLBACK")
                
                error_msg = f"Migration {migration.version} ({migration.name}) failed: {str(e)}"
                results['errors'].append(error_msg)
                
                # Record failed migration
                await self.db.execute("""
                    INSERT INTO schema_migrations 
                    (version, name, description, checksum, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    'failed'
                ))
                
                # Restore from backup if available
                if backup_path:
                    await self._restore_database(backup_path)
                    results['restored_from_backup'] = True
                    
                break
                
        results['final_version'] = await self.get_current_version()
        return results
        
    async def rollback(
        self,
        target_version: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Rollback to a previous version.
        
        Args:
            target_version: Target version to rollback to
            dry_run: If True, don't actually rollback
            
        Returns:
            Rollback results
        """
        current_version = await self.get_current_version()
        
        results = {
            'from_version': current_version,
            'to_version': target_version,
            'migrations_rolled_back': [],
            'errors': [],
            'dry_run': dry_run
        }
        
        if current_version <= target_version:
            results['message'] = 'Already at or below target version'
            return results
            
        # Get migrations to rollback
        migrations_to_rollback = [
            m for m in reversed(self.migrations)
            if target_version < m.version <= current_version
        ]
        
        # Check if all have down migrations
        missing_down = [m for m in migrations_to_rollback if m.down is None]
        if missing_down:
            results['errors'].append(
                f"Cannot rollback: migrations {[m.version for m in missing_down]} have no down method"
            )
            return results
            
        if dry_run:
            results['migrations_to_rollback'] = [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description
                }
                for m in migrations_to_rollback
            ]
            return results
            
        # Create backup
        backup_path = await self._backup_database()
        results['backup_path'] = str(backup_path)
        
        # Rollback migrations
        for migration in migrations_to_rollback:
            try:
                start_time = datetime.now()
                
                # Begin transaction
                await self.db.execute("BEGIN TRANSACTION")
                
                # Apply rollback
                if migration.down:
                    await migration.down(self.db)
                
                # Remove migration record
                await self.db.execute(
                    "DELETE FROM schema_migrations WHERE version = ?",
                    (migration.version,)
                )
                
                # Commit transaction
                await self.db.execute("COMMIT")
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                results['migrations_rolled_back'].append({
                    'version': migration.version,
                    'name': migration.name,
                    'execution_time_ms': execution_time
                })
                
            except Exception as e:
                # Rollback transaction
                await self.db.execute("ROLLBACK")
                
                error_msg = f"Rollback of migration {migration.version} failed: {str(e)}"
                results['errors'].append(error_msg)
                
                # Restore from backup
                await self._restore_database(backup_path)
                results['restored_from_backup'] = True
                break
                
        results['final_version'] = await self.get_current_version()
        return results
        
    async def validate_schema(self) -> Dict[str, Any]:
        """Validate database schema integrity."""
        results = {
            'valid': True,
            'issues': [],
            'current_version': await self.get_current_version()
        }
        
        # Check migration checksums
        applied_migrations = await self.db.fetch_all("""
            SELECT version, checksum 
            FROM schema_migrations 
            WHERE status = 'success'
        """)
        
        for row in applied_migrations:
            version = row['version']
            stored_checksum = row['checksum']
            
            # Find corresponding migration
            migration = next((m for m in self.migrations if m.version == version), None)
            
            if not migration:
                results['issues'].append(f"Migration {version} in database but not in code")
                results['valid'] = False
            elif migration.checksum != stored_checksum:
                results['issues'].append(
                    f"Checksum mismatch for migration {version}: "
                    f"expected {migration.checksum}, got {stored_checksum}"
                )
                results['valid'] = False
                
        # Check for required tables
        required_tables = [
            'users', 'files', 'shares', 'uploads', 'downloads',
            'settings', 'logs', 'file_versions'
        ]
        
        for table in required_tables:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            result = await self.db.fetch_one(query)
            if not result:
                results['issues'].append(f"Required table '{table}' is missing")
                results['valid'] = False
                
        return results
        
    async def _backup_database(self) -> Path:
        """Create database backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        # Copy database file
        # This assumes SQLite - adjust for other databases
        db_path = Path("usenetsync.db")  # Adjust path
        shutil.copy2(db_path, backup_path)
        
        # Also export as SQL dump
        dump_path = backup_path.with_suffix('.sql')
        await self._export_sql_dump(dump_path)
        
        return backup_path
        
    async def _restore_database(self, backup_path: Path):
        """Restore database from backup."""
        db_path = Path("usenetsync.db")  # Adjust path
        shutil.copy2(backup_path, db_path)
        
    async def _export_sql_dump(self, dump_path: Path):
        """Export database as SQL dump."""
        # This would use database-specific dump commands
        # For SQLite:
        import subprocess
        db_path = Path("usenetsync.db")
        
        with open(dump_path, 'w') as f:
            subprocess.run(
                ['sqlite3', str(db_path), '.dump'],
                stdout=f,
                check=True
            )
            
    # ==================== Migration Definitions ====================
    
    async def _migration_001_up(self, db):
        """Add version control tables."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS file_versions (
                id TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                size INTEGER,
                metadata TEXT,
                UNIQUE(file_hash, version_number)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS version_chains (
                id TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                parent_version_id TEXT,
                child_version_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    async def _migration_001_down(self, db):
        """Remove version control tables."""
        await db.execute("DROP TABLE IF EXISTS version_chains")
        await db.execute("DROP TABLE IF EXISTS file_versions")
        
    async def _migration_002_up(self, db):
        """Add quota management tables."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS storage_quotas (
                user_id TEXT PRIMARY KEY,
                max_storage_bytes INTEGER,
                max_files INTEGER,
                max_share_size INTEGER,
                current_usage_bytes INTEGER DEFAULT 0,
                current_file_count INTEGER DEFAULT 0,
                warning_threshold REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    async def _migration_002_down(self, db):
        """Remove quota management tables."""
        await db.execute("DROP TABLE IF EXISTS storage_quotas")
        
    async def _migration_003_up(self, db):
        """Add cache metadata table."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                size INTEGER,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                ttl_seconds INTEGER,
                file_path TEXT
            )
        """)
        
    async def _migration_003_down(self, db):
        """Remove cache metadata table."""
        await db.execute("DROP TABLE IF EXISTS cache_metadata")
        
    async def _migration_004_up(self, db):
        """Add server health tracking."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS server_health (
                server_id TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                last_check TIMESTAMP,
                status TEXT,
                response_time_ms INTEGER,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                consecutive_failures INTEGER DEFAULT 0
            )
        """)
        
    async def _migration_004_down(self, db):
        """Remove server health tracking."""
        await db.execute("DROP TABLE IF EXISTS server_health")
        
    async def _migration_005_up(self, db):
        """Add analytics tables."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id TEXT,
                metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_user 
            ON usage_analytics(user_id, timestamp)
        """)
        
    async def _migration_005_down(self, db):
        """Remove analytics tables."""
        await db.execute("DROP INDEX IF EXISTS idx_analytics_user")
        await db.execute("DROP TABLE IF EXISTS usage_analytics")