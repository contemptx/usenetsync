#!/usr/bin/env python3
"""Test CLI commands directly"""

import subprocess
import json
import sys

def test_command(cmd):
    """Test a CLI command"""
    print(f"\nTesting: {cmd}")
    print("-" * 40)
    
    result = subprocess.run(
        [sys.executable, "/workspace/src/cli.py"] + cmd.split(),
        capture_output=True,
        text=True,
        timeout=5
    )
    
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Stdout: {result.stdout}")
        try:
            data = json.loads(result.stdout)
            print(f"Valid JSON: ✓")
            print(f"Data type: {type(data)}")
            if isinstance(data, list):
                print(f"Array length: {len(data)}")
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
    
    if result.stderr:
        print(f"Stderr: {result.stderr[:200]}")
    
    return result

# Test all folder-related commands
print("=" * 60)
print("TESTING CLI COMMANDS")
print("=" * 60)

# Install dependencies first
print("\nInstalling dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "click", "psycopg2-binary", "-q"])

# Test commands
test_command("list-folders")
test_command("get-folders")
test_command("get_folders")
test_command("check-database")