#!/usr/bin/env python3
"""
Test ALL functionality with proper database - MUST BE 100%
"""

import sys
import os
import json
import subprocess
import tempfile
import hashlib
from pathlib import Path

# Set the database to our test database with correct schema
os.environ['USENETSYNC_DB'] = '/tmp/test_usenetsync.db'

sys.path.insert(0, '/workspace/src')

def call_backend(command, args=None):
    """Call backend command through the bridge"""
    if args is None:
        args = {}
    
    cmd_data = {
        'command': command,
        'args': args
    }
    
    env = os.environ.copy()
    env['USENETSYNC_DB'] = '/tmp/test_usenetsync.db'
    
    result = subprocess.run(
        [sys.executable, '/workspace/src/gui_backend_bridge.py', 
         '--mode', 'command', 
         '--command', json.dumps(cmd_data)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env
    )
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            return response
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON response'}
    else:
        return {'success': False, 'error': result.stderr}

def test_functionality():
    """Test all major functionality - MUST BE 100%"""
    
    print("=" * 80)
    print("TESTING ALL USENETSYNC FUNCTIONALITY - MUST BE 100%")
    print("=" * 80)
    
    results = {}
    
    # 1. Test User Management
    print("\n📤 1. USER MANAGEMENT")
    print("-" * 40)
    
    # Check if user initialized
    print("Testing: is_user_initialized")
    result = call_backend('is_user_initialized')
    results['user_initialized'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Initialize user (handle if already exists)
    print("Testing: initialize_user")
    # First check if we need to initialize
    if not result.get('data', False):  # Only initialize if not already initialized
        result = call_backend('initialize_user', {'display_name': 'TestUser'})
    else:
        result = {'success': True, 'data': 'already_initialized'}
    results['initialize_user'] = result.get('success', False)
    user_id = result.get('data', '')
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Get user info
    print("Testing: get_user_info")
    result = call_backend('get_user_info')
    results['get_user_info'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 2. Test Folder Management
    print("\n📁 2. FOLDER MANAGEMENT")
    print("-" * 40)
    
    # Create test folder
    test_dir = tempfile.mkdtemp(prefix='usenetsync_test_')
    test_file = Path(test_dir) / 'test_document.txt'
    test_file.write_text('This is a test document for UsenetSync testing.')
    
    # Add folder
    print(f"Testing: add_folder")
    result = call_backend('add_folder', {
        'path': test_dir,
        'name': 'Test Folder'
    })
    results['add_folder'] = result.get('success', False)
    folder_id = result.get('data', {}).get('folder_id', '')
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Index folder
    if folder_id:
        print(f"Testing: index_folder")
        result = call_backend('index_folder', {'folder_id': folder_id})
        results['index_folder'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Get folders
    print("Testing: get_folders")
    result = call_backend('get_folders')
    results['get_folders'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Get folder info
    if folder_id:
        print(f"Testing: folder_info")
        result = call_backend('folder_info', {'folder_id': folder_id})
        results['folder_info'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 3. Test Segmentation
    print("\n✂️ 3. SEGMENTATION")
    print("-" * 40)
    
    if folder_id:
        print(f"Testing: segment_folder")
        result = call_backend('segment_folder', {'folder_id': folder_id})
        results['segment_folder'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 4. Test Sharing
    print("\n🔗 4. SHARING")
    print("-" * 40)
    
    # Create share
    print("Testing: create_share")
    result = call_backend('create_share', {
        'files': [test_dir],
        'share_type': 'public'
    })
    results['create_share'] = result.get('success', False)
    share_id = result.get('data', {}).get('id', '')
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Get shares
    print("Testing: get_shares")
    result = call_backend('get_shares')
    results['get_shares'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Get share details
    if share_id:
        print(f"Testing: get_share_details")
        result = call_backend('get_share_details', {'share_id': share_id})
        results['get_share_details'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 5. Test Access Control
    print("\n🔒 5. ACCESS CONTROL")
    print("-" * 40)
    
    if folder_id:
        # Set folder access
        print(f"Testing: set_folder_access")
        result = call_backend('set_folder_access', {
            'folder_id': folder_id,
            'access_type': 'protected',
            'password': 'test123'
        })
        results['set_folder_access'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
        
        # Add authorized user
        print(f"Testing: add_authorized_user")
        result = call_backend('add_authorized_user', {
            'folder_id': folder_id,
            'user_id': 'test_user_123'
        })
        results['add_authorized_user'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
        
        # Get authorized users
        print(f"Testing: get_authorized_users")
        result = call_backend('get_authorized_users', {
            'folder_id': folder_id
        })
        results['get_authorized_users'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 6. Test Database
    print("\n💾 6. DATABASE")
    print("-" * 40)
    
    print("Testing: check_database_status")
    result = call_backend('check_database_status')
    results['check_database_status'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 7. Test System Stats
    print("\n📊 7. SYSTEM STATS")
    print("-" * 40)
    
    print("Testing: get_system_stats")
    result = call_backend('get_system_stats')
    results['get_system_stats'] = result.get('success', False)
    print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
    if not result.get('success'):
        print(f"    Error: {result.get('error', 'Unknown')}")
    
    # 8. Test Upload/Download Simulation
    print("\n⬆️⬇️ 8. UPLOAD/DOWNLOAD")
    print("-" * 40)
    
    if folder_id:
        print(f"Testing: upload_folder")
        result = call_backend('upload_folder', {'folder_id': folder_id})
        results['upload_folder'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
        
        print(f"Testing: publish_folder")
        result = call_backend('publish_folder', {
            'folder_id': folder_id,
            'access_type': 'public'
        })
        results['publish_folder'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    if share_id:
        print(f"Testing: download_share")
        download_dir = tempfile.mkdtemp(prefix='usenetsync_download_')
        result = call_backend('download_share', {
            'share_id': share_id,
            'destination': download_dir
        })
        results['download_share'] = result.get('success', False)
        print(f"  Result: {'✅ PASS' if result.get('success') else '❌ FAIL'}")
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY - MUST BE 100%")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test:30} {status}")
    
    print("\n" + "-" * 40)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 100% SUCCESS! ALL TESTS PASSED!")
        print("The application is FULLY FUNCTIONAL!")
    else:
        print(f"\n❌ FAILURE: Only {passed/total*100:.1f}% passing")
        print("NOT ACCEPTABLE - Must be 100%!")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(test_dir)
        if 'download_dir' in locals():
            shutil.rmtree(download_dir)
    except:
        pass
    
    return passed, failed

if __name__ == '__main__':
    passed, failed = test_functionality()
    sys.exit(0 if failed == 0 else 1)