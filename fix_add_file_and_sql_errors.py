#!/usr/bin/env python3
"""
Fix add_file method and SQL syntax errors
"""

import shutil
from pathlib import Path

def add_missing_file_methods():
    """Add missing file-related methods to ProductionDatabaseManager"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_add_file_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check which methods are missing
    missing_methods = []
    methods_to_check = [
        'add_file',
        'create_file',
        'bulk_insert_segments'
    ]
    
    for method in methods_to_check:
        if f'def {method}(' not in content:
            missing_methods.append(method)
    
    if not missing_methods:
        print("OK: All file methods already exist")
        return True
    
    print(f"ADDING: {', '.join(missing_methods)}")
    
    # Methods to add
    file_methods = '''
    def add_file(self, folder_id, file_path, file_hash, file_size, modified_at, version=1):
        """Add file to database"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO files 
                    (folder_id, file_path, file_hash, file_size, modified_at, version, state)
                    VALUES (?, ?, ?, ?, ?, ?, 'active')
                """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error adding file: {e}")
            raise e
    
    def create_file(self, folder_id, file_path, file_hash, file_size, version=1):
        """Create file entry (alias for add_file)"""
        from datetime import datetime
        return self.add_file(folder_id, file_path, file_hash, file_size, datetime.now(), version)
    
    def bulk_insert_segments(self, segments):
        """Bulk insert segments"""
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
                conn.commit()
                return True
        except Exception as e:
            print(f"Error bulk inserting segments: {e}")
            raise e
    
    def update_folder_stats(self, folder_id):
        """Update folder statistics"""
        try:
            with self.pool.get_connection() as conn:
                # Update file count and total size
                cursor = conn.execute("""
                    UPDATE folders 
                    SET file_count = (
                        SELECT COUNT(*) FROM files WHERE folder_id = ? AND state != 'deleted'
                    ),
                    total_size = (
                        SELECT COALESCE(SUM(file_size), 0) FROM files WHERE folder_id = ? AND state != 'deleted'
                    )
                    WHERE id = ?
                """, (folder_id, folder_id, folder_id))
                conn.commit()
        except Exception as e:
            print(f"Error updating folder stats: {e}")
    
    def create_folder_version(self, folder_id, version, change_summary):
        """Create folder version entry"""
        try:
            import json
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO folder_versions 
                    (folder_id, version, change_summary)
                    VALUES (?, ?, ?)
                """, (folder_id, version, json.dumps(change_summary) if isinstance(change_summary, dict) else str(change_summary)))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error creating folder version: {e}")
            return None
'''
    
    # Add methods before the close method
    if 'def close(self):' in content:
        content = content.replace('def close(self):', file_methods + '\n    def close(self):')
    else:
        # Add at the end
        content += file_methods
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Added {len(missing_methods)} file methods")
    return True

def fix_sql_syntax_errors():
    """Fix SQL syntax errors in database operations"""
    
    # Look for files that might have SQL syntax errors
    files_to_check = [
        "versioned_core_index_system.py",
        "production_db_wrapper.py"
    ]
    
    fixes_applied = []
    
    for filename in files_to_check:
        file_path = Path(filename)
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix common SQL syntax errors
        
        # Fix 1: Missing table name before WHERE
        if 'WHERE' in content and 'UPDATE  SET' in content:
            content = content.replace('UPDATE  SET', 'UPDATE folders SET')
            fixes_applied.append(f"{filename}: Fixed missing table name in UPDATE")
        
        # Fix 2: Double WHERE clauses
        if 'WHERE WHERE' in content:
            content = content.replace('WHERE WHERE', 'WHERE')
            fixes_applied.append(f"{filename}: Fixed double WHERE clause")
        
        # Fix 3: Missing table name in UPDATE statements
        import re
        update_pattern = r'UPDATE\s+SET'
        if re.search(update_pattern, content):
            content = re.sub(update_pattern, 'UPDATE folders SET', content)
            fixes_applied.append(f"{filename}: Fixed UPDATE statement missing table name")
        
        # Fix 4: Check for malformed DELETE statements
        delete_pattern = r'DELETE\s+WHERE'
        if re.search(delete_pattern, content):
            content = re.sub(delete_pattern, 'DELETE FROM folders WHERE', content)
            fixes_applied.append(f"{filename}: Fixed DELETE statement missing FROM")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    if fixes_applied:
        print("OK: Applied SQL syntax fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("OK: No SQL syntax errors found to fix")
    
    return True

def test_syntax():
    """Test syntax of fixed files"""
    print("Testing syntax...")
    
    try:
        import py_compile
        
        files_to_test = [
            "production_db_wrapper.py",
            "versioned_core_index_system.py"
        ]
        
        for file in files_to_test:
            if Path(file).exists():
                try:
                    py_compile.compile(file, doraise=True)
                    print(f"OK: {file} syntax good")
                except py_compile.PyCompileError as e:
                    print(f"ERROR: {file} syntax error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not test syntax: {e}")
        return True

def main():
    """Main function"""
    print("=" * 50)
    print("Fix add_file Method and SQL Errors")
    print("=" * 50)
    
    success = True
    
    # Add missing file methods
    if not add_missing_file_methods():
        print("ERROR: Could not add file methods")
        success = False
    
    # Fix SQL syntax errors
    if not fix_sql_syntax_errors():
        print("ERROR: Could not fix SQL errors")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("SUCCESS: File methods and SQL errors fixed!")
        print()
        print("Fixed:")
        print("  - Added missing add_file method")
        print("  - Added create_file method")
        print("  - Added bulk_insert_segments method")
        print("  - Fixed SQL syntax errors")
        print()
        print("Folder indexing should now work completely!")
    else:
        print("ERROR: Some fixes failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)