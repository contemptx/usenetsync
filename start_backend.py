#!/usr/bin/env python3
"""
Start the unified backend API server
"""
import os
import sys
import uvicorn

# Add backend/src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from unified.api.server import create_app
from unified.core.config import load_config, UnifiedConfig
from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema
from unified.core.migrations import UnifiedMigrations

if __name__ == "__main__":
    # Load configuration
    config: UnifiedConfig = load_config()
    
    # Initialize database
    db_config = DatabaseConfig(
        db_type=DatabaseType.POSTGRESQL if config.database_type == 'postgresql' else DatabaseType.SQLITE,
        sqlite_path=config.database_path,
        pg_host=config.database_host,
        pg_port=config.database_port,
        pg_database=config.database_name,
        pg_user=config.database_user,
        pg_password=config.database_password
    )
    db = UnifiedDatabase(db_config)
    
    # Run migrations
    migrations = UnifiedMigrations(db)
    migrations.migrate()
    
    # Create and run the FastAPI app
    app = create_app()
    uvicorn.run(app, host=config.api_host, port=config.api_port, log_level="info")
