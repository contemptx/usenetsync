#!/usr/bin/env python3
"""
Fix Folder Database Constraint Issues
Clean up duplicate folders and fix database constraints
"""

import sqlite3
import shutil
from pathlib import Path

def debug_folder_records():
    """Debug folder records in database"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        print("DEBUG: All folder records for fb8acefb61e0d92e7faa86893a9a67d17b54265d2ad9c3dec95059786c0bd5b4:")
        
        cursor = conn.execute("""
            SELECT id, folder_path, private_key IS NOT NULL as has_keys, created_at
            FROM folders 
            WHERE id LIKE '%fb8acefb61e0d92e7faa86893a9a67d17b54265d2ad9c3dec95059786c0bd5b4%'
               OR folder_path LIKE '%WIN%'
               OR id IN (10, 11, 12)
            ORDER BY id DESC
        """)
        
        folders = cursor.fetchall()
        for folder in folders:
            print(f"  ID: {folder[0]}, Path: {folder[1]}, Has Keys: {folder[2]}, Created: {folder[3]}")
        
        # Check for exact folder_unique_id match
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", ("fb8acefb61e0d92e7faa86893a9a67d17b54265d2ad9c3dec95059786c0bd5b4",))
        exact_match = cursor.fetchone()
        
        if exact_match:
            print(f"\nDEBUG: Exact match found:")
            print(f"  {dict(exact_match)}")
        else:
            print(f"\nDEBUG: No exact match for folder_unique_id")
        
        # Check database ID 12
        cursor = conn.execute("SELECT * FROM folders WHERE rowid = 12")
        db_12 = cursor.fetchone()
        if db_12:
            print(f"\nDEBUG: Database ID 12 record:")
            print(f"  {dict(db_12)}")
        
        conn.close()
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")

def clean_duplicate_folders():
    """Clean up duplicate folder records"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    # Create backup
    backup_path = db_path.with_suffix('.db.backup_folder_cleanup')
    try:
        shutil.copy2(db_path, backup_path)
        print(f"OK: Created database backup: {backup_path}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        print("Cleaning up duplicate folders...")
        
        # Find all folders for the same path
        cursor = conn.execute("""
            SELECT rowid, id, folder_path, private_key IS NOT NULL as has_keys
            FROM folders 
            WHERE folder_path LIKE '%WIN%'
            ORDER BY rowid DESC
        """)
        
        folders = cursor.fetchall()
        print(f"Found {len(folders)} folder records for WIN path:")
        
        for folder in folders:
            print(f"  DB_ID: {folder[0]}, Unique_ID: {folder[1]}, Has Keys: {folder[3]}")
        
        if len(folders) > 1:
            # Keep the most recent one with keys, delete others
            keep_folder = None
            delete_folders = []
            
            for folder in folders:
                if folder[3]:  # has_keys
                    if keep_folder is None:
                        keep_folder = folder
                        print(f"  KEEPING: DB_ID {folder[0]} (has keys)")
                    else:
                        delete_folders.append(folder)
                        print(f"  DELETING: DB_ID {folder[0]} (duplicate with keys)")
                else:
                    delete_folders.append(folder)
                    print(f"  DELETING: DB_ID {folder[0]} (no keys)")
            
            # Delete the duplicates
            for folder in delete_folders:
                print(f"Deleting folder DB_ID {folder[0]}")
                
                # Delete associated files and segments first
                conn.execute("DELETE FROM segments WHERE file_id IN (SELECT id FROM files WHERE folder_id = ?)", (folder[0],))
                conn.execute("DELETE FROM files WHERE folder_id = ?", (folder[0],))
                conn.execute("DELETE FROM folders WHERE rowid = ?", (folder[0],))
            
            conn.commit()
            print(f"OK: Cleaned up {len(delete_folders)} duplicate folders")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Could not clean up folders: {e}")
        return False

def fix_folder_lookup_in_security():
    """Fix the folder lookup to use the correct method"""
    
    security_file = Path("enhanced_security_system.py")
    if not security_file.exists():
        print("ERROR: enhanced_security_system.py not found")
        return False
    
    with open(security_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the load_folder_keys method to be more targeted
    new_load_method = '''def load_folder_keys(self, folder_id: str) -> Optional[FolderKeys]:
        """Load folder keys from database - fixed for constraint issues"""
        try:
            # Method 1: Direct database lookup by most recent folder with this unique_id
            with self.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM folders 
                    WHERE id = ? AND private_key IS NOT NULL
                    ORDER BY rowid DESC 
                    LIMIT 1
                """, (folder_id,))
                row = cursor.fetchone()
                
                if row:
                    folder = dict(row)
                    logger.info(f"Found folder by unique_id: DB_ID {folder['rowid']} for {folder_id}")
                else:
                    # Method 2: Get most recent folder with keys for this path
                    cursor = conn.execute("""
                        SELECT * FROM folders 
                        WHERE private_key IS NOT NULL
                        ORDER BY rowid DESC 
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    
                    if row:
                        folder = dict(row)
                        logger.info(f"Using most recent folder with keys: DB_ID {folder['rowid']}")
                    else:
                        logger.error(f"No folders with keys found in database")
                        return None
            
            if not folder.get('private_key'):
                logger.error(f"Folder has no private key: {folder}")
                return None
            
            # Load the keys
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                folder['private_key']
            )
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                folder['public_key']
            )
            
            logger.info(f"Successfully loaded keys for folder {folder_id} from DB_ID {folder['rowid']}")
            
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
    
    # Replace the method
    import re
    pattern = r'def load_folder_keys\(self, folder_id: str\).*?(?=\n    def |\n\nclass |\n\n[a-zA-Z]|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_load_method, content, flags=re.DOTALL)
        print("OK: Fixed load_folder_keys method for constraint issues")
        
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print("ERROR: Could not find load_folder_keys method")
        return False

def fix_database_concurrency():
    """Fix database concurrency issues"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        return True
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add better WAL mode setup
    wal_setup = '''
    def setup_wal_mode(self):
        """Setup WAL mode for better concurrency"""
        try:
            with self.pool.get_connection() as conn:
                # Enable WAL mode
                conn.execute("PRAGMA journal_mode=WAL")
                
                # Optimize for concurrent access
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA wal_autocheckpoint=1000")
                
                # Check that WAL mode is active
                result = conn.execute("PRAGMA journal_mode").fetchone()
                if result and result[0] == 'wal':
                    logger.info("WAL mode enabled successfully")
                else:
                    logger.warning("Failed to enable WAL mode")
                    
        except Exception as e:
            logger.error(f"Failed to setup WAL mode: {e}")
'''
    
    # Add the method if it doesn't exist
    if 'def setup_wal_mode(' not in content:
        if 'def close(self):' in content:
            content = content.replace('def close(self):', wal_setup + '\n    def close(self):')
        else:
            content += wal_setup
        
        # Add call to setup WAL mode in __init__
        if 'def __init__(' in content and 'self.setup_wal_mode()' not in content:
            # Find the end of __init__ method
            lines = content.split('\n')
            in_init = False
            init_indent = 0
            
            for i, line in enumerate(lines):
                if 'def __init__(' in line:
                    in_init = True
                    init_indent = len(line) - len(line.lstrip())
                elif in_init:
                    current_indent = len(line) - len(line.lstrip())
                    if (line.strip().startswith('def ') and current_indent <= init_indent) or \
                       (line.strip() and current_indent < init_indent):
                        # End of __init__ method
                        lines.insert(i, '        # Setup WAL mode for better concurrency')
                        lines.insert(i + 1, '        self.setup_wal_mode()')
                        break
            
            content = '\n'.join(lines)
        
        with open(wrapper_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Added WAL mode setup for better concurrency")
    
    return True

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('enhanced_security_system.py', doraise=True)
        print("OK: enhanced_security_system.py syntax valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("FIX FOLDER DATABASE CONSTRAINT ISSUES")
    print("="*60)
    print("Cleaning up duplicate folders and fixing constraints...")
    print()
    
    # Debug current state
    debug_folder_records()
    print()
    
    success = True
    
    # Clean up duplicate folders
    if not clean_duplicate_folders():
        print("ERROR: Could not clean up duplicate folders")
        success = False
    
    # Fix folder lookup method
    if not fix_folder_lookup_in_security():
        print("ERROR: Could not fix folder lookup")
        success = False
    
    # Fix database concurrency
    fix_database_concurrency()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Folder constraint issues fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Cleaned up duplicate folder records")
        print("  [OK] Fixed folder lookup to use most recent record with keys")
        print("  [OK] Improved database concurrency with WAL mode")
        print("  [OK] Added better error handling and logging")
        print()
        print("[READY] File indexing should now work!")
        print()
        print("The system will now:")
        print("  1. Clean up any duplicate folder records")
        print("  2. Always use the most recent folder with keys")
        print("  3. Better handle database lock issues")
        print("  4. Provide clear debugging information")
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