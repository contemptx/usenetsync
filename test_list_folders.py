#!/usr/bin/env python3
"""
Test what list-folders actually returns
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, '/workspace/src')
sys.path.insert(0, '/workspace')

# Mock the database connection to return empty folders
def mock_list_folders():
    """Return what list-folders should return"""
    # This is what the frontend expects - an array of folder objects
    return []

# Test the actual command
def test_actual_command():
    """Test the actual list-folders command"""
    try:
        # Try to import and run the actual command
        from database.database_selector import DatabaseSelector
        
        if DatabaseSelector:
            db_manager, db_type = DatabaseSelector.get_database_manager()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create table if needed
                if db_type == 'sqlite':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS folders (
                            folder_id TEXT PRIMARY KEY,
                            path TEXT NOT NULL,
                            name TEXT NOT NULL,
                            state TEXT DEFAULT 'added',
                            published INTEGER DEFAULT 0,
                            share_id TEXT,
                            access_type TEXT DEFAULT 'public',
                            total_files INTEGER DEFAULT 0,
                            total_size INTEGER DEFAULT 0,
                            total_segments INTEGER DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS folders (
                            folder_id VARCHAR(255) PRIMARY KEY,
                            path TEXT NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            state VARCHAR(50) DEFAULT 'added',
                            published BOOLEAN DEFAULT FALSE,
                            share_id VARCHAR(255),
                            access_type VARCHAR(50) DEFAULT 'public',
                            total_files INTEGER DEFAULT 0,
                            total_size BIGINT DEFAULT 0,
                            total_segments INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                conn.commit()
                
                # Query folders
                cursor.execute("""
                    SELECT folder_id, name, path, state, total_files, total_size,
                           total_segments, share_id, published, created_at
                    FROM folders
                    ORDER BY created_at DESC
                """)
                
                folders = []
                for row in cursor.fetchall():
                    folders.append({
                        'folder_id': row[0],
                        'name': row[1],
                        'path': row[2],
                        'state': row[3],
                        'total_files': row[4] or 0,
                        'total_size': row[5] or 0,
                        'total_segments': row[6] or 0,
                        'share_id': row[7],
                        'published': row[8] or False,
                        'created_at': row[9].isoformat() if row[9] else None
                    })
                
                return folders
        else:
            return []
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    # Test what we should return
    result = test_actual_command()
    
    # Always output valid JSON
    print(json.dumps(result))
    
    # Also show debug info to stderr
    print(f"Returned {len(result)} folders", file=sys.stderr)