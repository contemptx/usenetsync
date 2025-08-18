#!/usr/bin/env python3
"""
Simulate exactly what Tauri does when the frontend calls getFolders()
This test replicates the exact flow from frontend to backend
"""

import subprocess
import json
import sys
import os

def simulate_tauri_get_folders():
    """
    Simulate what happens when:
    1. Frontend calls: getFolders() 
    2. Which invokes: invoke('get_folders')
    3. Tauri Rust calls: cli.py list-folders
    """
    
    print("Simulating Tauri's get_folders() function")
    print("=" * 60)
    
    # This is exactly what Tauri does in main.rs line 740
    cmd = [sys.executable, "/workspace/src/cli.py", "list-folders"]
    
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd="/workspace"
        )
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print(f"Stdout length: {len(result.stdout)} chars")
            
            # Try to parse JSON (what Tauri does at line 746)
            try:
                folders = json.loads(result.stdout)
                print(f"✅ Valid JSON parsed")
                print(f"   Type: {type(folders).__name__}")
                
                if isinstance(folders, list):
                    print(f"   Array with {len(folders)} items")
                    if len(folders) > 0:
                        print(f"   First item keys: {list(folders[0].keys())}")
                        
                print("\n✅ SUCCESS: Frontend will receive valid data")
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"   At: line {e.lineno}, column {e.colno}")
                print(f"   Output: {repr(result.stdout[:100])}")
                print("\n❌ ERROR: Frontend will show 'EOF while parsing' error")
                return False
        else:
            print("❌ Empty stdout")
            print("\n❌ ERROR: Frontend will show 'EOF while parsing a value at line 1 column 0'")
            return False
            
        if result.stderr:
            print(f"Stderr: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_database_check():
    """Test the check-database command"""
    print("\n\nTesting check-database command")
    print("=" * 60)
    
    cmd = [sys.executable, "/workspace/src/cli.py", "check-database"]
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                print(f"✅ Valid JSON")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Type: {data.get('type', 'unknown')}")
                print(f"   Message: {data.get('message', 'unknown')}")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON: {repr(result.stdout[:100])}")
                return False
        else:
            print("❌ Empty output")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("TAURI INTEGRATION TEST")
    print("=" * 70)
    print("\nThis test simulates exactly what happens when:")
    print("1. User opens the Folders page in the frontend")
    print("2. Frontend calls getFolders()")
    print("3. Tauri invokes the backend command")
    print("\n")
    
    # Test the main flow
    folders_ok = simulate_tauri_get_folders()
    
    # Test database check
    db_ok = test_database_check()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    if folders_ok and db_ok:
        print("✅ ALL TESTS PASSED")
        print("\nThe frontend should work correctly:")
        print("- Folders page will load without errors")
        print("- No 'EOF while parsing' errors")
        print("- Database status will be displayed correctly")
    else:
        print("❌ SOME TESTS FAILED")
        if not folders_ok:
            print("\n⚠ The Folders page will show 'EOF while parsing' error")
        if not db_ok:
            print("\n⚠ Database status may not display correctly")
    
    print("=" * 70)

if __name__ == "__main__":
    main()