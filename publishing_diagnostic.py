#!/usr/bin/env python3
"""
Diagnostic script to find the exact publishing error
"""

import os
import sys
import traceback
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def diagnose_publishing():
    """Run a minimal publishing test to find the exact error"""
    
    print("Publishing System Diagnostic")
    print("=" * 50)
    
    try:
        # Import modules
        from enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig
        from publishing_system import PublishingSystem
        
        # Look at the IndexBuilder class specifically
        print("\n1. Checking IndexBuilder class...")
        
        # Create a minimal test
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db_config = DatabaseConfig(path=db_path)
            db = EnhancedDatabaseManager(db_config)
            
            # Create test data
            folder_id = db.create_folder("test", tmpdir, "Test", "public")
            
            # Add a file with version as string (common issue)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Insert file with string version
            cursor.execute("""
                INSERT INTO files (folder_id, file_path, size, hash, version, state)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (folder_id, "test.txt", 100, "abc123", "1", "active"))
            
            file_id = cursor.lastrowid
            
            # Insert segment
            cursor.execute("""
                INSERT INTO segments (file_id, segment_index, size, hash, message_id)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, 0, 100, "seg123", "<test@example.com>"))
            
            conn.commit()
            conn.close()
            
            print("  [OK] Created test data")
            
            # Now test the publishing system's _get_folder_files method
            print("\n2. Testing _get_folder_files method...")
            
            # We need to create a minimal publishing system to test
            # Import what we need
            from enhanced_security_system import EnhancedSecuritySystem
            from simplified_binary_index import SimplifiedBinaryIndex
            
            security = EnhancedSecuritySystem(db)
            
            # Create minimal publishing config
            config = {
                'index_newsgroup': 'alt.binaries.test',
                'max_index_segments': 10
            }
            
            # We'll create a minimal IndexBuilder to test
            class TestIndexBuilder:
                def __init__(self, db, security, binary_index):
                    self.db = db
                    self.security = security
                    self.binary_index = binary_index
                    self.logger = logger
                    
                def _get_folder_files(self, folder_db_id: int, version: int):
                    """Test version of the method"""
                    files = self.db.get_folder_files(folder_db_id)
                    
                    print(f"\n  Found {len(files)} files")
                    
                    file_data = []
                    for i, file in enumerate(files):
                        print(f"\n  File {i}:")
                        print(f"    Raw version value: {repr(file.get('version'))}")
                        print(f"    Version type: {type(file.get('version'))}")
                        
                        # This is where the error likely occurs
                        try:
                            file_version = file.get('version', 1)
                            print(f"    File version: {file_version} (type: {type(file_version)})")
                            
                            # The comparison that's failing
                            if file_version <= version:
                                print(f"    Comparison {file_version} <= {version} would work")
                            else:
                                print(f"    Comparison {file_version} <= {version} would fail")
                                
                        except Exception as e:
                            print(f"    ERROR in version comparison: {e}")
                            print(f"    This is the error we're seeing!")
                            traceback.print_exc()
                            
                    return file_data
            
            # Test the method
            builder = TestIndexBuilder(db, security, SimplifiedBinaryIndex)
            
            try:
                # Call with integer version
                builder._get_folder_files(folder_id, 1)
                print("\n  [OK] Method works with integer version")
            except Exception as e:
                print(f"\n  [ERROR] Method failed: {e}")
                traceback.print_exc()
                
            # Clean up
            db.close()
            
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        traceback.print_exc()
        

def check_actual_file():
    """Check the actual publishing_system.py file"""
    
    print("\n\n3. Checking actual publishing_system.py...")
    print("-" * 50)
    
    filepath = "publishing_system.py"
    if not os.path.exists(filepath):
        print("  [ERROR] File not found")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the _get_folder_files method
    in_method = False
    method_lines = []
    
    for i, line in enumerate(lines):
        if '_get_folder_files' in line and 'def' in line:
            in_method = True
            
        if in_method:
            method_lines.append((i+1, line.rstrip()))
            
            # Stop at next method or class
            if line.strip().startswith('def ') and '_get_folder_files' not in line:
                break
            if line.strip().startswith('class '):
                break
                
    if method_lines:
        print("  Found _get_folder_files method:")
        for line_no, line in method_lines[:20]:  # Show first 20 lines
            print(f"    {line_no}: {line}")
            
        # Look for the specific comparison
        for line_no, line in method_lines:
            if '<=' in line and 'version' in line:
                print(f"\n  Found version comparison at line {line_no}:")
                print(f"    {line}")


def main():
    """Run diagnostic"""
    diagnose_publishing()
    check_actual_file()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete.")
    print("\nIf the error persists, the issue might be:")
    print("1. The version field in the database is stored as TEXT")
    print("2. The comparison is happening before type conversion")
    print("3. There's another version comparison we missed")
    print("\nRun the full test to see the exact error:")
    print("  python test_runner.py")


if __name__ == "__main__":
    main()
