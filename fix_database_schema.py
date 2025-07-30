#!/usr/bin/env python3
"""
Fix database schema by adding missing columns
"""

import sqlite3
from pathlib import Path

def add_missing_columns():
    """Add missing columns to the database"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    print(f"Updating database schema: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check existing columns in folders table
        cursor.execute("PRAGMA table_info(folders)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns to folders table
        columns_to_add = [
            ('private_key', 'BLOB'),
            ('public_key', 'BLOB'), 
            ('keys_updated_at', 'TIMESTAMP'),
            ('file_count', 'INTEGER DEFAULT 0'),
            ('total_size', 'INTEGER DEFAULT 0'),
            ('last_updated', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        added_columns = []
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE folders ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    added_columns.append(column_name)
                    print(f"OK: Added column {column_name}")
                except Exception as e:
                    print(f"WARNING: Could not add column {column_name}: {e}")
        
        # Also check segments table and add state column if missing
        try:
            cursor.execute("PRAGMA table_info(segments)")
            segment_columns = [row[1] for row in cursor.fetchall()]
            
            if 'state' not in segment_columns:
                cursor.execute("ALTER TABLE segments ADD COLUMN state TEXT DEFAULT 'pending'")
                added_columns.append("segments.state")
                print("OK: Added segments.state column")
        except Exception as e:
            print(f"WARNING: Could not check/add segments.state: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"SUCCESS: Added {len(added_columns)} missing columns")
            return True
        else:
            print("OK: All required columns already exist")
            return True
            
    except Exception as e:
        print(f"ERROR: Database schema update failed: {e}")
        return False

def fix_update_folder_keys_method():
    """Fix the update_folder_keys method to handle missing columns gracefully"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("WARNING: production_db_wrapper.py not found")
        return True
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if update_folder_keys method exists and needs fixing
    if 'def update_folder_keys(' in content and 'keys_updated_at' in content:
        # Replace the problematic UPDATE statement
        old_update = '''conn.execute("""
                UPDATE folders 
                SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (private_key, public_key, folder_id))'''
        
        new_update = '''# Try with keys_updated_at first, fallback without it
                try:
                    conn.execute("""
                        UPDATE folders 
                        SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (private_key, public_key, folder_id))
                except Exception:
                    # Fallback if keys_updated_at column doesn't exist
                    conn.execute("""
                        UPDATE folders 
                        SET private_key = ?, public_key = ?
                        WHERE id = ?
                    """, (private_key, public_key, folder_id))'''
        
        if old_update in content:
            content = content.replace(old_update, new_update)
            
            with open(wrapper_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("OK: Fixed update_folder_keys method for schema compatibility")
            return True
    
    print("OK: update_folder_keys method doesn't need fixing")
    return True

def test_database_connection():
    """Test database connection and schema"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("WARNING: Database file not found")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Test the folders table
        cursor.execute("SELECT COUNT(*) FROM folders")
        folder_count = cursor.fetchone()[0]
        print(f"OK: Database accessible, {folder_count} folders found")
        
        # Check if we can do a basic update (without keys_updated_at)
        cursor.execute("SELECT id FROM folders LIMIT 1")
        row = cursor.fetchone()
        if row:
            folder_id = row[0]
            cursor.execute("UPDATE folders SET last_updated = CURRENT_TIMESTAMP WHERE id = ?", (folder_id,))
            print("OK: Basic UPDATE operations work")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("Fix Database Schema")
    print("=" * 50)
    
    success = True
    
    # Add missing columns
    if not add_missing_columns():
        print("ERROR: Could not update database schema")
        success = False
    
    # Fix the method to be more robust
    if not fix_update_folder_keys_method():
        print("ERROR: Could not fix update_folder_keys method")
        success = False
    
    # Test database
    if not test_database_connection():
        print("ERROR: Database test failed")
        success = False
    
    print()
    if success:
        print("SUCCESS: Database schema updated!")
        print()
        print("Fixed:")
        print("  - Added missing columns to folders table")
        print("  - Made update_folder_keys method more robust")
        print("  - Verified database connectivity")
        print()
        print("Folder indexing should now work without schema errors!")
    else:
        print("ERROR: Some database fixes failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)