#!/usr/bin/env python3
"""
Fix the output_json and output_error issues in cli.py
Run this on your local machine if git pull doesn't work
"""

import os
import sys
import re

def fix_cli_file(filepath):
    """Fix the undefined output functions in cli.py"""
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already fixed
    if 'output_json' not in content and 'output_error' not in content:
        print("File appears to be already fixed!")
        return True
    
    print("Found undefined output functions, fixing...")
    
    # Replace output_json with click.echo(json.dumps(...))
    content = re.sub(
        r'return output_json\((.*?)\)',
        r'click.echo(json.dumps(\1))',
        content,
        flags=re.DOTALL
    )
    
    # Replace output_error with click.echo(json.dumps({"error": ...}), err=True)
    # Handle simple string errors
    content = re.sub(
        r'return output_error\("([^"]+)"\)',
        r'click.echo(json.dumps({"error": "\1"}), err=True)\n            return',
        content
    )
    
    # Handle f-string errors
    content = re.sub(
        r'return output_error\(f"([^"]+)"\)',
        r'click.echo(json.dumps({"error": f"\1"}), err=True)\n            return',
        content
    )
    
    # Replace any remaining output_json that don't have return
    content = re.sub(
        r'(?<!return )output_json\((.*?)\)',
        r'click.echo(json.dumps(\1))',
        content,
        flags=re.DOTALL
    )
    
    # Replace any remaining output_error that don't have return
    content = re.sub(
        r'(?<!return )output_error\(f?"([^"]+)"\)',
        r'click.echo(json.dumps({"error": "\1"}), err=True)',
        content
    )
    
    # Write the fixed content back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")
    return True

def main():
    # Try multiple possible locations
    possible_paths = [
        r'C:\git\usenetsync\src\cli.py',
        r'src\cli.py',
        'src/cli.py',
    ]
    
    fixed = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found cli.py at: {path}")
            if fix_cli_file(path):
                fixed = True
                break
    
    if not fixed:
        print("Could not find cli.py to fix!")
        print("Please run this script from the usenetsync directory")
        return 1
    
    print("\nFix complete! The cli.py file has been updated.")
    print("You should now be able to use the database commands without errors.")
    return 0

if __name__ == '__main__':
    sys.exit(main())