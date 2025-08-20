#!/usr/bin/env python3
"""
Start the Unified Backend API Server
This script properly initializes and starts the unified backend
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, '/workspace/src')

# Set up environment
os.environ.update({
    'DATABASE_URL': 'postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync',
    'DATABASE_TYPE': 'postgresql',
    'DATABASE_HOST': 'localhost',
    'DATABASE_PORT': '5432',
    'DATABASE_NAME': 'usenetsync',
    'DATABASE_USER': 'usenetsync',
    'DATABASE_PASSWORD': 'usenetsync123',
    'NNTP_HOST': 'news.newshosting.com',
    'NNTP_PORT': '563',
    'NNTP_USERNAME': 'contemptx',
    'NNTP_PASSWORD': 'Kia211101#',
    'NNTP_SSL': 'true',
    'API_HOST': '0.0.0.0',
    'API_PORT': '8000',
    'SECRET_KEY': 'usenetsync-secret-key',
    'JWT_SECRET': 'usenetsync-jwt-secret',
})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize database schema if needed"""
    try:
        from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
        from unified.core.schema import UnifiedSchema
        
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            pg_host='localhost',
            pg_port=5432,
            pg_database='usenetsync',
            pg_user='usenetsync',
            pg_password='usenetsync123'
        )
        
        db = UnifiedDatabase(config)
        schema = UnifiedSchema(db)
        schema.create_all_tables()
        logger.info("Database schema initialized")
        return db
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return None

def start_server():
    """Start the unified API server"""
    try:
        # Initialize database first
        db = initialize_database()
        if not db:
            logger.error("Database initialization failed")
            return
        
        # Import and create the FastAPI app
        from unified.api.server import UnifiedAPIServer
        import uvicorn
        
        # Create server instance
        server = UnifiedAPIServer()
        
        # Get the app
        app = server.app
        
        logger.info("Starting Unified API Server on http://0.0.0.0:8000")
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting UsenetSync Unified Backend...")
    start_server()