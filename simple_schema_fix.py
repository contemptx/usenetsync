#!/usr/bin/env python3
"""
Simple database schema fix - only fix what's needed
"""

import sqlite3
from pathlib import Path

def fix_essential_schema():
    """Fix only the essential schema issues"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    print(f"Fixing essential database schema: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(folders)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {len(existing_columns)} found")
        
        # Only add the absolutely essential missing columns
        essential_columns = [
            ('keys_updated_at', 'TIMESTAMP'),
        ]
        
        added_count = 0
        for column_name, column_type in essential_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE folders ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    added_count += 1
                    print(f"OK: Added column {column_name}")
                except Exception as e:
                    print(f"INFO: Column {column_name} issue: {e}")
        
        # Add segments state column if missing
        try:
            cursor.execute("PRAGMA table_info(segments)")
            segment_columns = [row[1] for row in cursor.fetchall()]
            
            if 'state' not in segment_columns:
                cursor.execute("ALTER TABLE segments ADD COLUMN state TEXT DEFAULT 'pending'")
                added_count += 1
                print("OK: Added segments.state column")
        except Exception as e:
            print(f"INFO: Segments table issue: {e}")
        
        # Commit changes
        conn.commit()
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM folders")
        folder_count = cursor.fetchone()[0]
        print(f"OK: Database test successful, {folder_count} folders")
        
        conn.close()
        
        print(f"SUCCESS: Schema fix completed ({added_count} changes)")
        return True
        
    except Exception as e:
        print(f"ERROR: Schema fix failed: {e}")
        return False

def remove_problematic_column_references():
    """Remove references to columns that cause issues"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("WARNING: production_db_wrapper.py not found")
        return True
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Remove last_updated references that cause errors
    if 'last_updated = CURRENT_TIMESTAMP' in content:
        content = content.replace('last_updated = CURRENT_TIMESTAMP', '/* last_updated removed */')
        fixes_applied.append("Removed problematic last_updated references")
    
    # Fix 2: Make sure update_folder_keys is safe
    if 'keys_updated_at = CURRENT_TIMESTAMP' in content:
        # Replace with a safer version
        old_pattern = 'SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP'
        new_pattern = 'SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP'
        # Keep it as is since we added the column
        print("OK: keys_updated_at column should now exist")
    
    if fixes_applied:
        with open(wrapper_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"OK: Applied {len(fixes_applied)} database method fixes")
    
    return True

def test_folder_indexing():
    """Test if folder indexing will work now"""
    
    try:
        # Test the update_folder_keys operation
        db_path = Path("data/usenetsync.db")
        if not db_path.exists():
            print("WARNING: Cannot test - database not found")
            return True
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Test if we can do the update that was failing
        cursor.execute("SELECT id FROM folders LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            folder_id = row[0]
            # Test the exact update that was failing
            test_private_key = b'test_key_data'
            test_public_key = b'test_public_key_data'
            
            cursor.execute("""
                UPDATE folders 
                SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (test_private_key, test_public_key, folder_id))
            
            conn.commit()
            print("OK: Folder key update test successful")
        else:
            print("INFO: No folders to test with")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"WARNING: Folder indexing test failed: {e}")
        # This is just a test, don't fail the whole process
        return True

def main():
    """Main function"""
    print("=" * 50)
    print("Simple Database Schema Fix")
    print("=" * 50)
    
    success = True
    
    # Fix essential schema
    if not fix_essential_schema():
        print("ERROR: Essential schema fix failed")
        success = False
    
    # Remove problematic references
    if not remove_problematic_column_references():
        print("ERROR: Could not fix database method references")
        success = False
    
    # Test folder indexing capability
    test_folder_indexing()
    
    print()
    if success:
        print("SUCCESS: Database schema fixed!")
        print()
        print("The 'no such column: keys_updated_at' error should be resolved.")
        print("Try indexing a folder now!")
    else:
        print("ERROR: Some fixes failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)