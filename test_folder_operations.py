#!/usr/bin/env python3
"""
Test folder operations with full FolderManager functionality
"""

import subprocess
import json
import sys
import os
import tempfile

def run_cli_command(command):
    """Run a CLI command and return the result"""
    cmd = [sys.executable, "/workspace/src/cli.py"] + command.split()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
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

def test_database_setup():
    """Test database initialization"""
    print("\n1. Testing database setup...")
    print("-" * 50)
    
    result = run_cli_command("check-database")
    
    if result['success'] and result['stdout']:
        try:
            data = json.loads(result['stdout'])
            result['data'] = data
            print(f"✅ Database status: {data.get('status', 'unknown')}")
            print(f"   Type: {data.get('type', 'unknown')}")
            if data.get('schema_status'):
                print(f"   Schema: {data.get('schema_status')}")
            return True
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {result['stdout'][:100]}")
            return False
    else:
        print(f"❌ Database check failed")
        if result.get('stderr'):
            print(f"   Error: {result['stderr'][:200]}")
        return False

def test_add_folder():
    """Test adding a folder"""
    print("\n2. Testing add-folder command...")
    print("-" * 50)
    
    # Create a test folder
    test_dir = tempfile.mkdtemp(prefix="test_folder_")
    print(f"   Created test folder: {test_dir}")
    
    # Try to add the folder
    result = run_cli_command(f"add-folder --path {test_dir} --name TestFolder")
    
    if result['success'] and result['stdout']:
        try:
            data = json.loads(result['stdout'])
            
            if 'error' in data:
                print(f"❌ Error adding folder: {data['error']}")
                
                # Check if it's a database table issue
                if 'relation' in data['error'] and 'does not exist' in data['error']:
                    print("\n   📋 Database tables may not be initialized properly")
                    print("   The FolderManager requires these tables:")
                    print("   - managed_folders")
                    print("   - files")
                    print("   - segments")
                    print("   - folder_operations")
                    print("   - progress")
                return False
            else:
                print(f"✅ Folder added successfully")
                print(f"   Folder ID: {data.get('folder_id', 'N/A')}")
                print(f"   Path: {data.get('path', 'N/A')}")
                print(f"   Name: {data.get('name', 'N/A')}")
                return True
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {result['stdout'][:100]}")
            return False
    else:
        print(f"❌ Add folder failed")
        if result.get('stderr'):
            error = result['stderr']
            print(f"   Error: {error[:500]}")
            
            # Parse error if it's JSON
            try:
                error_data = json.loads(error)
                if 'error' in error_data:
                    print(f"\n   Specific error: {error_data['error']}")
            except:
                pass
        return False

def test_list_folders():
    """Test listing folders"""
    print("\n3. Testing list-folders command...")
    print("-" * 50)
    
    result = run_cli_command("list-folders")
    
    if result['success'] and result['stdout']:
        try:
            data = json.loads(result['stdout'])
            
            if isinstance(data, list):
                print(f"✅ List folders successful")
                print(f"   Found {len(data)} folder(s)")
                
                if len(data) > 0:
                    print("\n   Folders:")
                    for folder in data[:3]:  # Show first 3
                        print(f"   - {folder.get('name', 'Unknown')} ({folder.get('folder_id', 'N/A')})")
                return True
            else:
                print(f"❌ Unexpected response type: {type(data)}")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {result['stdout'][:100]}")
            return False
    else:
        print(f"❌ List folders failed")
        if result.get('stderr'):
            print(f"   Error: {result['stderr'][:200]}")
        return False

def main():
    print("=" * 70)
    print("FOLDER OPERATIONS TEST")
    print("=" * 70)
    print("\nTesting full FolderManager functionality...")
    
    # Run tests
    db_ok = test_database_setup()
    add_ok = test_add_folder()
    list_ok = test_list_folders()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    tests = [
        ("Database setup", db_ok),
        ("Add folder", add_ok),
        ("List folders", list_ok)
    ]
    
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(passed for _, passed in tests)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe folder management system is working correctly!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        
        if not db_ok:
            print("- Check database connection and configuration")
        
        if not add_ok:
            print("- Ensure all required tables are created")
            print("- Check FolderManager initialization")
            print("- Verify PostgreSQL is running and accessible")
        
        if not list_ok:
            print("- Check if folders table exists and is accessible")
    
    print("=" * 70)

if __name__ == "__main__":
    main()