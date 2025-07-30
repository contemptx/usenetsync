#!/usr/bin/env python3
"""
Fix missing database methods needed by the GUI
Adds all missing methods to ProductionDatabaseManager
"""

import shutil
from pathlib import Path

def get_missing_gui_methods():
    """Return the missing GUI database methods"""
    return '''
    def get_folder_info(self, folder_id):
        """Get folder information by ID (string or int)"""
        with self.pool.get_connection() as conn:
            if isinstance(folder_id, str):
                cursor = conn.execute("""
                    SELECT * FROM folders WHERE folder_unique_id = ?
                """, (folder_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM folders WHERE id = ?
                """, (folder_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_folder_files(self, folder_id, offset=0, limit=None):
        """Get files in folder with pagination support"""
        with self.pool.get_connection() as conn:
            # Convert folder_id to database ID if it's a string
            if isinstance(folder_id, str):
                folder_cursor = conn.execute("""
                    SELECT id FROM folders WHERE folder_unique_id = ?
                """, (folder_id,))
                folder_row = folder_cursor.fetchone()
                if not folder_row:
                    return []
                folder_db_id = folder_row[0]
            else:
                folder_db_id = folder_id
            
            # Build query with pagination
            query = """
                SELECT * FROM files 
                WHERE folder_id = ? AND state != 'deleted'
                ORDER BY file_path
            """
            params = [folder_db_id]
            
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_folder_segments(self, folder_id):
        """Get all segments for a folder"""
        with self.pool.get_connection() as conn:
            # Convert folder_id to database ID if it's a string
            if isinstance(folder_id, str):
                folder_cursor = conn.execute("""
                    SELECT id FROM folders WHERE folder_unique_id = ?
                """, (folder_id,))
                folder_row = folder_cursor.fetchone()
                if not folder_row:
                    return []
                folder_db_id = folder_row[0]
            else:
                folder_db_id = folder_id
            
            cursor = conn.execute("""
                SELECT s.*, f.file_path, f.file_hash 
                FROM segments s
                JOIN files f ON s.file_id = f.id
                WHERE f.folder_id = ?
                ORDER BY f.file_path, s.segment_index
            """, (folder_db_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_folder(self, folder_id):
        """Remove folder and all associated data"""
        with self.pool.get_connection() as conn:
            try:
                # Convert folder_id to database ID if it's a string
                if isinstance(folder_id, str):
                    folder_cursor = conn.execute("""
                        SELECT id FROM folders WHERE folder_unique_id = ?
                    """, (folder_id,))
                    folder_row = folder_cursor.fetchone()
                    if not folder_row:
                        return False
                    folder_db_id = folder_row[0]
                else:
                    folder_db_id = folder_id
                
                # Delete in correct order due to foreign key constraints
                # 1. Delete segments (references files)
                conn.execute("""
                    DELETE FROM segments 
                    WHERE file_id IN (
                        SELECT id FROM files WHERE folder_id = ?
                    )
                """, (folder_db_id,))
                
                # 2. Delete files (references folders)
                conn.execute("""
                    DELETE FROM files WHERE folder_id = ?
                """, (folder_db_id,))
                
                # 3. Delete folder versions
                conn.execute("""
                    DELETE FROM folder_versions WHERE folder_id = ?
                """, (folder_db_id,))
                
                # 4. Delete change journal entries
                conn.execute("""
                    DELETE FROM change_journal WHERE folder_id = ?
                """, (folder_db_id,))
                
                # 5. Delete access control entries (if table exists)
                try:
                    conn.execute("""
                        DELETE FROM access_control_local WHERE folder_id = ?
                    """, (folder_db_id,))
                except Exception:
                    # Table might not exist, ignore
                    pass
                
                # 6. Delete published indexes
                conn.execute("""
                    DELETE FROM published_indexes WHERE folder_id = ?
                """, (folder_db_id,))
                
                # 7. Delete publications
                conn.execute("""
                    DELETE FROM publications WHERE folder_id = ?
                """, (folder_db_id,))
                
                # 8. Finally delete the folder
                conn.execute("""
                    DELETE FROM folders WHERE id = ?
                """, (folder_db_id,))
                
                conn.commit()
                return True
                
            except Exception as e:
                conn.rollback()
                raise e
    
    def get_indexed_folders(self):
        """Get all indexed folders with statistics"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    f.*,
                    COUNT(fi.id) as file_count,
                    COALESCE(SUM(fi.file_size), 0) as total_size
                FROM folders f
                LEFT JOIN files fi ON f.id = fi.folder_id AND fi.state != 'deleted'
                GROUP BY f.id
                ORDER BY f.display_name
            """)
            
            folders = []
            for row in cursor.fetchall():
                folder_dict = dict(row)
                folders.append(folder_dict)
            
            return folders
    
    def cleanup_old_sessions(self, days=30):
        """Clean up old upload/download sessions"""
        with self.pool.get_connection() as conn:
            # Clean upload sessions
            conn.execute("""
                DELETE FROM upload_sessions 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            # Clean download sessions if table exists
            try:
                conn.execute("""
                    DELETE FROM download_sessions 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days))
            except Exception:
                # Table might not exist
                pass
            
            conn.commit()
    
    def vacuum(self):
        """Vacuum the database to reclaim space"""
        with self.pool.get_connection() as conn:
            conn.execute("VACUUM")
    
    def analyze(self):
        """Analyze the database to update statistics"""
        with self.pool.get_connection() as conn:
            conn.execute("ANALYZE")
'''

