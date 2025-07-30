#!/usr/bin/env python3
"""
Fix database lock issues and state constraint errors
"""

import shutil
from pathlib import Path

def fix_database_issues():
    """Fix database locking and state constraint issues"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_db_lock_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Update add_file method to use correct state value
    if "VALUES (?, ?, ?, ?, ?, ?, 'active')" in content:
        content = content.replace(
            "VALUES (?, ?, ?, ?, ?, ?, 'active')",
            "VALUES (?, ?, ?, ?, ?, ?, 'indexed')"
        )
        fixes_applied.append("Fixed file state: 'active' -> 'indexed'")
    
    # Fix 2: Add better database connection handling with WAL mode
    if 'def get_connection(self):' not in content:
        better_connection_method = '''
    def get_connection(self):
        """Get database connection with better locking handling"""
        import sqlite3
        import time
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.config.path, timeout=30.0)
                conn.row_factory = dict_factory
                
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
        
        # Add before close method
        if 'def close(self):' in content:
            content = content.replace('def close(self):', better_connection_method + '\n\n    def close(self):')
        else:
            content += better_connection_method
        
        fixes_applied.append("Added better database connection handling")
    
    # Fix 3: Update add_file method to use WAL mode friendly transactions
    new_add_file = '''
    def add_file(self, folder_id, file_path, file_hash, file_size, modified_at, version=1):
        """Add file to database with better locking handling"""
        import sqlite3
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    # Use immediate transaction to reduce lock time
                    conn.execute("BEGIN IMMEDIATE")
                    try:
                        cursor = conn.execute("""
                            INSERT INTO files 
                            (folder_id, file_path, file_hash, file_size, modified_at, version, state)
                            VALUES (?, ?, ?, ?, ?, ?, 'indexed')
                        """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                        
                        file_id = cursor.lastrowid
                        conn.commit()
                        return file_id
                    except Exception:
                        conn.rollback()
                        raise
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    print(f"Database locked, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Database error after {attempt + 1} attempts: {e}")
                    raise e
        
        raise sqlite3.OperationalError(f"Failed to add file after {max_retries} attempts")'''
    
    # Replace existing add_file method
    import re
    add_file_pattern = r'def add_file\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(add_file_pattern, content, re.DOTALL):
        content = re.sub(add_file_pattern, new_add_file.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Updated add_file method with better error handling")
    
    # Fix 4: Update bulk_insert_segments to handle locking better
    new_bulk_insert = '''
    def bulk_insert_segments(self, segments):
        """Bulk insert segments with better locking"""
        import sqlite3
        import time
        
        if not segments:
            return True
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    try:
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
                        conn.commit()
                        return True
                    except Exception:
                        conn.rollback()
                        raise
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        
        return False'''
    
    # Replace existing bulk_insert_segments method
    bulk_pattern = r'def bulk_insert_segments\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    if re.search(bulk_pattern, content, re.DOTALL):
        content = re.sub(bulk_pattern, new_bulk_insert.strip(), content, flags=re.DOTALL)
        fixes_applied.append("Updated bulk_insert_segments with better locking")
    
    if not fixes_applied:
        print("OK: No database issues found to fix")
        return True
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} database fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

def optimize_database():
    """Optimize the database for better performance"""
    import sqlite3
    from pathlib import Path
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("WARNING: Database not found")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        print("Optimizing database...")
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Optimize settings
        conn.execute("PRAGMA synchronous=NORMAL") 
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        
        # Vacuum and analyze
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        
        conn.close()
        print("OK: Database optimized")
        return True
        
    except Exception as e:
        print(f"WARNING: Could not optimize database: {e}")
        return True  # Non-critical

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: Syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("Fix Database Lock and State Issues")
    print("=" * 50)
    
    success = True
    
    # Fix database code issues
    if not fix_database_issues():
        print("ERROR: Could not fix database issues")
        success = False
    
    # Optimize database
    optimize_database()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("SUCCESS: Database issues fixed!")
        print()
        print("Fixed:")
        print("  - File state constraint (active -> indexed)")
        print("  - Database locking with WAL mode")
        print("  - Better retry logic and error handling")
        print("  - Optimized database settings")
        print()
        print("Folder indexing should now work without locking errors!")
    else:
        print("ERROR: Some fixes failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)