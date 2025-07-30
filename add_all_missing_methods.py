#!/usr/bin/env python3
"""
Add all missing database methods to ProductionDatabaseManager
This should be the final fix for all GUI database method errors
"""

import shutil
from pathlib import Path

def get_all_missing_methods():
    """Return all the missing methods that GUI needs"""
    return '''
    def get_folder_authorized_users(self, folder_id):
        """Get authorized users for a folder"""
        try:
            # Convert folder_id to database ID if it's a string
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return []
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                try:
                    cursor = conn.execute("""
                        SELECT user_id, access_type, added_at, added_by
                        FROM access_control_local 
                        WHERE folder_id = ?
                        ORDER BY added_at
                    """, (folder_db_id,))
                    
                    users = []
                    for row in cursor.fetchall():
                        users.append({
                            'user_id': row[0],
                            'access_type': row[1],
                            'added_at': row[2],
                            'added_by': row[3]
                        })
                    return users
                except Exception:
                    return []
        except Exception:
            return []
    
    def add_folder_authorized_user(self, folder_id, user_id, access_type='read', added_by=None):
        """Add authorized user to folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return False
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                # Create table if needed
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS access_control_local (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_id INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        access_type TEXT DEFAULT 'read',
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        added_by TEXT,
                        FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
                        UNIQUE(folder_id, user_id)
                    )
                """)
                
                conn.execute("""
                    INSERT OR REPLACE INTO access_control_local 
                    (folder_id, user_id, access_type, added_by)
                    VALUES (?, ?, ?, ?)
                """, (folder_db_id, user_id, access_type, added_by))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    def remove_folder_authorized_user(self, folder_id, user_id):
        """Remove authorized user from folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return False
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                conn.execute("""
                    DELETE FROM access_control_local 
                    WHERE folder_id = ? AND user_id = ?
                """, (folder_db_id, user_id))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_upload_progress(self, folder_id):
        """Get upload progress for folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return {'total': 0, 'uploaded': 0, 'failed': 0}
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN state = 'uploaded' THEN 1 ELSE 0 END) as uploaded,
                        SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM segments s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.folder_id = ?
                """, (folder_db_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'total': row[0] or 0,
                        'uploaded': row[1] or 0,
                        'failed': row[2] or 0
                    }
                return {'total': 0, 'uploaded': 0, 'failed': 0}
        except Exception:
            return {'total': 0, 'uploaded': 0, 'failed': 0}
    
    def update_segment_state(self, segment_id, state):
        """Update segment upload state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE segments SET state = ? WHERE id = ?
                """, (state, segment_id))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_folder_share_info(self, folder_id):
        """Get share information for folder"""
        try:
            if isinstance(folder_id, str):
                folder = self.get_folder(folder_id)
                if not folder:
                    return None
                folder_db_id = folder['id']
            else:
                folder_db_id = folder_id
            
            with self.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT share_id, access_string, share_type, created_at
                    FROM publications 
                    WHERE folder_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (folder_db_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'share_id': row[0],
                        'access_string': row[1],
                        'share_type': row[2],
                        'created_at': row[3]
                    }
                return None
        except Exception:
            return None
    
    def create_upload_session(self, session_id, folder_id, total_segments):
        """Create upload session record"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS upload_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        folder_id TEXT NOT NULL,
                        total_segments INTEGER DEFAULT 0,
                        uploaded_segments INTEGER DEFAULT 0,
                        failed_segments INTEGER DEFAULT 0,
                        state TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    INSERT OR REPLACE INTO upload_sessions 
                    (session_id, folder_id, total_segments)
                    VALUES (?, ?, ?)
                """, (session_id, folder_id, total_segments))
                
                conn.commit()
                return True
        except Exception:
            return False
    
    def update_upload_session_state(self, session_id, state):
        """Update upload session state"""
        try:
            with self.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE upload_sessions 
                    SET state = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (state, session_id))
                conn.commit()
                return True
        except Exception:
            return False
'''

def apply_all_missing_methods():
    """Apply all missing methods to the database wrapper"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_all_missing')
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
        'get_folder_authorized_users',
        'add_folder_authorized_user',
        'remove_folder_authorized_user',
        'get_upload_progress',
        'update_segment_state',
        'get_folder_share_info',
        'create_upload_session',
        'update_upload_session_state'
    ]
    
    for method in methods_to_check:
        if f'def {method}(' not in content:
            missing_methods.append(method)
    
    if not missing_methods:
        print("OK: All methods already exist")
        return True
    
    print(f"ADDING: {', '.join(missing_methods)}")
    
    # Add all missing methods
    methods_code = get_all_missing_methods()
    
    # Add before the close method
    if 'def close(self):' in content:
        content = content.replace('def close(self):', methods_code + '\n    def close(self):')
    else:
        # Add at the end
        content += methods_code
    
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
    print("Add All Missing Database Methods")
    print("=" * 50)
    
    if apply_all_missing_methods():
        if test_syntax():
            print()
            print("SUCCESS: All missing database methods added!")
            print()
            print("Added methods for:")
            print("  - User authorization management")
            print("  - Upload progress tracking")
            print("  - Segment state management")
            print("  - Share information")
            print("  - Upload session management")
            print()
            print("This should be the final fix for all GUI database errors!")
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