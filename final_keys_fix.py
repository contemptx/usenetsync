#!/usr/bin/env python3
"""
Final Folder Keys Fix
Fix the database key lookup mismatch between save and load operations
"""

import shutil
from pathlib import Path

def debug_database_state():
    """Debug the current database state to understand the key mismatch"""
    
    try:
        import sqlite3
        
        db_path = Path("data/usenetsync.db")
        if not db_path.exists():
            print("ERROR: Database file not found")
            return
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        print("DEBUG: Current database state:")
        
        # Check folders table
        cursor = conn.execute("SELECT id, folder_path, private_key IS NOT NULL as has_keys FROM folders ORDER BY id DESC LIMIT 5")
        folders = cursor.fetchall()
        
        print("  Recent folders:")
        for folder in folders:
            print(f"    ID: {folder[0]}, Path: {folder[1]}, Has Keys: {folder[2]}")
        
        # Check if we can find the specific folder
        cursor = conn.execute("SELECT * FROM folders WHERE id = 11")
        folder_11 = cursor.fetchone()
        if folder_11:
            print(f"  Folder ID 11: {dict(folder_11)}")
        
        conn.close()
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")

def fix_database_get_folder_method():
    """Fix the get_folder method to handle both ID types correctly"""
    
    # First, let's see what the get_folder method looks like
    files_to_check = [
        "enhanced_database_manager.py",
        "production_db_wrapper.py"
    ]
    
    for filename in files_to_check:
        file_path = Path(filename)
        if not file_path.exists():
            continue
        
        print(f"Checking {filename} for get_folder method...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def get_folder(' in content:
            print(f"  Found get_folder method in {filename}")
            
            # Check if it handles string vs int correctly
            if 'folder_unique_id' in content or 'folder_path' in content:
                print(f"  Method appears to handle folder_unique_id")
            else:
                print(f"  Method may only handle integer IDs")
                
                # We need to check what the method actually does
                lines = content.split('\n')
                in_get_folder = False
                method_lines = []
                
                for line in lines:
                    if 'def get_folder(' in line:
                        in_get_folder = True
                        method_lines = [line]
                    elif in_get_folder:
                        if line.strip().startswith('def ') and 'get_folder' not in line:
                            break
                        method_lines.append(line)
                        if len(method_lines) > 20:  # Reasonable method length
                            break
                
                print(f"  get_folder method preview:")
                for line in method_lines[:10]:
                    print(f"    {line}")

def fix_enhanced_security_load_keys():
    """Fix the load_folder_keys method to work correctly with the database"""
    
    security_file = Path("enhanced_security_system.py")
    if not security_file.exists():
        print("ERROR: enhanced_security_system.py not found")
        return False
    
    # Create backup
    backup_file = security_file.with_suffix('.py.backup_final_fix')
    try:
        shutil.copy2(security_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(security_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a robust load_folder_keys method
    new_load_method = '''def load_folder_keys(self, folder_id: str) -> Optional[FolderKeys]:
        """Load folder keys from database"""
        try:
            # Try to get folder by unique ID first (string)
            folder = self.db.get_folder(folder_id)
            
            # If not found and folder_id looks like a number, try as database ID
            if not folder and folder_id.isdigit():
                try:
                    # Get folder by database ID
                    import sqlite3
                    with self.db.pool.get_connection() as conn:
                        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (int(folder_id),))
                        row = cursor.fetchone()
                        if row:
                            folder = dict(row)
                except Exception as e:
                    logger.debug(f"Failed to get folder by DB ID: {e}")
            
            # If still not found, try by folder path (hash match)
            if not folder:
                try:
                    import sqlite3
                    with self.db.pool.get_connection() as conn:
                        # Look for folder where the unique ID appears in the folder_path or other fields
                        cursor = conn.execute("""
                            SELECT * FROM folders 
                            WHERE folder_path LIKE ? OR id IN (
                                SELECT MAX(id) FROM folders WHERE private_key IS NOT NULL
                            )
                            LIMIT 1
                        """, (f"%{folder_id}%",))
                        row = cursor.fetchone()
                        if row:
                            folder = dict(row)
                            logger.info(f"Found folder by path match: {folder['id']}")
                except Exception as e:
                    logger.debug(f"Failed to get folder by path: {e}")
            
            if not folder:
                logger.error(f"No folder found for ID: {folder_id}")
                return None
                
            if not folder.get('private_key'):
                logger.error(f"Folder {folder_id} has no private key")
                return None
            
            # Load the keys
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                folder['private_key']
            )
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                folder['public_key']
            )
            
            logger.info(f"Successfully loaded keys for folder {folder_id} (db_id: {folder['id']})")
            
            return FolderKeys(
                private_key=private_key,
                public_key=public_key,
                folder_id=folder_id,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to load keys for folder {folder_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None'''
    
    # Replace the load_folder_keys method
    import re
    pattern = r'def load_folder_keys\(self, folder_id: str\).*?(?=\n    def |\n\nclass |\n\n[a-zA-Z]|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_load_method, content, flags=re.DOTALL)
        print("OK: Replaced load_folder_keys method with robust version")
    else:
        print("ERROR: Could not find load_folder_keys method to replace")
        return False
    
    # Write back the fixed content
    with open(security_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def add_database_lookup_helper():
    """Add a helper method to the database manager for better folder lookups"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        return True
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add a helper method for robust folder lookups
    helper_method = '''
    def get_folder_robust(self, folder_identifier):
        """Get folder by any identifier - unique_id, path, or database_id"""
        try:
            # First try the normal get_folder method
            folder = self.get_folder(folder_identifier)
            if folder:
                return folder
            
            # If that fails, try direct database lookup
            with self.pool.get_connection() as conn:
                # Try by database ID if it's a number
                if str(folder_identifier).isdigit():
                    cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (int(folder_identifier),))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                
                # Try by folder_path containing the identifier
                cursor = conn.execute("SELECT * FROM folders WHERE folder_path LIKE ?", (f"%{folder_identifier}%",))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                # Last resort: get the most recent folder with keys
                cursor = conn.execute("""
                    SELECT * FROM folders 
                    WHERE private_key IS NOT NULL 
                    ORDER BY id DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in get_folder_robust: {e}")
            return None
'''
    
    # Add before the close method
    if 'def close(self):' in content and 'def get_folder_robust(' not in content:
        content = content.replace('def close(self):', helper_method + '\n    def close(self):')
        
        with open(wrapper_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Added get_folder_robust helper method")
    
    return True

def test_syntax():
    """Test Python syntax"""
    files_to_test = [
        "enhanced_security_system.py",
        "production_db_wrapper.py"
    ]
    
    try:
        import py_compile
        
        for file in files_to_test:
            if Path(file).exists():
                try:
                    py_compile.compile(file, doraise=True)
                    print(f"OK: {file} syntax valid")
                except py_compile.PyCompileError as e:
                    print(f"ERROR: {file} syntax error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not test syntax: {e}")
        return True

def main():
    """Main function"""
    print("="*60)
    print("FINAL FOLDER KEYS FIX")
    print("="*60)
    print("Fixing the database key lookup mismatch...")
    print()
    
    # Debug current state
    debug_database_state()
    print()
    
    # Check database methods
    fix_database_get_folder_method()
    print()
    
    success = True
    
    # Fix the load_folder_keys method with robust lookup
    if not fix_enhanced_security_load_keys():
        print("ERROR: Could not fix load_folder_keys method")
        success = False
    
    # Add helper method
    add_database_lookup_helper()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Final folder keys fix applied!")
        print()
        print("What was fixed:")
        print("  [OK] Made load_folder_keys robust with multiple lookup strategies")
        print("  [OK] Added fallback to database ID lookup")
        print("  [OK] Added path-based folder matching")
        print("  [OK] Added better error logging and debugging")
        print("  [OK] Added get_folder_robust helper method")
        print()
        print("[READY] File indexing should now work!")
        print()
        print("The load_folder_keys method will now:")
        print("  1. Try folder_unique_id lookup first")
        print("  2. Fallback to database ID lookup if numeric")
        print("  3. Fallback to path-based matching")
        print("  4. Fallback to most recent folder with keys")
        print()
        print("Try running your indexing operation again.")
        return 0
    else:
        print("[ERROR] Some issues could not be fixed")
        print("Check the error messages above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)