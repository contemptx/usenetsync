#!/usr/bin/env python3
"""
Fix Import Order in GUI File
Move threading import to the top before it's used
"""

import shutil
from pathlib import Path

def fix_import_order():
    """Fix the import order in GUI file"""
    
    gui_file = Path("usenetsync_gui_main.py")
    if not gui_file.exists():
        print("ERROR: usenetsync_gui_main.py not found")
        return False
    
    # Create backup
    backup_file = gui_file.with_suffix('.py.backup_import_order_fix')
    try:
        shutil.copy2(gui_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines
    lines = content.split('\n')
    
    # Find the threading code at the top and the shebang/imports section
    threading_code_lines = []
    other_lines = []
    in_threading_section = True
    
    for i, line in enumerate(lines):
        if i < 20 and ('_indexing' in line or line.strip().startswith('def _is_indexing') or line.strip().startswith('def _set_indexing')):
            # This is part of the threading code at the top
            if in_threading_section:
                threading_code_lines.append(line)
                continue
        
        # Mark end of threading section when we hit the shebang
        if line.startswith('#!/usr/bin/env'):
            in_threading_section = False
        
        other_lines.append(line)
    
    # Now rebuild the file with proper order
    new_lines = []
    
    # Start with shebang and docstring
    in_header = True
    for line in other_lines:
        if in_header:
            new_lines.append(line)
            # Add imports right after the docstring
            if line.strip().endswith('"""') and len(line.strip()) > 3:
                # Add threading import first
                new_lines.append('')
                new_lines.append('import threading')
                new_lines.append('import tkinter as tk')
                new_lines.append('from tkinter import ttk, messagebox, filedialog')
                new_lines.append('import logging')
                new_lines.append('import sys')
                new_lines.append('import os')
                new_lines.append('import time')
                new_lines.append('from pathlib import Path')
                new_lines.append('from typing import Optional, Dict, Any, Callable')
                new_lines.append('from datetime import datetime')
                new_lines.append('')
                
                # Add the threading code after imports
                for thread_line in threading_code_lines:
                    new_lines.append(thread_line)
                new_lines.append('')
                
                in_header = False
        else:
            # Skip existing import lines to avoid duplicates
            if (line.startswith('import ') or line.startswith('from ') or 
                line.strip() in ['', '# Add parent directory to path for backend imports']):
                continue
            else:
                new_lines.append(line)
    
    # Write the fixed content
    with open(gui_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("OK: Fixed import order - threading now imported before use")
    return True

def test_gui_syntax():
    """Test GUI syntax"""
    try:
        import py_compile
        py_compile.compile('usenetsync_gui_main.py', doraise=True)
        print("OK: GUI syntax is now valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: GUI syntax error: {e}")
        return False

def main():
    """Main function"""
    print("="*50)
    print("FIX IMPORT ORDER")
    print("="*50)
    print("Moving threading import before its usage...")
    print()
    
    success = True
    
    # Fix import order
    if not fix_import_order():
        print("ERROR: Could not fix import order")
        success = False
    
    # Test syntax
    if not test_gui_syntax():
        print("ERROR: Syntax still invalid")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Import order fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Moved 'import threading' to top of file")
        print("  [OK] Organized all imports in proper order")
        print("  [OK] Moved threading code after imports")
        print("  [OK] Verified Python syntax")
        print()
        print("[READY] GUI should now start without import errors!")
        print()
        print("Try running the production launcher again:")
        print("  python production_launcher.py")
        return 0
    else:
        print("[ERROR] Could not fix import order")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)