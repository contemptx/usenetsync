"""Database Migration System for UsenetSync"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UnifiedMigrations:
    """Manages database schema migrations"""
    
    def __init__(self, db):
        self.db = db
        self._ensure_migration_table()
        
    def _ensure_migration_table(self):
        """Ensure migrations tracking table exists"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    def get_current_version(self) -> int:
        """Get current schema version"""
        result = self.db.fetch_one(
            "SELECT MAX(version) as version FROM schema_migrations"
        )
        return result['version'] if result and result['version'] else 0
        
    def migrate(self):
        """Run all pending migrations"""
        current = self.get_current_version()
        migrations = self._get_migrations()
        applied = 0
        
        for version, migration in migrations.items():
            if version > current:
                logger.info(f"Applying migration {version}: {migration['name']}")
                try:
                    for sql in migration['sql']:
                        self.db.execute(sql)
                    self.db.insert('schema_migrations', {
                        'version': version,
                        'name': migration['name']
                    })
                    applied += 1
                except Exception as e:
                    logger.error(f"Migration {version} failed: {e}")
                    raise
                    
        logger.info(f"Applied {applied} migrations, database at version {self.get_current_version()}")
        return applied
        
    def _get_migrations(self) -> Dict[int, Dict[str, Any]]:
        """Define all migrations"""
        return {
            1: {
                'name': 'initial_schema',
                'sql': ["SELECT 1"]  # Schema created by UnifiedSchema
            },
            2: {
                'name': 'add_share_tracking',
                'sql': [
                    "ALTER TABLE shares ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0",
                    "ALTER TABLE shares ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP"
                ]
            },
            3: {
                'name': 'add_user_preferences',
                'sql': [
                    """CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id VARCHAR(255) PRIMARY KEY,
                        theme VARCHAR(50) DEFAULT 'light',
                        notifications BOOLEAN DEFAULT TRUE,
                        auto_index BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )"""
                ]
            }
        }
