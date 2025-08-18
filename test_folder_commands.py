#!/usr/bin/env python3
"""
Test all folder-related CLI commands to ensure they return valid JSON
"""

import subprocess
import json
import sys
import os

def test_cli_command(command_args):
    """Test a CLI command and verify JSON output"""
    cmd_str = command_args[-1] if command_args else "unknown"
    print(f"\nTesting: {cmd_str}")
    print("-" * 50)
    
    try:
        # Run the command
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            timeout=5,
            cwd="/workspace"
        )
        
        print(f"Exit code: {result.returncode}")
        
        # Check for output
        if not result.stdout:
            print("❌ ERROR: Empty stdout (causes 'EOF while parsing')")
            return False
        
        print(f"Stdout length: {len(result.stdout)} chars")
        
        # Try to parse JSON
        try:
            data = json.loads(result.stdout)
            print(f"✅ Valid JSON parsed")
            print(f"   Type: {type(data).__name__}")
            
            if isinstance(data, list):
                print(f"   Array with {len(data)} items")
            elif isinstance(data, dict):
                print(f"   Dict with keys: {list(data.keys())[:5]}")
                
            # Show sample data
            if isinstance(data, list) and len(data) > 0:
                print(f"   First item: {json.dumps(data[0], indent=2)[:200]}")
            elif isinstance(data, dict):
                print(f"   Sample: {json.dumps(data, indent=2)[:200]}")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"   Output: {repr(result.stdout[:100])}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("TESTING FOLDER-RELATED CLI COMMANDS")
    print("=" * 70)
    
    python = sys.executable
    cli_path = "/workspace/src/cli.py"
    
    # Check if CLI exists
    if not os.path.exists(cli_path):
        print(f"❌ CLI not found at {cli_path}")
        return
    
    # Test commands
    commands = [
        [python, cli_path, "list-folders"],
        [python, cli_path, "get-folders"],
        [python, cli_path, "get_folders"],
        [python, cli_path, "check-database"],
    ]
    
    results = []
    for cmd in commands:
        success = test_cli_command(cmd)
        results.append((cmd[-1], success))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for cmd_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{cmd_name:20} {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Frontend should work correctly")
    else:
        print("❌ SOME TESTS FAILED - Frontend will show 'EOF while parsing' error")
    print("=" * 70)

if __name__ == "__main__":
    main()