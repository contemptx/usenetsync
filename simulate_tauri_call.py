#!/usr/bin/env python3
"""Simulate what Tauri does when calling get_folders"""

import subprocess
import sys
import json

# This simulates what Tauri does in main.rs line 740
def simulate_tauri_get_folders():
    cmd = [sys.executable, "/workspace/src/cli.py", "list-folders"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)}")
        print(f"Stderr length: {len(result.stderr)}")
        
        if result.stdout:
            print(f"Stdout content: {repr(result.stdout[:100])}")
        
        if result.stderr:
            print(f"Stderr content: {repr(result.stderr[:200])}")
        
        # Try to parse as JSON (what Tauri does)
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                print(f"✓ Valid JSON parsed: {type(data)}")
                if isinstance(data, list):
                    print(f"  Array with {len(data)} items")
                return data
            except json.JSONDecodeError as e:
                print(f"✗ JSON parse error: {e}")
                print(f"  At position: line {e.lineno}, column {e.colno}")
                return None
        else:
            print("✗ Empty stdout - this causes 'EOF while parsing' error")
            return None
            
    except Exception as e:
        print(f"Error running command: {e}")
        return None

print("Simulating Tauri's call to get_folders()...")
print("=" * 60)
result = simulate_tauri_get_folders()
print("=" * 60)

if result is None:
    print("\nThis would cause the frontend error:")
    print("  'EOF while parsing a value at line 1 column 0'")
else:
    print(f"\nSuccess! Returned: {json.dumps(result, indent=2)}")