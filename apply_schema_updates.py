#!/usr/bin/env python3
"""
Apply schema updates to add missing tables.
This script will create the new tables without affecting existing data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.src.unified.core.database import UnifiedDatabase
from backend.src.unified.core.schema import UnifiedSchema

def apply_schema_updates():
    """Apply schema updates to create missing tables."""
    print("Applying schema updates...")
    
    try:
        # Initialize database
        db = UnifiedDatabase()
        print(f"Connected to database: {db.db_path if hasattr(db, 'db_path') else 'database'}")
        
        # Initialize schema
        schema = UnifiedSchema(db)
        print("Schema initialized")
        
        # Create all tables (will skip existing ones)
        schema.create_tables()
        print("Tables created/verified")
        
        # Verify new tables exist
        new_tables = ['authorized_users', 'access_commitments', 'access_logs']
        for table_name in new_tables:
            try:
                result = db.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
                print(f"✅ Table '{table_name}' exists with {result['count']} rows")
            except Exception as e:
                print(f"❌ Table '{table_name}' check failed: {e}")
        
        # Create indexes
        schema.create_indexes()
        print("Indexes created/verified")
        
        print("\n✅ Schema updates applied successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error applying schema updates: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_schema_updates()
    sys.exit(0 if success else 1)