#!/usr/bin/env python3
"""Check what tables and columns actually exist"""

import sys
import os

sys.path.insert(0, '/workspace/src')
sys.path.insert(0, '/workspace')

from database.database_selector import DatabaseSelector

try:
    db_manager, db_type = DatabaseSelector.get_database_manager()
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        if db_type == 'sqlite':
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"SQLite Tables: {tables}")
            
            # Check folders table structure
            cursor.execute("PRAGMA table_info(folders)")
            columns = cursor.fetchall()
            print(f"\nFolders table columns:")
            for col in columns:
                print(f"  {col}")
                
            # Try to query with different column names
            try:
                cursor.execute("SELECT * FROM folders LIMIT 1")
                print(f"\nSample query successful")
            except Exception as e:
                print(f"\nQuery failed: {e}")
                
        else:
            # PostgreSQL
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            print(f"PostgreSQL Tables: {tables}")
            
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'folders'
            """)
            columns = cursor.fetchall()
            print(f"\nFolders table columns:")
            for col in columns:
                print(f"  {col}")
                
except Exception as e:
    print(f"Error: {e}")