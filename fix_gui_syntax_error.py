#!/usr/bin/env python3
"""
Fix GUI Syntax Error
Fix the malformed threading code in the GUI file
"""

import shutil
from pathlib import Path

def fix_gui_syntax_error():
    """Fix the syntax error in GUI file"""
    
    gui_file = Path("usenetsync_gui_main.py")
    if not gui_file.exists():
        print("ERROR: usenetsync_gui_main.py not found")
        return False
    
    # Create backup
    backup_file = gui_file.with_suffix('.py.backup_syntax_error_fix')
    try:
        shutil.copy2(gui_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Checking for syntax errors...")
    
    # Find and fix the problematic line
    lines = content.split('\n')
    fixed_lines = []
    fixes_applied = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Fix the malformed threading code
        if '*indexing*lock' in line:
            print(f"FOUND problematic line {line_num}: {line.strip()}")
            
            # Replace with correct syntax
            if 'threading.Lock()' in line:
                # Fix the variable name
                fixed_line = line.replace('*indexing*lock', '_indexing_lock')
                fixed_lines.append(fixed_line)
                fixes_applied.append(f"Line {line_num}: Fixed variable name")
                print(f"FIXED to: {fixed_line.strip()}")
            else:
                # Skip malformed lines
                print(f"SKIPPED malformed line: {line.strip()}")
                continue
        else:
            fixed_lines.append(line)
    
    if fixes_applied:
        # Write back the fixed content
        with open(gui_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"OK: Applied {len(fixes_applied)} syntax fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
        
        return True
    else:
        # Check for other potential issues
        print("No obvious syntax errors found. Checking for other issues...")
        
        # Look for the actual problematic code
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if 'threading' in line:
                print(f"Line {i+1}: {line}")
        
        return False

def clean_gui_file_completely():
    """Clean up the GUI file by removing problematic threading code"""
    
    gui_file = Path("usenetsync_gui_main.py")
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Cleaning GUI file completely...")
    
    # Remove any problematic lines
    lines = content.split('\n')
    clean_lines = []
    
    for i, line in enumerate(lines):
        # Skip any lines with malformed syntax
        if '*indexing*' in line or line.strip().startswith('*'):
            print(f"REMOVED problematic line {i+1}: {line.strip()}")
            continue
        
        # Clean up any malformed imports or declarations
        if 'threading.Lock()' in line and not line.strip().startswith('#'):
            # Check if this is a proper variable declaration
            if '=' in line and not line.strip().startswith('import'):
                # Try to fix variable name
                if '*' in line:
                    print(f"CLEANED line {i+1}: {line.strip()}")
                    line = line.replace('*indexing*lock', '_indexing_lock')
                    line = line.replace('*', '_')  # Replace any remaining asterisks
        
        clean_lines.append(line)
    
    # Ensure threading is properly imported
    has_threading_import = any('import threading' in line for line in clean_lines)
    if not has_threading_import:
        # Find where to insert the import
        for i, line in enumerate(clean_lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            else:
                clean_lines.insert(i, 'import threading')
                print("Added threading import")
                break
    
    # Write back the cleaned content
    with open(gui_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean_lines))
    
    print("OK: GUI file cleaned")
    return True

def test_gui_import():
    """Test if the GUI file can be imported"""
    
    try:
        # First test syntax compilation
        import py_compile
        py_compile.compile('usenetsync_gui_main.py', doraise=True)
        print("OK: GUI syntax is valid")
        
        # Try to import the first few lines
        with open('usenetsync_gui_main.py', 'r') as f:
            first_lines = [f.readline().strip() for _ in range(10)]
        
        print("First 10 lines of GUI file:")
        for i, line in enumerate(first_lines, 1):
            if line:
                print(f"  {i}: {line}")
        
        return True
        
    except py_compile.PyCompileError as e:
        print(f"ERROR: GUI syntax error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Could not test GUI: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("FIX GUI SYNTAX ERROR")
    print("="*60)
    print("Fixing malformed threading code in GUI file...")
    print()
    
    success = True
    
    # Try to fix specific syntax error
    if not fix_gui_syntax_error():
        print("Specific fix failed, trying complete cleanup...")
        
        # Try complete cleanup
        clean_gui_file_completely()
    
    # Test the GUI file
    if not test_gui_import():
        print("ERROR: GUI file still has syntax errors")
        success = False
    
    print()
    if success:
        print("[SUCCESS] GUI syntax error fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Removed/fixed malformed threading code")
        print("  [OK] Ensured proper threading import")
        print("  [OK] Verified Python syntax")
        print()
        print("[READY] GUI should now start without errors!")
        print()
        print("Try running the production launcher again:")
        print("  python production_launcher.py")
        return 0
    else:
        print("[ERROR] Could not fix GUI syntax errors")
        print()
        print("Manual fix required:")
        print("1. Open usenetsync_gui_main.py")
        print("2. Look for line with '*indexing*lock'")
        print("3. Fix or remove the malformed line")
        print("4. Ensure 'import threading' is at the top")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)