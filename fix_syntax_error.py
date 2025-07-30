#!/usr/bin/env python3
"""
Fix Production Wrapper Syntax Error
Fixes the specific syntax error in production_db_wrapper.py
"""

import shutil
from pathlib import Path

def fix_syntax_error():
    """Fix the syntax error in production_db_wrapper.py"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_syntax_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read the file line by line to find and fix the issue
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the problematic line around line 812
    fixed_lines = []
    in_try_block = False
    try_indent = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check if we're entering a try block
        if line.strip().startswith('try:'):
            in_try_block = True
            try_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
        
        # Check if this is the problematic line (around line 812)
        if line_num >= 810 and line_num <= 815:
            if 'PRAGMA busy_timeout' in line and in_try_block:
                # This line was added incorrectly inside a try block
                # We need to add it in the right place with proper indentation
                
                # Look for the connection creation line before this
                for j in range(len(fixed_lines) - 1, -1, -1):
                    if 'sqlite3.connect' in fixed_lines[j]:
                        # Add the pragma settings after the connection creation
                        pragma_lines = [
                            '        \n',
                            '        # Configure for better concurrent access\n',
                            '        conn.execute("PRAGMA busy_timeout=60000")  # 60 second timeout\n',
                            '        conn.execute("PRAGMA journal_mode=WAL")\n',
                            '        conn.execute("PRAGMA synchronous=NORMAL")\n'
                        ]
                        
                        # Insert after row_factory line if it exists
                        for k in range(j, len(fixed_lines)):
                            if 'row_factory' in fixed_lines[k]:
                                # Insert pragma settings after row_factory
                                for pragma_line in pragma_lines:
                                    fixed_lines.insert(k + 1, pragma_line)
                                break
                        break
                
                # Skip the current problematic line
                continue
        
        # Check if we're exiting the try block
        if in_try_block and line.strip() and len(line) - len(line.lstrip()) <= try_indent:
            if line.strip().startswith(('except', 'finally', 'else')) or not line.strip().startswith(' '):
                in_try_block = False
        
        fixed_lines.append(line)
    
    # Write the fixed content back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("OK: Fixed syntax error in production_db_wrapper.py")
    return True

def clean_up_database_wrapper():
    """Clean up the production_db_wrapper.py to remove any problematic additions"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        return False
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any malformed pragma additions
    lines = content.split('\n')
    cleaned_lines = []
    
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        
        # Remove orphaned pragma lines that aren't properly indented
        if 'PRAGMA busy_timeout' in line and 'expected' not in line:
            # Check if this line is properly placed
            if i > 0 and 'try:' in lines[i-1]:
                # This is likely the problematic line - skip it
                continue
            elif line.strip().startswith('conn.execute("PRAGMA') and not any(x in line for x in ['def ', 'class ', 'with ']):
                # Check indentation context
                indent = len(line) - len(line.lstrip())
                if indent < 8:  # Probably orphaned
                    continue
        
        cleaned_lines.append(line)
    
    # Write back the cleaned content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print("OK: Cleaned up production_db_wrapper.py")
    return True

def add_proper_database_configuration():
    """Add proper database configuration in the right place"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        return False
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we need to add database configuration
    if 'PRAGMA busy_timeout' not in content:
        # Find the get_connection method or similar
        if 'def get_connection(self):' in content:
            # Add configuration after connection creation
            old_pattern = 'conn.row_factory = dict_factory'
            new_pattern = '''conn.row_factory = dict_factory
                
                # Configure for better concurrent access
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")'''
            
            if old_pattern in content and 'PRAGMA busy_timeout' not in content:
                content = content.replace(old_pattern, new_pattern)
                
                with open(wrapper_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("OK: Added proper database configuration")
    
    return True

def test_syntax():
    """Test Python syntax"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: production_db_wrapper.py syntax valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error still exists: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("FIX PRODUCTION WRAPPER SYNTAX ERROR")
    print("="*60)
    
    success = True
    
    # Clean up any problematic additions first
    if not clean_up_database_wrapper():
        print("ERROR: Could not clean up database wrapper")
        success = False
    
    # Fix the specific syntax error
    if not fix_syntax_error():
        print("ERROR: Could not fix syntax error")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax error still exists")
        # Try a more aggressive fix
        print("Attempting more aggressive syntax fix...")
        
        # Read the file and look for the specific error line
        with open('production_db_wrapper.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove any lines that contain PRAGMA statements outside of proper context
        fixed_lines = []
        for line in lines:
            if 'PRAGMA busy_timeout' in line and line.strip().startswith('conn.execute("PRAGMA'):
                # Check if this line is properly indented within a method
                indent = len(line) - len(line.lstrip())
                if indent >= 8:  # Properly indented
                    fixed_lines.append(line)
                # Otherwise skip this problematic line
            else:
                fixed_lines.append(line)
        
        # Write back
        with open('production_db_wrapper.py', 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        # Test again
        if not test_syntax():
            print("ERROR: Could not fix syntax error automatically")
            success = False
        else:
            print("OK: Aggressive fix worked")
    
    # Add proper configuration if needed
    add_proper_database_configuration()
    
    print()
    if success:
        print("[SUCCESS] Production wrapper syntax fixed!")
        print()
        print("The file should now have valid Python syntax.")
        print("Try running the folder indexing again.")
        return 0
    else:
        print("[ERROR] Could not fix syntax error")
        print()
        print("Manual fix needed:")
        print("1. Open production_db_wrapper.py")
        print("2. Look for line around 812 with PRAGMA statement")
        print("3. Make sure it's inside a proper method with correct indentation")
        print("4. Or remove the line if it's orphaned")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)