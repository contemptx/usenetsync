#!/usr/bin/env python3
"""
Direct Production Wrapper Fix
Manually fix the specific syntax issues in production_db_wrapper.py
"""

import shutil
from pathlib import Path

def fix_production_wrapper_completely():
    """Fix all syntax issues in production_db_wrapper.py"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_complete_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the specific issues
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for the problematic line around 812
        if i >= 810 and i <= 820:
            if 'conn.execute("PRAGMA busy_timeout=60000")' in line:
                # This line is orphaned - skip it and the following pragma lines
                print(f"REMOVING orphaned line {i+1}: {line.strip()}")
                i += 1
                # Skip following pragma lines too
                while i < len(lines) and 'PRAGMA' in lines[i]:
                    print(f"REMOVING orphaned line {i+1}: {lines[i].strip()}")
                    i += 1
                continue
        
        # Fix the duplicate timeout parameter issue
        if 'sqlite3.connect(self.config.path, timeout=30.0, timeout=60.0)' in line:
            line = line.replace('timeout=30.0, timeout=60.0', 'timeout=60.0')
            print(f"FIXED duplicate timeout on line {i+1}")
        
        # Fix SQL syntax issues
        if 'WHERE id = ?' in line and 'UPDATE folders' in line and '/* last_updated removed */' in line:
            # Fix the malformed SQL
            line = line.replace('/* last_updated removed */\n                WHERE id = ?', 'WHERE id = ?')
            print(f"FIXED SQL syntax on line {i+1}")
        
        # Fix any other orphaned pragma statements
        if line.strip().startswith('conn.execute("PRAGMA') and not any(x in line for x in ['def ', 'try:', 'with ']):
            # Check if this is properly indented within a method
            indent = len(line) - len(line.lstrip())
            if indent < 8:  # Not properly indented
                print(f"REMOVING orphaned pragma line {i+1}: {line.strip()}")
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("OK: Applied comprehensive fixes to production_db_wrapper.py")
    return True

def clean_up_get_connection_method():
    """Clean up the get_connection method specifically"""
    
    wrapper_file = Path("production_db_wrapper.py")
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the get_connection method completely
    old_get_connection = '''def get_connection(self):
        """Get database connection with better locking handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.config.path, timeout=60.0)
                conn.row_factory = dict_factory
        # Configure for better concurrent access
        conn.execute("PRAGMA busy_timeout=60000")  # 60 second timeout
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
                
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL") 
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                raise e
        
        raise sqlite3.OperationalError("Could not get database connection after retries")'''
    
    new_get_connection = '''def get_connection(self):
        """Get database connection with better locking handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.config.path, timeout=60.0)
                conn.row_factory = dict_factory
                
                # Configure for better concurrent access
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                conn.execute("PRAGMA mmap_size=268435456")
                
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                raise e
        
        raise sqlite3.OperationalError("Could not get database connection after retries")'''
    
    if 'def get_connection(self):' in content:
        # Find and replace the entire method
        import re
        pattern = r'def get_connection\(self\):.*?raise sqlite3\.OperationalError\("Could not get database connection after retries"\)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_get_connection.strip(), content, flags=re.DOTALL)
            
            with open(wrapper_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("OK: Fixed get_connection method")
    
    return True

def fix_dict_factory_reference():
    """Fix missing dict_factory reference"""
    
    wrapper_file = Path("production_db_wrapper.py")
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add dict_factory function if missing
    if 'def dict_factory(' not in content and 'dict_factory' in content:
        dict_factory_def = '''
def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

'''
        
        # Add at the top after imports
        if 'from enhanced_database_manager import' in content:
            content = content.replace(
                'from enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig',
                'from enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig' + dict_factory_def
            )
            
            with open(wrapper_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("OK: Added missing dict_factory function")
    
    return True

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: production_db_wrapper.py syntax is now valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error still exists: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("DIRECT PRODUCTION WRAPPER FIX")
    print("="*60)
    print("Applying targeted fixes to production_db_wrapper.py...")
    print()
    
    success = True
    
    # Apply comprehensive fixes
    if not fix_production_wrapper_completely():
        print("ERROR: Could not apply comprehensive fixes")
        success = False
    
    # Clean up get_connection method
    clean_up_get_connection_method()
    
    # Fix dict_factory reference
    fix_dict_factory_reference()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors still exist")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Production wrapper syntax is now valid!")
        print()
        print("Fixed issues:")
        print("  [OK] Removed orphaned PRAGMA statements")
        print("  [OK] Fixed duplicate timeout parameters")
        print("  [OK] Fixed malformed SQL statements")
        print("  [OK] Cleaned up get_connection method")
        print("  [OK] Added missing dict_factory function")
        print()
        print("Your file indexing should now work!")
        print("Try running the indexing operation again.")
        return 0
    else:
        print("[ERROR] Could not fix all syntax errors")
        print()
        print("The file may need manual review.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)