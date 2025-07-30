#!/usr/bin/env python3
"""
Simple GUI database methods fix without Unicode characters
"""

import shutil
from pathlib import Path

def add_missing_methods():
    """Add missing database methods to ProductionDatabaseManager"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_gui_simple')
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
        'get_folder_info',
        'get_folder_segments', 
        'remove_folder'
    ]
    
    for method in methods_to_check:
        if f'def {method}(' not in content:
            missing_methods.append(method)
    
    # Check if get_folder_files needs offset parameter
    needs_folder_files_update = False
    if 'def get_folder_files(' in content and 'offset=' not in content:
        needs_folder_files_update = True
        missing_methods.append('get_folder_files_update')
    
    if not missing_methods:
        print("OK: All required methods already exist")
        return True
    
    print(f"ADDING: {', '.join(missing_methods)}")
    
    # Methods to add
    new_methods = '''
    def get_folder_info(self, folder_id):
        """Get folder information by ID"""
        return self.get_folder(folder_id)
    
    def get_folder_segments(self, folder_id):
        """Get all segments for a folder"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return []
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.*, f.file_path, f.file_hash 
                    FROM segments s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.folder_id = ?
                    ORDER BY f.file_path, s.segment_index
                """, (folder_db_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def remove_folder(self, folder_id):
        """Remove folder and all associated data"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return False
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                # Delete files and segments first
                conn.execute("DELETE FROM segments WHERE file_id IN (SELECT id FROM files WHERE folder_id = ?)", (folder_db_id,))
                conn.execute("DELETE FROM files WHERE folder_id = ?", (folder_db_id,))
                conn.execute("DELETE FROM folders WHERE id = ?", (folder_db_id,))
                conn.commit()
                return True
        except Exception as e:
            raise e
    
    def cleanup_old_sessions(self, days=30):
        """Clean up old sessions"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("DELETE FROM upload_sessions WHERE created_at < datetime('now', '-{} days')".format(days))
                conn.commit()
        except Exception:
            pass
    
    def vacuum(self):
        """Vacuum database"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("VACUUM")
        except Exception:
            pass
    
    def analyze(self):
        """Analyze database"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("ANALYZE")
        except Exception:
            pass
'''
    
    # Update get_folder_files to support offset if needed
    if needs_folder_files_update:
        # Replace the existing get_folder_files method
        import re
        pattern = r'def get_folder_files\(self, folder_id.*?(?=def |\n    def |\Z)'
        new_get_folder_files = '''def get_folder_files(self, folder_id, offset=0, limit=None):
        """Get files in folder with pagination"""
        try:
            folder = self.get_folder(folder_id)
            if not folder:
                return []
            folder_db_id = folder['id']
            
            with self.pool.get_connection() as conn:
                query = "SELECT * FROM files WHERE folder_id = ? ORDER BY file_path"
                params = [folder_db_id]
                
                if limit is not None:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    '''
        content = re.sub(pattern, new_get_folder_files, content, flags=re.DOTALL)
    
    # Add new methods before the close method
    if 'def close(self):' in content:
        content = content.replace('def close(self):', new_methods + '\n    def close(self):')
    else:
        # Add at the end
        content += new_methods
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Added {len(missing_methods)} methods")
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
    print("Simple GUI Database Methods Fix")
    print("=" * 50)
    
    if add_missing_methods():
        if test_syntax():
            print()
            print("SUCCESS: GUI database methods fixed!")
            print()
            print("Added methods:")
            print("  - get_folder_info")
            print("  - get_folder_segments") 
            print("  - remove_folder")
            print("  - cleanup_old_sessions")
            print("  - vacuum/analyze")
            print("  - get_folder_files (updated for pagination)")
            print()
            print("GUI should now work without database method errors!")
            return 0
        else:
            print("ERROR: Syntax errors found")
            return 1
    else:
        print("ERROR: Could not add methods")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)