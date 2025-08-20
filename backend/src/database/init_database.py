#!/usr/bin/env python3
"""
Simple Database Initialization Script
"""

import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from database.enhanced_database_manager import DatabaseConfig, EnhancedDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database"""
    
    config = DatabaseConfig()
    config.path = "data/usenetsync.db"
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    logger.info(f"Initializing database at {config.path}")
    
    try:
        # Simply creating the EnhancedDatabaseManager should initialize the database
        db = EnhancedDatabaseManager(config)
        
        logger.info("Database initialized successfully!")
        
        # Try to verify tables exist
        try:
            # Use the context manager approach
            with db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Created tables: {tables}")
        except Exception as e:
            logger.warning(f"Could not verify tables: {e}")
        
        # Close the database
        db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
