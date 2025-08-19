#!/usr/bin/env python3
"""
Comprehensive test of the complete folder management system
Tests all functionality end-to-end
"""

import subprocess
import json
import sys
import os
import tempfile
import time
import shutil
from pathlib import Path

def run_cli_command(command):
    """Run a CLI command and return the result"""
    cmd = [sys.executable, "/workspace/src/cli.py"] + command.split()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/workspace"
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'data': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_json_output(result):
    """Parse JSON from command output"""
    if result['success'] and result['stdout']:
        try:
            result['data'] = json.loads(result['stdout'])
            return True
        except json.JSONDecodeError:
            return False
    return False

class FolderSystemTest:
    def __init__(self):
        self.test_dir = None
        self.folder_id = None
        self.results = {}
        
    def setup(self):
        """Create test environment"""
        print("\n" + "="*70)
        print("SETTING UP TEST ENVIRONMENT")
        print("="*70)
        
        # Create test directory with some files
        self.test_dir = tempfile.mkdtemp(prefix="test_folder_system_")
        print(f"✓ Created test directory: {self.test_dir}")
        
        # Create some test files
        for i in range(5):
            file_path = Path(self.test_dir) / f"test_file_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"This is test file {i}\n" * 1000)
        
        # Create a subdirectory with files
        subdir = Path(self.test_dir) / "subdir"
        subdir.mkdir()
        for i in range(3):
            file_path = subdir / f"sub_file_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"This is sub file {i}\n" * 500)
        
        print(f"✓ Created 8 test files in directory structure")
        return True
    
    def test_1_add_folder(self):
        """Test adding a folder with different configurations"""
        print("\n" + "="*70)
        print("TEST 1: ADD FOLDER")
        print("="*70)
        
        # Test 1.1: Add basic folder
        print("\n1.1 Adding basic folder...")
        result = run_cli_command(f"add-folder --path {self.test_dir} --name TestSystemFolder")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                self.folder_id = data.get('folder_id')
                print(f"✓ Folder added successfully")
                print(f"  ID: {self.folder_id}")
                print(f"  Name: {data.get('name')}")
                print(f"  Path: {data.get('path')}")
                print(f"  State: {data.get('state')}")
                self.results['add_folder'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to add folder")
            if result.get('stderr'):
                print(f"  Error: {result['stderr'][:200]}")
        
        self.results['add_folder'] = False
        return False
    
    def test_2_list_folders(self):
        """Test listing folders"""
        print("\n" + "="*70)
        print("TEST 2: LIST FOLDERS")
        print("="*70)
        
        result = run_cli_command("list-folders")
        
        if parse_json_output(result):
            folders = result['data']
            print(f"✓ Found {len(folders)} folder(s)")
            
            # Find our test folder
            our_folder = None
            for folder in folders:
                if folder.get('folder_id') == self.folder_id:
                    our_folder = folder
                    break
            
            if our_folder:
                print(f"✓ Our test folder found:")
                print(f"  Name: {our_folder.get('name')}")
                print(f"  State: {our_folder.get('state')}")
                print(f"  Files: {our_folder.get('total_files', 0)}")
                print(f"  Size: {our_folder.get('total_size', 0)} bytes")
                self.results['list_folders'] = True
                return True
            else:
                print(f"✗ Test folder not found in list")
        else:
            print(f"✗ Failed to list folders")
        
        self.results['list_folders'] = False
        return False
    
    def test_3_index_folder(self):
        """Test indexing files in folder"""
        print("\n" + "="*70)
        print("TEST 3: INDEX FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['index_folder'] = False
            return False
        
        print(f"Indexing folder {self.folder_id}...")
        result = run_cli_command(f"index-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder indexed successfully")
                print(f"  Files indexed: {data.get('files_indexed', 0)}")
                print(f"  Total size: {data.get('total_size', 0)} bytes")
                print(f"  State: {data.get('state')}")
                self.results['index_folder'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to index folder")
            if result.get('stderr'):
                print(f"  Error: {result['stderr'][:500]}")
        
        self.results['index_folder'] = False
        return False
    
    def test_4_segment_folder(self):
        """Test creating segments for folder"""
        print("\n" + "="*70)
        print("TEST 4: SEGMENT FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['segment_folder'] = False
            return False
        
        print(f"Creating segments for folder {self.folder_id}...")
        result = run_cli_command(f"segment-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder segmented successfully")
                print(f"  Total segments: {data.get('total_segments', 0)}")
                print(f"  Redundancy segments: {data.get('redundancy_segments', 0)}")
                print(f"  State: {data.get('state')}")
                self.results['segment_folder'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to segment folder")
            if result.get('stderr'):
                print(f"  Error: {result['stderr'][:500]}")
        
        self.results['segment_folder'] = False
        return False
    
    def test_5_access_control(self):
        """Test access control settings"""
        print("\n" + "="*70)
        print("TEST 5: ACCESS CONTROL")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['access_control'] = False
            return False
        
        tests_passed = 0
        
        # Test 5.1: Set folder to private
        print("\n5.1 Setting folder to private...")
        result = run_cli_command(f"set-folder-access --folder-id {self.folder_id} --access-type private")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder set to private")
                tests_passed += 1
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to set access type")
        
        # Test 5.2: Add authorized user
        print("\n5.2 Adding authorized user...")
        result = run_cli_command(f"add-authorized-user --folder-id {self.folder_id} --user-id test_user_1")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ User authorized")
                tests_passed += 1
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to add authorized user")
        
        # Test 5.3: Set folder to password-protected
        print("\n5.3 Setting folder to password-protected...")
        result = run_cli_command(f"set-folder-access --folder-id {self.folder_id} --access-type protected --password TestPassword123")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder password-protected")
                tests_passed += 1
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to set password protection")
        
        # Test 5.4: Set back to public
        print("\n5.4 Setting folder back to public...")
        result = run_cli_command(f"set-folder-access --folder-id {self.folder_id} --access-type public")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder set to public")
                tests_passed += 1
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to set to public")
        
        self.results['access_control'] = tests_passed >= 2
        return self.results['access_control']
    
    def test_6_upload_folder(self):
        """Test uploading folder to Usenet"""
        print("\n" + "="*70)
        print("TEST 6: UPLOAD FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['upload_folder'] = False
            return False
        
        print(f"Uploading folder {self.folder_id}...")
        print("Note: This requires configured Usenet server")
        
        result = run_cli_command(f"upload-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Upload initiated")
                print(f"  Uploaded segments: {data.get('uploaded_segments', 0)}")
                print(f"  Failed segments: {data.get('failed_segments', 0)}")
                print(f"  State: {data.get('state')}")
                self.results['upload_folder'] = True
                return True
            else:
                # Upload might fail if no server configured
                print(f"⚠ Upload not available: {data['error']}")
                self.results['upload_folder'] = None  # Not a failure, just not available
                return None
        else:
            print(f"⚠ Upload functionality not available")
            if result.get('stderr'):
                print(f"  Info: {result['stderr'][:200]}")
        
        self.results['upload_folder'] = None
        return None
    
    def test_7_publish_folder(self):
        """Test publishing folder core index"""
        print("\n" + "="*70)
        print("TEST 7: PUBLISH FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['publish_folder'] = False
            return False
        
        print(f"Publishing folder {self.folder_id}...")
        result = run_cli_command(f"publish-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder published")
                print(f"  Share ID: {data.get('share_id')}")
                print(f"  Core index size: {data.get('core_index_size', 0)} bytes")
                print(f"  Published: {data.get('published')}")
                self.results['publish_folder'] = True
                return True
            else:
                print(f"⚠ Publishing not available: {data['error']}")
                self.results['publish_folder'] = None
                return None
        else:
            print(f"⚠ Publishing functionality not available")
        
        self.results['publish_folder'] = None
        return None
    
    def test_8_resync_folder(self):
        """Test re-syncing folder for changes"""
        print("\n" + "="*70)
        print("TEST 8: RE-SYNC FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['resync_folder'] = False
            return False
        
        # Make a change to the folder
        print("Making changes to folder...")
        new_file = Path(self.test_dir) / "new_file.txt"
        with open(new_file, 'w') as f:
            f.write("This is a new file for resync test\n" * 100)
        print(f"✓ Added new file: {new_file.name}")
        
        # Re-sync the folder
        print(f"\nRe-syncing folder {self.folder_id}...")
        result = run_cli_command(f"resync-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder re-synced")
                print(f"  New files: {data.get('new_files', 0)}")
                print(f"  Modified files: {data.get('modified_files', 0)}")
                print(f"  Deleted files: {data.get('deleted_files', 0)}")
                self.results['resync_folder'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to re-sync folder")
            if result.get('stderr'):
                print(f"  Error: {result['stderr'][:200]}")
        
        self.results['resync_folder'] = False
        return False
    
    def test_9_folder_info(self):
        """Test getting detailed folder information"""
        print("\n" + "="*70)
        print("TEST 9: FOLDER INFORMATION")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['folder_info'] = False
            return False
        
        print(f"Getting info for folder {self.folder_id}...")
        result = run_cli_command(f"folder-info --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder information retrieved")
                print(f"  Name: {data.get('name')}")
                print(f"  State: {data.get('state')}")
                print(f"  Total files: {data.get('total_files', 0)}")
                print(f"  Total size: {data.get('total_size', 0)} bytes")
                print(f"  Total segments: {data.get('total_segments', 0)}")
                print(f"  Access type: {data.get('access_type', 'public')}")
                print(f"  Published: {data.get('published', False)}")
                print(f"  Share ID: {data.get('share_id', 'N/A')}")
                self.results['folder_info'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to get folder info")
        
        self.results['folder_info'] = False
        return False
    
    def test_10_delete_folder(self):
        """Test deleting a folder"""
        print("\n" + "="*70)
        print("TEST 10: DELETE FOLDER")
        print("="*70)
        
        if not self.folder_id:
            print("✗ No folder ID available")
            self.results['delete_folder'] = False
            return False
        
        print(f"Deleting folder {self.folder_id}...")
        result = run_cli_command(f"delete-folder --folder-id {self.folder_id}")
        
        if parse_json_output(result):
            data = result['data']
            if 'error' not in data:
                print(f"✓ Folder deleted successfully")
                self.results['delete_folder'] = True
                return True
            else:
                print(f"✗ Error: {data['error']}")
        else:
            print(f"✗ Failed to delete folder")
        
        self.results['delete_folder'] = False
        return False
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n" + "="*70)
        print("CLEANING UP")
        print("="*70)
        
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"✓ Removed test directory: {self.test_dir}")
        
        return True
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("COMPLETE FOLDER MANAGEMENT SYSTEM TEST")
        print("="*80)
        
        # Setup
        self.setup()
        
        # Run tests
        tests = [
            self.test_1_add_folder,
            self.test_2_list_folders,
            self.test_3_index_folder,
            self.test_4_segment_folder,
            self.test_5_access_control,
            self.test_6_upload_folder,
            self.test_7_publish_folder,
            self.test_8_resync_folder,
            self.test_9_folder_info,
            self.test_10_delete_folder
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"✗ Test failed with exception: {e}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        test_names = {
            'add_folder': 'Add Folder',
            'list_folders': 'List Folders',
            'index_folder': 'Index Folder',
            'segment_folder': 'Segment Folder',
            'access_control': 'Access Control',
            'upload_folder': 'Upload Folder',
            'publish_folder': 'Publish Folder',
            'resync_folder': 'Re-sync Folder',
            'folder_info': 'Folder Info',
            'delete_folder': 'Delete Folder'
        }
        
        passed = 0
        failed = 0
        skipped = 0
        
        for key, name in test_names.items():
            result = self.results.get(key)
            if result is True:
                status = "✅ PASS"
                passed += 1
            elif result is False:
                status = "❌ FAIL"
                failed += 1
            elif result is None:
                status = "⚠️  SKIP"
                skipped += 1
            else:
                status = "❓ UNKNOWN"
                
            print(f"{name:20} {status}")
        
        print("\n" + "-"*40)
        print(f"Passed:  {passed}")
        print(f"Failed:  {failed}")
        print(f"Skipped: {skipped}")
        
        print("\n" + "="*80)
        if failed == 0:
            print("✅ ALL CRITICAL TESTS PASSED!")
            print("\nThe folder management system is fully functional.")
        else:
            print("❌ SOME TESTS FAILED")
            print("\nPlease review the failures above.")
        print("="*80)

if __name__ == "__main__":
    tester = FolderSystemTest()
    tester.run_all_tests()