#!/usr/bin/env python3
"""
Comprehensive fix for missing database methods in ProductionDatabaseManager
Adds all methods that the security system and indexing system need
"""

def get_missing_methods():
    """Return the missing database methods"""
    return '''
    def update_folder_keys(self, folder_id: int, private_key: bytes, public_key: bytes):
        """Update folder keys in database"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE folders 
                SET private_key = ?, public_key = ?, keys_updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (private_key, public_key, folder_id))
            conn.commit()
    
    def get_folder_by_path(self, folder_path: str) -> Optional[Dict]:
        """Get folder by file system path"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM folders WHERE folder_path = ?
            """, (folder_path,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_folder_stats(self, folder_id: int):
        """Update folder statistics"""
        with self.pool.get_connection() as conn:
            # Update file count and total size
            cursor = conn.execute("""
                UPDATE folders 
                SET file_count = (
                    SELECT COUNT(*) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                total_size = (
                    SELECT COALESCE(SUM(file_size), 0) FROM files WHERE folder_id = ? AND state != 'deleted'
                ),
                last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (folder_id, folder_id, folder_id))
            conn.commit()
    
    def get_folder_files(self, folder_id: int) -> List[Dict]:
        """Get all files in a folder"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE folder_id = ? ORDER BY file_path
            """, (folder_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_file_segments(self, file_id: int) -> List[Dict]:
        """Get all segments for a file"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM segments WHERE file_id = ? ORDER BY segment_index
            """, (file_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def create_file(self, folder_id: int, file_path: str, file_hash: str, 
                   file_size: int, version: int = 1) -> int:
        """Create new file entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO files 
                (folder_id, file_path, file_hash, file_size, version, state)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (folder_id, file_path, file_hash, file_size, version))
            conn.commit()
            return cursor.lastrowid
    
    def get_file(self, folder_id: int, file_path: str) -> Optional[Dict]:
        """Get file by folder and path"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM files WHERE folder_id = ? AND file_path = ?
            """, (folder_id, file_path))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_file_state(self, file_id: int, state: str):
        """Update file state"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                UPDATE files SET state = ?, modified_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (state, file_id))
            conn.commit()
    
    def create_segment(self, file_id: int, segment_index: int, segment_hash: str,
                      segment_size: int, data_offset: int, redundancy_index: int = 0) -> int:
        """Create new segment entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO segments 
                (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index))
            conn.commit()
            return cursor.lastrowid
    
    def record_change(self, folder_id: int, file_path: str, change_type: str,
                     old_version: Optional[int], new_version: Optional[int],
                     old_hash: Optional[str], new_hash: Optional[str]):
        """Record change in journal"""
        with self.pool.get_connection() as conn:
            conn.execute("""
                INSERT INTO change_journal 
                (folder_id, file_path, change_type, old_version, new_version, old_hash, new_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (folder_id, file_path, change_type, old_version, new_version, old_hash, new_hash))
            conn.commit()
    
    def create_folder_version(self, folder_id: int, version: int, change_data: Dict) -> int:
        """Create folder version entry"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO folder_versions 
                (folder_id, version, change_summary)
                VALUES (?, ?, ?)
            """, (folder_id, version, json.dumps(change_data)))
            conn.commit()
            return cursor.lastrowid
'''

def apply_comprehensive_fix():
    """Apply comprehensive database fix"""
    from pathlib import Path
    import shutil
    
    # Find the database wrapper file
    possible_files = [
        "production_db_wrapper.py",
        "enhanced_database_manager_production.py", 
        "enhanced_database_manager.py"
    ]
    
    wrapper_file = None
    for filename in possible_files:
        if Path(filename).exists():
            wrapper_file = Path(filename)
            break
    
    if not wrapper_file:
        print("❌ Could not find ProductionDatabaseManager file")
        return False
    
    print(f"✓ Found database wrapper: {wrapper_file}")
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_comprehensive')
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
        'update_folder_keys',
        'get_folder_by_path', 
        'update_folder_stats',
        'get_folder_files',
        'get_file_segments',
        'create_file',
        'get_file',
        'update_file_state',
        'create_segment',
        'record_change',
        'create_folder_version'
    ]
    
    for method in methods_to_check:
        if f'def {method}(' not in content:
            missing_methods.append(method)
    
    if not missing_methods:
        print("✓ All required methods already exist")
        return True
    
    print(f"📝 Missing methods: {', '.join(missing_methods)}")
    
    # Add imports if needed
    if 'import json' not in content and 'from typing import' in content:
        content = content.replace('from typing import', 'import json\nfrom typing import')
    elif 'import json' not in content:
        content = 'import json\n' + content
    
    # Add the missing methods
    methods_code = get_missing_methods()
    
    # Find insertion point (end of class)
    if "class ProductionDatabaseManager" in content:
        # Find a good insertion point
        insertion_points = [
            "def close(self):",
            "def __del__(self):",
            "def cleanup(self):",
            "def get_indexed_folders(self):"
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
            lines = content.split('\n')
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
                    # Found end of class, insert before this line
                    lines.insert(i, methods_code)
                    content = '\n'.join(lines)
                    inserted = True
                    break
            
            if not inserted:
                content += methods_code
    else:
        print("❌ Could not find ProductionDatabaseManager class")
        return False
    
    # Write the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added {len(missing_methods)} missing methods to {wrapper_file}")
    return True

def main():
    """Main fix function"""
    print("=" * 60)
    print("    Comprehensive Database Methods Fix")
    print("=" * 60)
    print()
    
    if apply_comprehensive_fix():
        print()
        print("✅ Database methods fix completed!")
        print()
        print("Added methods:")
        print("  • update_folder_keys - for security system")
        print("  • get_folder_by_path - for folder lookup")
        print("  • update_folder_stats - for statistics")
        print("  • get_folder_files - for file listing")  
        print("  • get_file_segments - for segment management")
        print("  • create_file - for indexing")
        print("  • create_segment - for segment creation")
        print("  • And more...")
        print()
        print("You can now test folder indexing:")
        print("  python test_backend_final.py")
        return 0
    else:
        print("❌ Fix failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)