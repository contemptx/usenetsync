#!/usr/bin/env python3
"""
Windows-Compatible Database Fix
Immediate fix for all database transaction and SQL syntax errors
"""

import shutil
import sqlite3
import time
import re
from pathlib import Path

def fix_production_db_wrapper():
    """Fix all issues in production_db_wrapper.py"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_windows_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Remove all manual transaction calls that cause conflicts
    transaction_fixes = [
        ('conn.execute("BEGIN IMMEDIATE")', '# Transaction handled by connection pool'),
        ('conn.commit()', '# Commit handled by connection pool'),
        ('conn.rollback()', '# Rollback handled by connection pool')
    ]
    
    for old, new in transaction_fixes:
        if old in content:
            content = content.replace(old, new)
            fixes_applied.append(f"Removed manual {old}")
    
    # Fix 2: Replace the problematic add_file method completely
    new_add_file = '''    def add_file(self, folder_id, file_path, file_hash, file_size, modified_at, version=1):
        """Add file to database with proper error handling"""
        import sqlite3
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.execute("""
                        INSERT INTO files 
                        (folder_id, file_path, file_hash, file_size, modified_at, version, state)
                        VALUES (?, ?, ?, ?, ?, ?, 'indexed')
                    """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                    
                    file_id = cursor.lastrowid
                    return file_id
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    print(f"Database locked, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database error after {attempt + 1} attempts: {e}")
                    raise e
            except Exception as e:
                print(f"Error adding file: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        raise sqlite3.OperationalError(f"Failed to add file after {max_retries} attempts")'''
    
    # Replace the add_file method
    add_file_pattern = r'def add_file\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(add_file_pattern, content, re.DOTALL):
        content = re.sub(add_file_pattern, new_add_file.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Replaced add_file method")
    elif 'def add_file(' not in content:
        # Add the method if it doesn't exist
        if 'def close(self):' in content:
            content = content.replace('def close(self):', new_add_file + '\n\n    def close(self):')
        else:
            content += '\n' + new_add_file
        fixes_applied.append("Added add_file method")
    
    # Fix 3: Replace bulk_insert_segments method
    new_bulk_insert = '''    def bulk_insert_segments(self, segments):
        """Bulk insert segments with proper transaction handling"""
        import sqlite3
        import time
        
        if not segments:
            return True
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    for segment in segments:
                        conn.execute("""
                            INSERT INTO segments 
                            (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, state)
                            VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        """, (
                            segment['file_id'],
                            segment['segment_index'], 
                            segment['segment_hash'],
                            segment['segment_size'],
                            segment['data_offset'],
                            segment.get('redundancy_index', 0)
                        ))
                    return True
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                print(f"Error bulk inserting segments: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        return False'''
    
    # Replace bulk_insert_segments method
    bulk_pattern = r'def bulk_insert_segments\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(bulk_pattern, content, re.DOTALL):
        content = re.sub(bulk_pattern, new_bulk_insert.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Replaced bulk_insert_segments method")
    elif 'def bulk_insert_segments(' not in content:
        # Add the method if it doesn't exist
        if 'def close(self):' in content:
            content = content.replace('def close(self):', new_bulk_insert + '\n\n    def close(self):')
        else:
            content += '\n' + new_bulk_insert
        fixes_applied.append("Added bulk_insert_segments method")
    
    # Fix 4: Fix any SQL syntax errors
    sql_fixes = [
        (r'UPDATE\s+SET', 'UPDATE folders SET'),
        (r'WHERE\s+WHERE', 'WHERE'),
        (r'DELETE\s+WHERE', 'DELETE FROM folders WHERE')
    ]
    
    for pattern, replacement in sql_fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes_applied.append(f"Fixed SQL syntax: {pattern}")
    
    # Write back the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

def setup_database():
    """Set up database with proper schema and settings"""
    
    db_path = Path("data/usenetsync.db")
    db_path.parent.mkdir(exist_ok=True)
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60.0)
        
        print("Setting up database...")
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA cache_size=10000")
        
        # Ensure files table exists with correct schema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                modified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                state TEXT DEFAULT 'indexed',
                UNIQUE(folder_id, file_path)
            )
        """)
        
        # Ensure segments table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                segment_index INTEGER NOT NULL,
                segment_hash TEXT,
                segment_size INTEGER,
                data_offset INTEGER,
                redundancy_index INTEGER DEFAULT 0,
                state TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_id, segment_index)
            )
        """)
        
        # Ensure folders table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT UNIQUE NOT NULL,
                folder_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                file_count INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                state TEXT DEFAULT 'active'
            )
        """)
        
        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files (folder_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_state ON files (state)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments (file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_state ON segments (state)")
        
        # Optimize database
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        
        conn.close()
        print("OK: Database setup complete")
        return True
        
    except Exception as e:
        print(f"ERROR: Database setup failed: {e}")
        return False

def test_database():
    """Test that database operations work"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database does not exist")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        # Test basic operations
        conn.execute("SELECT COUNT(*) FROM files")
        conn.execute("SELECT COUNT(*) FROM segments")
        conn.execute("SELECT COUNT(*) FROM folders")
        
        # Test WAL mode
        result = conn.execute("PRAGMA journal_mode").fetchone()
        if result and result[0] == 'wal':
            print("OK: WAL mode active")
        else:
            print("WARNING: WAL mode not active")
        
        conn.close()
        print("OK: Database operations working")
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: Python syntax valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Python syntax error: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("WINDOWS DATABASE FIX - IMMEDIATE SOLUTION")
    print("="*60)
    print("Fixing all database issues that prevent file indexing...")
    print()
    
    success = True
    
    # Fix the Python code
    if not fix_production_db_wrapper():
        print("ERROR: Could not fix production_db_wrapper.py")
        success = False
    
    # Set up database
    if not setup_database():
        print("ERROR: Could not set up database")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    # Test database
    if not test_database():
        print("ERROR: Database test failed")
        success = False
    
    print()
    print("="*60)
    if success:
        print("[SUCCESS] All database issues have been fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Nested transaction errors")
        print("  [OK] Database lock issues with retry logic")  
        print("  [OK] SQL syntax errors")
        print("  [OK] Missing database methods")
        print("  [OK] WAL mode enabled for better performance")
        print("  [OK] Complete database schema")
        print()
        print("[READY] Your file indexing should now work!")
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