def apply_gui_database_fix():
    """Apply the GUI database methods fix"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("❌ production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_gui_methods')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠ Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check which methods are missing
    missing_methods = []
    methods_to_check = [
        'get_folder_info',
        'get_folder_segments', 
        'remove_folder',
        'cleanup_old_sessions',
        'vacuum',
        'analyze'
    ]
    
    for method in methods_to_check:
        if f'def {method}(' not in content:
            missing_methods.append(method)
    
    # Check if get_folder_files needs to be updated for offset parameter
    needs_folder_files_update = False
    if 'def get_folder_files(' in content:
        # Check if it already supports offset
        if 'offset=' not in content or 'get_folder_files(self, folder_id, offset=' not in content:
            needs_folder_files_update = True
            missing_methods.append('get_folder_files (update for offset parameter)')
    
    if not missing_methods and not needs_folder_files_update:
        print("✓ All required GUI methods already exist")
        return True
    
    print(f"📝 Missing/updating methods: {', '.join(missing_methods)}")
    
    # Add the missing methods
    methods_code = get_missing_gui_methods()
    
    # If get_folder_files exists but needs updating, remove the old version first
    if needs_folder_files_update:
        import re
        # Remove old get_folder_files method
        pattern = r'def get_folder_files\(self, folder_id.*?(?=def |\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Find insertion point (before the close method)
    insertion_points = [
        "def close(self):",
        "def get_monitoring_stats(self):",
        "def get_all_shares(self):"
    ]
    
    inserted = False
    for point in insertion_points:
        if point in content:
            # Insert before this method
            content = content.replace(point, methods_code + '\n    ' + point)
            inserted = True
            break
    
    if not inserted:
        # Add at the end of the class
        # Find the last method and add after it
        lines = content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and lines[i].startswith('    def '):
                # Found last method, add after it
                # Find the end of this method
                j = i + 1
                while j < len(lines):
                    if lines[j].strip() == "":
                        j += 1
                        continue
                    if lines[j] and not lines[j].startswith('        ') and not lines[j].startswith('\t\t'):
                        break
                    j += 1
                
                lines.insert(j, methods_code)
                content = '\n'.join(lines)
                inserted = True
                break
    
    if not inserted:
        # Fallback: add at the very end
        content += '\n' + methods_code
    
    # Write the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added/updated {len(missing_methods)} methods in {wrapper_file}")
    return True

def main():
    """Main fix function"""
    print("=" * 60)
    print("    GUI Database Methods Fix")
    print("=" * 60)
    print()
    
    if apply_gui_database_fix():
        print()
        print("✅ GUI database methods fix completed!")
        print()
        print("Added/updated methods:")
        print("  • get_folder_info - for folder information")
        print("  • get_folder_files - with offset/limit pagination")
        print("  • get_folder_segments - for segment listing")
        print("  • remove_folder - for folder deletion")
        print("  • cleanup_old_sessions - for maintenance")
        print("  • vacuum/analyze - for database optimization")
        print()
        print("GUI should now work without database method errors!")
        return 0
    else:
        print("❌ Fix failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)