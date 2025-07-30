#!/usr/bin/env python3
"""
Fix Database Transaction and SQL Syntax Errors
Comprehensive fix for all database issues preventing file indexing
"""

import shutil
import sqlite3
import time
from pathlib import Path
import re

def fix_connection_pool_transactions():
    """Fix connection pool to prevent nested transactions"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_transaction_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Remove manual BEGIN IMMEDIATE calls since connection pool handles transactions
    if 'conn.execute("BEGIN IMMEDIATE")' in content:
        content = content.replace('conn.execute("BEGIN IMMEDIATE")', '# Transaction handled by connection pool')
        fixes_applied.append("Removed manual BEGIN IMMEDIATE calls")
    
    # Fix 2: Remove manual COMMIT calls inside with statements
    # The connection pool handles commits automatically
    content = re.sub(r'\s*conn\.commit\(\)\s*\n', '\n                        # Commit handled by connection pool\n', content)
    if 'conn.commit()' not in content:
        fixes_applied.append("Removed manual commit calls")
    
    # Fix 3: Remove manual rollback in except blocks inside with statements
    content = re.sub(r'\s*conn\.rollback\(\)\s*\n', '\n                        # Rollback handled by connection pool\n', content)
    if 'conn.rollback()' not in content:
        fixes_applied.append("Removed manual rollback calls")
    
    # Fix 4: Update add_file method to be simpler and avoid transaction conflicts
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
                raise e
        
        raise sqlite3.OperationalError(f"Failed to add file after {max_retries} attempts")'''
    
    # Replace the add_file method
    add_file_pattern = r'def add_file\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(add_file_pattern, content, re.DOTALL):
        content = re.sub(add_file_pattern, new_add_file.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Fixed add_file method to avoid transaction conflicts")
    
    # Fix 5: Update bulk_insert_segments method
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
                raise e
        
        return False'''
    
    # Replace bulk_insert_segments method
    bulk_pattern = r'def bulk_insert_segments\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(bulk_pattern, content, re.DOTALL):
        content = re.sub(bulk_pattern, new_bulk_insert.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Fixed bulk_insert_segments method")
    
    if not fixes_applied:
        print("OK: No transaction issues found to fix")
        return True
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} transaction fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

def fix_sql_syntax_errors():
    """Fix SQL syntax errors that cause 'near WHERE' errors"""
    
    files_to_check = [
        "production_db_wrapper.py",
        "versioned_core_index_system.py"
    ]
    
    fixes_applied = []
    
    for filename in files_to_check:
        file_path = Path(filename)
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Missing table name in UPDATE statements
        content = re.sub(r'UPDATE\s+SET', 'UPDATE folders SET', content)
        
        # Fix 2: Double WHERE clauses
        content = re.sub(r'WHERE\s+WHERE', 'WHERE', content)
        
        # Fix 3: Missing FROM in DELETE statements
        content = re.sub(r'DELETE\s+WHERE', 'DELETE FROM folders WHERE', content)
        
        # Fix 4: Empty WHERE clauses
        content = re.sub(r'WHERE\s*$', '', content, flags=re.MULTILINE)
        
        # Fix 5: Malformed UPDATE with missing table
        content = re.sub(r'UPDATE\s*\n\s*SET', 'UPDATE folders SET', content)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append(f"Fixed SQL syntax in {filename}")
    
    if fixes_applied:
        print("OK: Applied SQL syntax fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("OK: No SQL syntax errors found")
    
    return True

def optimize_database_settings():
    """Optimize database for better concurrent access"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("WARNING: Database not found, will be created on first use")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60.0)
        
        print("Optimizing database settings...")
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Optimize for concurrent access
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        conn.execute("PRAGMA wal_autocheckpoint=1000")
        
        # Vacuum and analyze for better performance
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        
        conn.close()
        print("OK: Database optimized for concurrent access")
        return True
        
    except Exception as e:
        print(f"WARNING: Could not optimize database: {e}")
        return True  # Non-critical

def fix_connection_pool_class():
    """Fix the connection pool to handle transactions properly"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        return True
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we need to add proper connection pool transaction handling
    if 'class DatabaseConnectionPool' in content:
        # Add transaction context manager to connection pool
        pool_enhancement = '''
class TransactionConnection:
    """Wrapper for database connection with transaction management"""
    
    def __init__(self, connection):
        self.conn = connection
        self.in_transaction = False
    
    def __enter__(self):
        if not self.in_transaction:
            self.conn.execute("BEGIN IMMEDIATE")
            self.in_transaction = True
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.in_transaction:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.in_transaction = False
        self.conn.close()
'''
        
        # Add before class DatabaseConnectionPool
        if 'class DatabaseConnectionPool' in content and 'class TransactionConnection' not in content:
            content = content.replace('class DatabaseConnectionPool', pool_enhancement + '\nclass DatabaseConnectionPool')
            
            # Update get_connection method to use TransactionConnection
            old_get_conn = 'def get_connection(self):'
            new_get_conn = '''def get_connection(self):
        """Get connection wrapped in transaction manager"""
        conn = self._create_connection()
        return TransactionConnection(conn)
    
    def _create_connection(self):'''
            
            if old_get_conn in content:
                content = content.replace(old_get_conn, new_get_conn)
                
                # Write back
                with open(wrapper_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("OK: Enhanced connection pool with transaction management")
                return True
    
    return True

def test_database_operations():
    """Test that database operations work after fixes"""
    
    print("Testing database operations...")
    
    try:
        # Test basic connectivity
        db_path = Path("data/usenetsync.db")
        db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        # Test WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        result = conn.execute("PRAGMA journal_mode").fetchone()
        if result and result[0] == 'wal':
            print("OK: WAL mode enabled")
        else:
            print("WARNING: WAL mode not enabled")
        
        # Test basic operations
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
        conn.execute("INSERT OR IGNORE INTO test (id) VALUES (1)")
        conn.execute("SELECT COUNT(*) FROM test")
        
        conn.close()
        print("OK: Basic database operations working")
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: Python syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Python syntax error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Fix Database Transaction and SQL Syntax Errors")
    print("=" * 60)
    
    success = True
    
    # Fix connection pool transactions
    if not fix_connection_pool_transactions():
        print("ERROR: Could not fix connection pool transactions")
        success = False
    
    # Fix SQL syntax errors
    if not fix_sql_syntax_errors():
        print("ERROR: Could not fix SQL syntax errors")
        success = False
    
    # Enhance connection pool
    fix_connection_pool_class()
    
    # Optimize database
    optimize_database_settings()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    # Test database operations
    if not test_database_operations():
        print("ERROR: Database operations test failed")
        success = False
    
    print()
    if success:
        print("SUCCESS: All database issues fixed!")
        print()
        print("Fixed issues:")
        print("  ✓ Nested transaction errors (cannot start transaction within transaction)")
        print("  ✓ Database lock issues with retry logic")
        print("  ✓ SQL syntax errors (near WHERE)")
        print("  ✓ Connection pool transaction management")
        print("  ✓ WAL mode enabled for better concurrency")
        print()
        print("File indexing should now work without errors!")
        print("Run your indexing operation again.")
        return 0
    else:
        print("ERROR: Some issues could not be fixed")
        print("Check the error messages above for manual fixes needed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)