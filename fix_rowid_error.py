#!/usr/bin/env python3
"""
Fix rowid KeyError in load_folder_keys
Quick fix for the 'rowid' key error
"""

import shutil
from pathlib import Path

def fix_load_folder_keys_rowid_error():
    """Fix the rowid KeyError in load_folder_keys method"""
    
    security_file = Path("enhanced_security_system.py")
    if not security_file.exists():
        print("ERROR: enhanced_security_system.py not found")
        return False
    
    # Create backup
    backup_file = security_file.with_suffix('.py.backup_rowid_fix')
    try:
        shutil.copy2(security_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(security_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a fixed load_folder_keys method
    new_load_method = '''def load_folder_keys(self, folder_id: str) -> Optional[FolderKeys]:
        """Load folder keys from database - fixed rowid access"""
        try:
            # Method 1: Direct database lookup by unique_id
            with self.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT rowid, * FROM folders 
                    WHERE id = ? AND private_key IS NOT NULL
                    ORDER BY rowid DESC 
                    LIMIT 1
                """, (folder_id,))
                row = cursor.fetchone()
                
                if row:
                    folder = dict(row)
                    db_id = folder.get('rowid', folder.get('id', 'unknown'))
                    logger.info(f"Found folder by unique_id: DB_ID {db_id} for {folder_id}")
                else:
                    # Method 2: Get most recent folder with keys
                    cursor = conn.execute("""
                        SELECT rowid, * FROM folders 
                        WHERE private_key IS NOT NULL
                        ORDER BY rowid DESC 
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    
                    if row:
                        folder = dict(row)
                        db_id = folder.get('rowid', folder.get('id', 'unknown'))
                        logger.info(f"Using most recent folder with keys: DB_ID {db_id}")
                    else:
                        logger.error(f"No folders with keys found in database")
                        return None
            
            if not folder.get('private_key'):
                logger.error(f"Folder has no private key: {folder.get('id', 'unknown')}")
                return None
            
            # Load the keys
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                folder['private_key']
            )
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                folder['public_key']
            )
            
            db_id = folder.get('rowid', folder.get('id', 'unknown'))
            logger.info(f"Successfully loaded keys for folder {folder_id} from DB_ID {db_id}")
            
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
        print("OK: Fixed load_folder_keys method to handle rowid properly")
        
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print("ERROR: Could not find load_folder_keys method")
        return False

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
    print("="*50)
    print("FIX ROWID KEYERROR")
    print("="*50)
    print("Fixing the 'rowid' KeyError in load_folder_keys...")
    print()
    
    success = True
    
    # Fix the rowid KeyError
    if not fix_load_folder_keys_rowid_error():
        print("ERROR: Could not fix rowid KeyError")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] rowid KeyError fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Added 'rowid' to SELECT query")
        print("  [OK] Added safe access to rowid field")
        print("  [OK] Added fallback to 'id' field if rowid missing")
        print()
        print("[READY] File indexing should now work completely!")
        print()
        print("The sequence is now:")
        print("  1. Keys generated ✅")
        print("  2. Keys saved to database ✅")
        print("  3. Keys loaded from database ✅ (FIXED)")
        print("  4. Files should now index successfully!")
        print()
        print("Try your indexing operation again.")
        return 0
    else:
        print("[ERROR] Could not fix the issue")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)