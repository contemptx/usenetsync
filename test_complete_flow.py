#!/usr/bin/env python3
"""Test the complete flow from Tauri to CLI"""

import subprocess
import json
import sys
import os

def test_cli_command(command):
    """Test a CLI command exactly as Tauri would call it"""
    print(f"\nTesting command: {command}")
    print("=" * 60)
    
    # Build the command as Tauri would
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "src", "cli.py")]
    cmd.extend(command.split())
    
    try:
        # Run with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(__file__)
        )
        
        print(f"Exit code: {result.returncode}")
        
        # Check stdout
        if result.stdout:
            print(f"Stdout (first 100 chars): {result.stdout[:100]}")
            
            # Try to parse as JSON
            try:
                data = json.loads(result.stdout)
                print(f"✓ Valid JSON")
                print(f"  Type: {type(data).__name__}")
                if isinstance(data, list):
                    print(f"  Length: {len(data)}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                return True, data
            except json.JSONDecodeError as e:
                print(f"✗ JSON parse error: {e}")
                print(f"  Full stdout: {repr(result.stdout)}")
                return False, None
        else:
            print("✗ Empty stdout (causes 'EOF while parsing' error)")
            return False, None
            
        # Check stderr
        if result.stderr:
            print(f"Stderr (first 200 chars): {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print("✗ Command timed out")
        return False, None
    except Exception as e:
        print(f"✗ Error running command: {e}")
        return False, None

# Test the commands
print("TESTING CLI COMMANDS AS TAURI WOULD CALL THEM")
print("=" * 80)

# Test list-folders (what Tauri actually calls)
success1, data1 = test_cli_command("list-folders")

# Test get-folders (hyphen version)
success2, data2 = test_cli_command("get-folders")

# Test get_folders (underscore version)
success3, data3 = test_cli_command("get_folders")

# Test check-database
success4, data4 = test_cli_command("check-database")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"list-folders: {'✓ Success' if success1 else '✗ Failed'}")
print(f"get-folders:  {'✓ Success' if success2 else '✗ Failed'}")
print(f"get_folders:  {'✓ Success' if success3 else '✗ Failed'}")
print(f"check-database: {'✓ Success' if success4 else '✗ Failed'}")

if not success1:
    print("\n⚠ The list-folders command is failing!")
    print("This is what Tauri calls, so the frontend will get 'EOF while parsing' error")