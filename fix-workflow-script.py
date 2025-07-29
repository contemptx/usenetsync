#!/usr/bin/env python3
"""
Diagnostic script to find and show the syntax error in consolidated_github_workflow.py
"""

import sys
from pathlib import Path

def diagnose_syntax_error():
    """Find and display the syntax error"""
    
    print("Diagnosing consolidated_github_workflow.py...")
    print("=" * 60)
    
    file_path = Path('consolidated_github_workflow.py')
    
    if not file_path.exists():
        print("Error: consolidated_github_workflow.py not found!")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"File has {len(lines)} lines total")
        print("\nShowing lines 100-115 (around line 107):")
        print("-" * 60)
        
        for i in range(max(0, 100), min(len(lines), 115)):
            line_num = i + 1
            line = lines[i].rstrip()
            marker = " <-- ERROR HERE" if line_num == 107 else ""
            print(f"{line_num:4d}: {line}{marker}")
        
        print("-" * 60)
        
        # Look for common batch file commands that shouldn't be in Python
        batch_commands = ['xcopy', 'echo', 'REM', '@echo', 'mkdir', 'del', 'pause']
        found_batch = False
        
        print("\nScanning for batch commands in Python file:")
        for i, line in enumerate(lines):
            for cmd in batch_commands:
                if line.strip().startswith(cmd):
                    if not found_batch:
                        print("\nFound batch commands that should not be in Python file:")
                        found_batch = True
                    print(f"  Line {i+1}: {line.strip()[:60]}...")
        
        if not found_batch:
            print("  No obvious batch commands found")
            
        # Check for unterminated strings around line 107
        print("\nChecking for string issues around line 107:")
        for i in range(max(0, 105), min(len(lines), 110)):
            line = lines[i]
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\\"')
            
            if single_quotes % 2 != 0 or double_quotes % 2 != 0:
                print(f"  Line {i+1}: Possible unterminated string")
                print(f"    {line.strip()[:70]}...")
        
    except Exception as e:
        print(f"Error reading file: {e}")
    
    print("\n" + "=" * 60)
    print("Diagnosis complete!")
    print("\nTo fix:")
    print("1. Delete the current consolidated_github_workflow.py")
    print("2. Re-save the Python artifact (make sure it's the Python code, not batch)")
    print("3. Or use the fixed version I'll create next")

if __name__ == '__main__':
    diagnose_syntax_error()
