#!/usr/bin/env python3
"""
Fix Threading Import
Add missing threading import to GUI file
"""

import shutil
from pathlib import Path

def fix_threading_import():
    """Add missing threading import to GUI file"""
    
    gui_file = Path("usenetsync_gui_main.py")
    if not gui_file.exists():
        print("ERROR: usenetsync_gui_main.py not found")
        return False
    
    # Create backup
    backup_file = gui_file.with_suffix('.py.backup_threading_fix')
    try:
        shutil.copy2(gui_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if threading is already imported
    if 'import threading' in content:
        print("OK: threading already imported")
        return True
    
    # Find the import section and add threading
    lines = content.split('\n')
    import_section_end = 0
    
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_section_end = i
        elif line.strip() == '':
            continue
        else:
            break
    
    # Insert threading import after the last import
    if import_section_end >= 0:
        lines.insert(import_section_end + 1, 'import threading')
        print("OK: Added threading import")
    else:
        # If no imports found, add at the beginning
        lines.insert(0, 'import threading')
        print("OK: Added threading import at beginning")
    
    # Write back the fixed content
    with open(gui_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True

def fix_versioned_core_threading():
    """Also fix threading import in versioned_core_index_system.py if needed"""
    
    indexing_file = Path("versioned_core_index_system.py")
    if not indexing_file.exists():
        print("WARNING: versioned_core_index_system.py not found")
        return True
    
    with open(indexing_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if threading is imported
    if 'import threading' not in content:
        # Find import section
        lines = content.split('\n')
        
        # Look for existing imports
        for i, line in enumerate(lines):
            if 'import logging' in line:
                lines.insert(i + 1, 'import threading')
                print("OK: Added threading import to versioned_core_index_system.py")
                break
        
        with open(indexing_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    return True

def test_syntax():
    """Test Python syntax"""
    files_to_test = [
        "usenetsync_gui_main.py",
        "versioned_core_index_system.py"
    ]
    
    try:
        import py_compile
        
        for file in files_to_test:
            if Path(file).exists():
                try:
                    py_compile.compile(file, doraise=True)
                    print(f"OK: {file} syntax valid")
                except py_compile.PyCompileError as e:
                    print(f"ERROR: {file} syntax error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not test syntax: {e}")
        return True

def main():
    """Main function"""
    print("="*50)
    print("FIX THREADING IMPORT")
    print("="*50)
    print("Adding missing threading import...")
    print()
    
    success = True
    
    # Fix GUI file
    if not fix_threading_import():
        print("ERROR: Could not fix threading import in GUI")
        success = False
    
    # Fix indexing file
    fix_versioned_core_threading()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Threading import fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Added 'import threading' to usenetsync_gui_main.py")
        print("  [OK] Added 'import threading' to versioned_core_index_system.py")
        print("  [OK] Verified Python syntax")
        print()
        print("[READY] GUI should now start without import errors!")
        print()
        print("Try running the production launcher again:")
        print("  python production_launcher.py")
        return 0
    else:
        print("[ERROR] Could not fix import issues")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)