"""
Database configuration for the application
"""
import os
from pathlib import Path
from production_db_wrapper import create_production_db, ProductionDatabaseManager
from enhanced_database_manager_production import DatabaseConfig

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database paths
PRODUCTION_DB_PATH = DATA_DIR / "usenetsync.db"
DATABASE_LOG_PATH = LOGS_DIR / "database.log"

# Database configuration based on environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Pool sizes by environment
POOL_SIZES = {
    "development": 1,    # Single connection for development
    "testing": 1,        # Single connection for tests
    "staging": 5,        # Moderate for staging
    "production": 10     # Full pool for production
}

def get_database_manager() -> ProductionDatabaseManager:
    """
    Get configured database manager instance
    
    Returns:
        ProductionDatabaseManager: Configured database instance
    """
    pool_size = POOL_SIZES.get(ENVIRONMENT, 10)
    
    # Create database manager with production features
    db = create_production_db(
        db_path=str(PRODUCTION_DB_PATH),
        log_file=str(DATABASE_LOG_PATH) if ENVIRONMENT != "testing" else None,
        pool_size=pool_size
    )
    
    return db

# Singleton instance (optional)
_db_instance = None

def get_db() -> ProductionDatabaseManager:
    """
    Get singleton database instance
    
    Note: Remember to close with close_db() when application shuts down
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = get_database_manager()
    return _db_instance

def close_db():
    """Close the singleton database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None

# For backwards compatibility
def initialize_database(config: DatabaseConfig = None) -> ProductionDatabaseManager:
    """
    Initialize database (backwards compatible function)
    
    Args:
        config: Optional DatabaseConfig (ignored, uses production settings)
        
    Returns:
        ProductionDatabaseManager instance
    """
    return get_database_manager()
