#!/usr/bin/env python3
"""
Comprehensive test of all CLI commands to verify functionality
"""

import subprocess
import json
import sys
import os

def run_command(cmd_parts):
    """Run a CLI command and return the result"""
    try:
        # Build the command
        if isinstance(cmd_parts, str):
            cmd_parts = cmd_parts.split()
        
        full_cmd = [sys.executable, "/workspace/src/cli.py"] + cmd_parts
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            'command': ' '.join(cmd_parts),
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'json_valid': False,
            'json_data': None
        }
    except subprocess.TimeoutExpired:
        return {
            'command': ' '.join(cmd_parts),
            'error': 'Command timed out',
            'exit_code': -1
        }
    except Exception as e:
        return {
            'command': ' '.join(cmd_parts),
            'error': str(e),
            'exit_code': -1
        }

def parse_json_output(result):
    """Try to parse JSON from the output"""
    if result.get('stdout'):
        try:
            result['json_data'] = json.loads(result['stdout'])
            result['json_valid'] = True
        except json.JSONDecodeError as e:
            result['json_error'] = str(e)
    return result

def test_command(cmd_parts, description=""):
    """Test a single command and print results"""
    print(f"\n{'='*60}")
    if description:
        print(f"TEST: {description}")
    print(f"COMMAND: {' '.join(cmd_parts) if isinstance(cmd_parts, list) else cmd_parts}")
    print('-'*60)
    
    result = run_command(cmd_parts)
    result = parse_json_output(result)
    
    print(f"Exit Code: {result.get('exit_code', 'N/A')}")
    
    if result.get('stdout'):
        print(f"Stdout: {result['stdout'][:200]}{'...' if len(result['stdout']) > 200 else ''}")
    
    if result.get('stderr'):
        print(f"Stderr: {result['stderr'][:200]}{'...' if len(result['stderr']) > 200 else ''}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    if result.get('json_valid'):
        print(f"JSON Valid: ✓")
        print(f"JSON Data: {json.dumps(result['json_data'], indent=2)[:500]}")
    elif result.get('json_error'):
        print(f"JSON Valid: ✗ - {result['json_error']}")
    
    return result

def main():
    print("="*80)
    print("COMPREHENSIVE CLI COMMAND TESTING")
    print("="*80)
    
    # Test database commands
    print("\n" + "="*80)
    print("DATABASE COMMANDS")
    print("="*80)
    
    test_command(["check-database"], "Check database connection")
    test_command(["database-info"], "Get database info")
    
    # Test folder commands - all variations
    print("\n" + "="*80)
    print("FOLDER LISTING COMMANDS")
    print("="*80)
    
    test_command(["list-folders"], "List folders (hyphen)")
    test_command(["get-folders"], "Get folders (hyphen)")
    test_command(["get_folders"], "Get folders (underscore) - What Tauri calls")
    
    # Test add folder command variations
    print("\n" + "="*80)
    print("ADD FOLDER COMMANDS")
    print("="*80)
    
    test_command(["add-folder", "--path", "/test/path", "--name", "Test Folder"], "Add folder (hyphen)")
    test_command(["add_folder", "--path", "/test/path", "--name", "Test Folder"], "Add folder (underscore)")
    
    # Test other folder operations
    print("\n" + "="*80)
    print("OTHER FOLDER OPERATIONS")
    print("="*80)
    
    test_command(["index-folder", "--folder-id", "test-id"], "Index folder")
    test_command(["segment-folder", "--folder-id", "test-id"], "Segment folder")
    test_command(["upload-folder", "--folder-id", "test-id"], "Upload folder")
    
    # Test user commands
    print("\n" + "="*80)
    print("USER COMMANDS")
    print("="*80)
    
    test_command(["get-user-info"], "Get user info")
    test_command(["is-user-initialized"], "Check if user initialized")
    
    # Summary
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()