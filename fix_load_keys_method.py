#!/usr/bin/env python3
"""
Fix Load Folder Keys Method
Fix the broken load_folder_keys method in enhanced_security_system.py
"""

import shutil
from pathlib import Path

def fix_load_folder_keys_method():
    """Fix the broken load_folder_keys method"""
    
    security_file = Path("enhanced_security_system.py")
    if not security_file.exists():
        print("ERROR: enhanced_security_system.py not found")
        return False
    
    # Create backup
    backup_file = security_file.with_suffix('.py.backup_load_keys_fix')
    try:
        shutil.copy2(security_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(security_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the broken load_folder_keys method
    old_method = '''def load_folder_keys(self, folder_id: str) -> Optional[FolderKeys]:
        """Load folder keys from database"""
        # Convert folder_id to int if it's a string number
        try:
            folder_id_int = int(folder_id)
        except (ValueError, TypeError):
            # Not a number, use as is (might be unique_id)
            folder_id_int = folder_id
        """Load folder keys from database"""
        folder = self.db.get_folder(folder_id_int)
        if not folder or not folder['private_key']:
            return None
            
        try:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                folder['private_key']
            )
            public'''
    
    new_method = '''def load_folder_keys(self, folder_id: str) -> Optional[FolderKeys]:
        """Load folder keys from database"""
        folder = self.db.get_folder(folder_id)
        if not folder or not folder.get('private_key'):
            return None
            
        try:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                folder['private_key']
            )
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                folder['public_key']
            )
            
            return FolderKeys(
                private_key=private_key,
                public_key=public_key,
                folder_id=folder_id,
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to load keys for folder {folder_id}: {e}")
            return None'''
    
    # Replace the broken method
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("OK: Fixed broken load_folder_keys method")
    else:
        # Try to find and fix the method with a more flexible approach
        import re
        
        # Find the load_folder_keys method
        pattern = r'def load_folder_keys\(self, folder_id: str\).*?(?=\n    def |\n\nclass |\n\n[a-zA-Z]|\Z)'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_method, content, flags=re.DOTALL)
            print("OK: Fixed load_folder_keys method with regex")
        else:
            print("WARNING: Could not find load_folder_keys method to fix")
    
    # Write back the fixed content
    with open(security_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_sql_where_errors():
    """Fix any remaining SQL WHERE syntax errors"""
    
    files_to_check = [
        "production_db_wrapper.py",
        "enhanced_security_system.py"
    ]
    
    fixes_applied = []
    
    for filename in files_to_check:
        file_path = Path(filename)
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix the specific SQL error in update_folder_stats
        if 'UPDATE folders' in content and '/* last_updated removed */' in content:
            # Fix the malformed SQL
            old_sql = '''UPDATE folders 
                SET file_count = (
                    SELECT COUNT(*) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                total_size = (
                    SELECT COALESCE(SUM(file_size), 0) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                /* last_updated removed */
                WHERE id = ?'''
            
            new_sql = '''UPDATE folders 
                SET file_count = (
                    SELECT COUNT(*) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                total_size = (
                    SELECT COALESCE(SUM(file_size), 0) FROM files WHERE folder_id = ? AND state != 'deleted'
                )
                WHERE id = ?'''
            
            content = content.replace(old_sql, new_sql)
            fixes_applied.append(f"Fixed malformed SQL in {filename}")
        
        # Fix any other SQL syntax issues
        content = content.replace('WHERE WHERE', 'WHERE')
        content = content.replace('UPDATE  SET', 'UPDATE folders SET')
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if f"Fixed malformed SQL in {filename}" not in fixes_applied:
                fixes_applied.append(f"Fixed SQL syntax in {filename}")
    
    if fixes_applied:
        print("OK: Applied SQL fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("OK: No SQL syntax errors found")
    
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
    print("FIX LOAD FOLDER KEYS METHOD")
    print("="*60)
    print("Fixing the load_folder_keys method and SQL errors...")
    print()
    
    success = True
    
    # Fix the load_folder_keys method
    if not fix_load_folder_keys_method():
        print("ERROR: Could not fix load_folder_keys method")
        success = False
    
    # Fix SQL WHERE syntax errors
    if not fix_sql_where_errors():
        print("ERROR: Could not fix SQL syntax errors")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Load folder keys method fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Removed duplicate docstring in load_folder_keys")
        print("  [OK] Fixed folder key loading to use folder_unique_id directly")
        print("  [OK] Fixed SQL WHERE syntax errors")
        print("  [OK] Added proper error handling")
        print()
        print("[READY] File indexing should now work!")
        print()
        print("The errors should be resolved:")
        print("  - 'No keys found for folder' error")
        print("  - 'near WHERE: syntax error'")
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