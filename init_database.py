#!/usr/bin/env python3
"""
Initialize database with correct schema
"""

import os
import sys

sys.path.insert(0, '/workspace/src')

# Set database path
os.environ['USENETSYNC_DB'] = '/tmp/test_usenetsync.db'

from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema

# Initialize database
config = DatabaseConfig(
    db_type=DatabaseType.SQLITE,
    sqlite_path='/tmp/test_usenetsync.db'
)

db = UnifiedDatabase(config)
schema = UnifiedSchema(db)

# Initialize all tables
schema.initialize_schema()

print("✅ Database initialized with all tables")

# Verify tables exist
tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
print(f"✅ Created {len(tables)} tables:")
for table in tables:
    print(f"   - {table['name']}")
    
# Check columns in folders table
columns = db.fetch_all("PRAGMA table_info(folders)")
print("\n✅ Folders table columns:")
for col in columns:
    print(f"   - {col['name']} ({col['type']})")