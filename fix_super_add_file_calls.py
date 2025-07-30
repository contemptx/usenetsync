#!/usr/bin/env python3
"""
Fix the super().add_file() calls in ProductionDatabaseManager
"""

import shutil
from pathlib import Path

def fix_super_add_file():
    """Fix super().add_file() calls that are failing"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_super_add_file')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the problematic super() calls
    fixes_applied = []
    
    # Check if there's already an add_file method that calls super()
    if 'def add_file(' in content and 'super(' in content:
        # Look for the problematic method and replace it
        import re
        
        # Find the add_file method that calls super()
        pattern = r'def add_file\(.*?\):\s*.*?return self\._monitor_operation\(\s*\'add_file\',\s*lambda: self\._retry_operation\(_add\)\s*\)'
        
        # Replace with a direct implementation
        new_add_file = '''def add_file(self, folder_id, file_path, file_hash, file_size, modified_at, version=1):
        """Add file with retry logic"""
        def _add():
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO files 
                    (folder_id, file_path, file_hash, file_size, modified_at, version, state)
                    VALUES (?, ?, ?, ?, ?, ?, 'active')
                """, (folder_id, file_path, file_hash, file_size, modified_at, version))
                conn.commit()
                return cursor.lastrowid
        
        return self._monitor_operation(
            'add_file',
            lambda: self._retry_operation(_add)
        )'''
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_add_file, content, flags=re.DOTALL)
            fixes_applied.append("Fixed add_file method to not use super()")
    
    # Also check for and fix other super() calls that might fail
    super_patterns = [
        ('super().add_file(', 'self.add_file('),
        ('super().create_file(', 'self.create_file('),
        ('super().bulk_insert_segments(', 'self.bulk_insert_segments(')
    ]
    
    for old_pattern, new_pattern in super_patterns:
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            fixes_applied.append(f"Fixed super() call: {old_pattern}")
    
    # If there's no add_file method at all, add a simple one
    if 'def add_file(' not in content:
        add_file_method = '''
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
            raise e'''
        
        # Add before close method
        if 'def close(self):' in content:
            content = content.replace('def close(self):', add_file_method + '\n\n    def close(self):')
        else:
            content += add_file_method
        
        fixes_applied.append("Added missing add_file method")
    
    # Add bulk_insert_segments if missing
    if 'def bulk_insert_segments(' not in content:
        bulk_insert_method = '''
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
            raise e'''
        
        # Add before close method
        if 'def close(self):' in content:
            content = content.replace('def close(self):', bulk_insert_method + '\n\n    def close(self):')
        else:
            content += bulk_insert_method
        
        fixes_applied.append("Added missing bulk_insert_segments method")
    
    if not fixes_applied:
        print("OK: No super() add_file issues found to fix")
        return True
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

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
    print("Fix Super add_file Calls")
    print("=" * 50)
    
    if fix_super_add_file():
        if test_syntax():
            print()
            print("SUCCESS: Super add_file calls fixed!")
            print()
            print("The 'super' object has no attribute 'add_file' error should be resolved.")
            print("Try indexing the folder again!")
            return 0
        else:
            print("ERROR: Syntax errors found")
            return 1
    else:
        print("ERROR: Could not fix super() calls")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)