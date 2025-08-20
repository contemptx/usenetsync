#!/usr/bin/env python3
"""
Test the Python backend bridge to ensure it handles commands correctly
"""

import sys
import os
import json
import subprocess

sys.path.insert(0, '/workspace/src')

def test_command(command_name, args=None):
    """Test a single command through the backend bridge"""
    if args is None:
        args = {}
    
    cmd_data = {
        'command': command_name,
        'args': args
    }
    
    # Call the backend bridge
    result = subprocess.run(
        [sys.executable, '/workspace/src/gui_backend_bridge.py', 
         '--mode', 'command', 
         '--command', json.dumps(cmd_data)],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode != 0:
        return False, f"Command failed with code {result.returncode}: {result.stderr}"
    
    try:
        response = json.loads(result.stdout)
        return response.get('success', False), response
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON response: {e}"

def main():
    print("=" * 80)
    print("BACKEND BRIDGE TEST")
    print("=" * 80)
    
    # Test various commands
    test_cases = [
        ('is_user_initialized', {}),
        ('check_database_status', {}),
        ('get_system_stats', {}),
        ('get_folders', {}),
    ]
    
    passed = 0
    failed = 0
    
    for command, args in test_cases:
        print(f"\n📍 Testing: {command}")
        success, result = test_command(command, args)
        
        if success:
            print(f"✅ {command} - SUCCESS")
            if isinstance(result, dict) and 'data' in result:
                data_str = str(result['data'])[:100]
                print(f"   Response: {data_str}...")
            passed += 1
        else:
            print(f"❌ {command} - FAILED")
            error_str = str(result)[:200]
            print(f"   Error: {error_str}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("BACKEND BRIDGE TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL BACKEND COMMANDS WORK!")
        return True
    else:
        print(f"\n⚠️ {failed} commands failed")
        return False

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)