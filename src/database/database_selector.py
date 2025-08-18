"""
Database Selector - Automatically chooses between PostgreSQL and SQLite
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseSelector:
    """Automatically selects the appropriate database backend"""
    
    @staticmethod
    def get_config_path() -> Path:
        """Get the configuration file path"""
        if sys.platform == "win32":
            config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync'
        else:
            config_dir = Path.home() / '.usenetsync'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = DatabaseSelector.get_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        return {}
    
    @staticmethod
    def save_config(config: Dict[str, Any]):
        """Save configuration to file"""
        config_path = DatabaseSelector.get_config_path()
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    @staticmethod
    def test_postgresql() -> bool:
        """Test if PostgreSQL is available"""
        try:
            import psycopg2
            # Try to connect to PostgreSQL
            conn = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                port=int(os.environ.get('POSTGRES_PORT', '5432')),
                user=os.environ.get('POSTGRES_USER', 'usenet'),
                password=os.environ.get('POSTGRES_PASSWORD', 'usenetsync'),
                database=os.environ.get('POSTGRES_DB', 'usenet'),
                connect_timeout=3
            )
            conn.close()
            return True
        except Exception as e:
            logger.info(f"PostgreSQL not available: {e}")
            return False
    
    @staticmethod
    def get_database_manager():
        """Get the appropriate database manager based on availability"""
        config = DatabaseSelector.load_config()
        
        # Check if user has forced SQLite mode
        use_sqlite = (
            os.environ.get('USE_SQLITE', '').lower() == 'true' or
            config.get('database', {}).get('type') == 'sqlite'
        )
        
        if not use_sqlite:
            # Try PostgreSQL first
            if DatabaseSelector.test_postgresql():
                logger.info("Using PostgreSQL database")
                from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
                
                pg_config = PostgresConfig(
                    host=os.environ.get('POSTGRES_HOST', 'localhost'),
                    port=int(os.environ.get('POSTGRES_PORT', '5432')),
                    user=os.environ.get('POSTGRES_USER', 'usenet'),
                    password=os.environ.get('POSTGRES_PASSWORD', 'usenetsync'),
                    database=os.environ.get('POSTGRES_DB', 'usenet')
                )
                return ShardedPostgreSQLManager(pg_config), 'postgresql'
        
        # Fall back to SQLite
        logger.info("Using SQLite database")
        from database.production_db_wrapper import ProductionDatabaseManager
        from database.enhanced_database_manager import DatabaseConfig
        
        # Determine SQLite path
        if sys.platform == "win32":
            default_db_path = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync' / 'data.db'
        else:
            default_db_path = Path.home() / '.usenetsync' / 'data.db'
        
        sqlite_path = os.environ.get('SQLITE_PATH', str(default_db_path))
        
        # Ensure directory exists
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        
        db_config = DatabaseConfig()
        db_config.path = sqlite_path
        
        # Save config for future use
        if not config.get('database'):
            config['database'] = {
                'type': 'sqlite',
                'path': sqlite_path
            }
            DatabaseSelector.save_config(config)
        
        return ProductionDatabaseManager(db_config), 'sqlite'
    
    @staticmethod
    def get_connection_info() -> Dict[str, Any]:
        """Get information about the current database connection"""
        config = DatabaseSelector.load_config()
        
        if DatabaseSelector.test_postgresql():
            return {
                'type': 'postgresql',
                'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                'port': int(os.environ.get('POSTGRES_PORT', '5432')),
                'database': os.environ.get('POSTGRES_DB', 'usenet'),
                'status': 'connected'
            }
        else:
            if sys.platform == "win32":
                default_db_path = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync' / 'data.db'
            else:
                default_db_path = Path.home() / '.usenetsync' / 'data.db'
            
            sqlite_path = os.environ.get('SQLITE_PATH', str(default_db_path))
            
            return {
                'type': 'sqlite',
                'path': sqlite_path,
                'status': 'connected' if Path(sqlite_path).exists() else 'not initialized'
            }