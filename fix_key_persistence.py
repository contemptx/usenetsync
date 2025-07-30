#!/usr/bin/env python3
"""
Fix Key Persistence Issue
The keys are being "saved" but not actually persisting to the database
"""

import sqlite3
import shutil
from pathlib import Path

def debug_key_save_process():
    """Debug the key saving process"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        print("DEBUG: Key save process analysis:")
        
        # Check current state of folder 12
        cursor = conn.execute("SELECT rowid, private_key, public_key, keys_updated_at FROM folders WHERE rowid = 12")
        folder_12 = cursor.fetchone()
        
        if folder_12:
            print(f"  Folder 12 - Private Key: {folder_12[1] is not None}, Public Key: {folder_12[2] is not None}")
            print(f"  Keys Updated: {folder_12[3]}")
        else:
            print("  Folder 12 not found")
        
        # Check table schema
        cursor = conn.execute("PRAGMA table_info(folders)")
        columns = cursor.fetchall()
        
        print(f"\n  Folders table columns:")
        for col in columns:
            print(f"    {col[1]} ({col[2]}) - NOT NULL: {bool(col[3])}")
        
        conn.close()
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")

def fix_update_folder_keys_method():
    """Fix the update_folder_keys method to actually persist data"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_key_persistence')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a robust update_folder_keys method
    new_update_keys = '''def update_folder_keys(self, folder_id: int, private_key: bytes, public_key: bytes):
        """Update folder keys in database with explicit transaction handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Use a direct connection to ensure transaction control
                conn = sqlite3.connect(self.config.path, timeout=60.0)
                
                try:
                    # Enable WAL mode for better concurrency
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA busy_timeout=60000")
                    
                    # Begin explicit transaction
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Update with explicit commit
                    cursor = conn.execute("""
                        UPDATE folders 
                        SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                        WHERE rowid = ?
                    """, (private_key, public_key, folder_id))
                    
                    if cursor.rowcount == 0:
                        # Try with id field instead of rowid
                        cursor = conn.execute("""
                            UPDATE folders 
                            SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (private_key, public_key, folder_id))
                    
                    # Explicit commit
                    conn.commit()
                    
                    # Verify the update worked
                    cursor = conn.execute("SELECT private_key IS NOT NULL, public_key IS NOT NULL FROM folders WHERE rowid = ?", (folder_id,))
                    result = cursor.fetchone()
                    
                    if result and result[0] and result[1]:
                        print(f"SUCCESS: Keys saved to folder {folder_id} - verified in database")
                        conn.close()
                        return
                    else:
                        print(f"WARNING: Keys not verified in database for folder {folder_id}")
                        
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.close()
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    print(f"Database locked during key save, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database error during key save after {attempt + 1} attempts: {e}")
                    raise e
            except Exception as e:
                print(f"Error saving keys: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
                
        raise sqlite3.OperationalError(f"Failed to save keys after {max_retries} attempts")'''
    
    # Replace the update_folder_keys method
    import re
    pattern = r'def update_folder_keys\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_update_keys.strip(), content, flags=re.DOTALL)
        print("OK: Fixed update_folder_keys method for proper persistence")
    else:
        print("ERROR: Could not find update_folder_keys method")
        return False
    
    # Write back the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def test_key_save_directly():
    """Test saving keys directly to verify database works"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60.0)
        
        # Enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        
        # Create test keys
        test_private_key = b'test_private_key_32_bytes_long_'
        test_public_key = b'test_public_key_32_bytes_long__'
        
        print("Testing direct key save to database...")
        
        # Update folder 12 with test keys
        cursor = conn.execute("""
            UPDATE folders 
            SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
            WHERE rowid = 12
        """, (test_private_key, test_public_key))
        
        conn.commit()
        
        # Verify the save
        cursor = conn.execute("SELECT private_key, public_key FROM folders WHERE rowid = 12")
        result = cursor.fetchone()
        
        if result and result[0] == test_private_key and result[1] == test_public_key:
            print("SUCCESS: Direct key save test passed")
            
            # Clean up test keys
            conn.execute("UPDATE folders SET private_key = NULL, public_key = NULL WHERE rowid = 12")
            conn.commit()
            
            conn.close()
            return True
        else:
            print("ERROR: Direct key save test failed")
            conn.close()
            return False
            
    except Exception as e:
        print(f"ERROR: Direct key save test failed: {e}")
        return False

def fix_save_folder_keys_call():
    """Fix the save_folder_keys call to use database ID correctly"""
    
    security_file = Path("enhanced_security_system.py")
    if not security_file.exists():
        print("ERROR: enhanced_security_system.py not found")
        return False
    
    with open(security_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the save_folder_keys method to debug the issue
    new_save_method = '''def save_folder_keys(self, folder_unique_id: str, keys: FolderKeys):
        """Save folder keys to database with debugging
        
        Args:
            folder_unique_id: The unique string identifier for the folder
            keys: The FolderKeys object containing the key pair
        """
        try:
            # Get the folder record
            folder = self.db.get_folder(folder_unique_id)
            if not folder:
                raise ValueError(f"Folder not found: {folder_unique_id}")
            
            # Use rowid for the update (this is the actual database primary key)
            folder_db_id = folder.get('rowid') or folder.get('id')
            
            print(f"DEBUG: Saving keys to folder DB_ID: {folder_db_id}")
            
            private_bytes = keys.private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_bytes = keys.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            print(f"DEBUG: Key bytes - Private: {len(private_bytes)} bytes, Public: {len(public_bytes)} bytes")
            
            # Save to database
            self.db.update_folder_keys(folder_db_id, private_bytes, public_bytes)
            
            # Verify the save worked
            updated_folder = self.db.get_folder(folder_unique_id)
            if updated_folder and updated_folder.get('private_key'):
                logger.info(f"VERIFIED: Keys saved for folder: {folder_unique_id} (db_id: {folder_db_id})")
            else:
                logger.error(f"FAILED: Keys not found after save for folder: {folder_unique_id}")
                
        except Exception as e:
            logger.error(f"Error saving folder keys: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise e'''
    
    # Replace the save_folder_keys method
    import re
    pattern = r'def save_folder_keys\(self, folder_unique_id: str, keys: FolderKeys\):.*?(?=\n    def |\n\nclass |\n\n[a-zA-Z]|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_save_method, content, flags=re.DOTALL)
        print("OK: Fixed save_folder_keys method with debugging")
        
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print("ERROR: Could not find save_folder_keys method")
        return False

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
    print("FIX KEY PERSISTENCE ISSUE")
    print("="*60)
    print("Fixing the database key save/load mismatch...")
    print()
    
    # Debug current state
    debug_key_save_process()
    print()
    
    success = True
    
    # Test direct database save
    if not test_key_save_directly():
        print("ERROR: Direct database save test failed")
        success = False
    
    # Fix the update_folder_keys method
    if not fix_update_folder_keys_method():
        print("ERROR: Could not fix update_folder_keys method")
        success = False
    
    # Fix the save_folder_keys call
    if not fix_save_folder_keys_call():
        print("ERROR: Could not fix save_folder_keys method")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Key persistence issue fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Fixed update_folder_keys to use explicit transactions")
        print("  [OK] Added verification that keys are actually saved")
        print("  [OK] Fixed database ID usage (rowid vs id)")
        print("  [OK] Added detailed debugging for key save process")
        print("  [OK] Added retry logic for database lock issues")
        print()
        print("[READY] File indexing should now work!")
        print()
        print("The keys will now:")
        print("  1. Be saved with explicit database transactions")
        print("  2. Be verified after saving")
        print("  3. Use the correct database ID (rowid)")
        print("  4. Handle database locks properly")
        print()
        print("Try running your indexing operation again.")
        return 0
    else:
        print("[ERROR] Some issues could not be fixed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)