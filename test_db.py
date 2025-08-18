#!/usr/bin/env python3
"""Test database connection"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
    
    # Try to connect with test config
    config = PostgresConfig(
        host="localhost",
        port=5432,
        database="usenetsync",
        user="usenet",
        password="usenet_secure_2024"
    )
    
    print("Creating database manager...")
    db_manager = ShardedPostgreSQLManager(config)
    print("Database manager created successfully!")
    
    # Try to get a connection
    print("Testing connection...")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Connection successful! Test query result: {result}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()