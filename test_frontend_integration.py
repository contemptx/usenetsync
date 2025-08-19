#!/usr/bin/env python3
"""
Test script to verify all CLI commands work correctly for frontend integration
"""

import subprocess
import json
import tempfile
import os
import sys
from pathlib import Path

def run_command(cmd):
    """Run a CLI command and return the result"""
    try:
        result = subprocess.run(
            f"python3 src/cli.py {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            cwd="/workspace"
        )
        
        # Try to parse as JSON
        try:
            return {
                'success': result.returncode == 0,
                'data': json.loads(result.stdout) if result.stdout else {},
                'error': result.stderr
            }
        except json.JSONDecodeError:
            return {
                'success': result.returncode == 0,
                'data': result.stdout,
                'error': result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }

def test_command(name, cmd, expected_success=True):
    """Test a single command"""
    print(f"\nTesting: {name}")
    print(f"Command: {cmd}")
    
    result = run_command(cmd)
    
    if result['success'] == expected_success:
        print(f"✅ {name}: PASS")
        if result['data']:
            print(f"   Response: {json.dumps(result['data'], indent=2) if isinstance(result['data'], dict) else result['data'][:100]}")
    else:
        print(f"❌ {name}: FAIL")
        print(f"   Error: {result['error']}")
    
    return result

def main():
    print("=" * 70)
    print("FRONTEND INTEGRATION TEST")
    print("Testing all CLI commands used by the frontend")
    print("=" * 70)
    
    # Create a test folder
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_folder"
        test_path.mkdir()
        
        # Create some test files
        for i in range(3):
            (test_path / f"test_file_{i}.txt").write_text(f"Test content {i}\n" * 100)
        
        print(f"\nCreated test folder: {test_path}")
        
        # Test 1: Add folder
        print("\n" + "=" * 50)
        print("TEST 1: ADD FOLDER")
        print("=" * 50)
        result = test_command(
            "add-folder",
            f'add-folder --path "{test_path}" --name "TestFolder"'
        )
        
        folder_id = None
        if result['success'] and isinstance(result['data'], dict):
            folder_id = result['data'].get('folder_id')
            print(f"   Folder ID: {folder_id}")
        
        # Test 2: List folders
        print("\n" + "=" * 50)
        print("TEST 2: LIST FOLDERS")
        print("=" * 50)
        test_command("list-folders", "list-folders")
        test_command("get-folders", "get-folders")
        
        if folder_id:
            # Test 3: Index folder (using the correct command name)
            print("\n" + "=" * 50)
            print("TEST 3: INDEX FOLDER")
            print("=" * 50)
            test_command(
                "index-managed-folder",
                f'index-managed-folder --folder-id {folder_id}'
            )
            
            # Test 4: Get folder info
            print("\n" + "=" * 50)
            print("TEST 4: FOLDER INFO")
            print("=" * 50)
            test_command(
                "folder-info",
                f'folder-info --folder-id {folder_id}'
            )
            
            # Test 5: Set folder access
            print("\n" + "=" * 50)
            print("TEST 5: SET ACCESS CONTROL")
            print("=" * 50)
            test_command(
                "set-folder-access (public)",
                f'set-folder-access --folder-id {folder_id} --access-type public'
            )
            test_command(
                "set-folder-access (protected)",
                f'set-folder-access --folder-id {folder_id} --access-type protected --password test123'
            )
            
            # Test 6: Segment folder
            print("\n" + "=" * 50)
            print("TEST 6: SEGMENT FOLDER")
            print("=" * 50)
            test_command(
                "segment-folder",
                f'segment-folder --folder-id {folder_id}'
            )
            
            # Test 7: Resync folder
            print("\n" + "=" * 50)
            print("TEST 7: RESYNC FOLDER")
            print("=" * 50)
            # Add a new file
            (test_path / "new_file.txt").write_text("New content")
            test_command(
                "resync-folder",
                f'resync-folder --folder-id {folder_id}'
            )
            
            # Test 8: Delete folder
            print("\n" + "=" * 50)
            print("TEST 8: DELETE FOLDER")
            print("=" * 50)
            test_command(
                "delete-folder",
                f'delete-folder --folder-id {folder_id} --confirm'
            )
    
    print("\n" + "=" * 70)
    print("FRONTEND INTEGRATION TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()