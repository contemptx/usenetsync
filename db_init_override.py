#!/usr/bin/env python3
"""
Override for database initialization to prevent schema conflicts
"""

import logging
from pathlib import Path

# Monkey patch to prevent schema reinitialization
_original_init_db = None

def override_database_init():
    """Override the database initialization to prevent schema conflicts"""
    
    try:
        import enhanced_database_manager
        
        # Save original method
        global _original_init_db
        _original_init_db = enhanced_database_manager.EnhancedDatabaseManager._initialize_database
        
        # Create new method that checks first
        def _safe_initialize_database(self):
            """Safe initialization that doesn't overwrite existing schema"""
            try:
                # Check if main tables exist
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table' 
                        AND name IN ('folders', 'upload_queue', 'publications')
                    """)
                    count = cursor.fetchone()[0]
                    
                    if count >= 3:
                        logging.info("Database already has required tables, skipping schema init")
                        return
            except Exception as e:
                logging.debug(f"Database check: {e}")
            
            # Call original if needed
            try:
                _original_init_db(self)
            except Exception as e:
                logging.warning(f"Schema init warning (ignored): {e}")
        
        # Replace the method
        enhanced_database_manager.EnhancedDatabaseManager._initialize_database = _safe_initialize_database
        
        logging.info("Database initialization override applied")
        
    except Exception as e:
        logging.error(f"Could not apply override: {e}")

# Apply the override when imported
override_database_init()
