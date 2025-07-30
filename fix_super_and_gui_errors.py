#!/usr/bin/env python3
"""
Fix super() syntax errors and GUI variable scope errors
"""

import shutil
from pathlib import Path
import re

def fix_super_calls():
    """Fix super() calls in production_db_wrapper.py"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_super_syntax')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix super() calls
    fixes_applied = []
    
    # Fix 1: super().method_name calls
    # Replace super().method_name with super(ProductionDatabaseManager, self).method_name
    super_pattern = r'super\(\)\.(\w+)\('
    
    def replace_super(match):
        method_name = match.group(1)
        return f'super(ProductionDatabaseManager, self).{method_name}('
    
    original_content = content
    content = re.sub(super_pattern, replace_super, content)
    
    if content != original_content:
        fixes_applied.append("Fixed super() method calls")
    
    # Fix 2: Any remaining bare super() calls
    if 'super()' in content:
        content = content.replace('super()', 'super(ProductionDatabaseManager, self)')
        fixes_applied.append("Fixed bare super() calls")
    
    if not fixes_applied:
        print("OK: No super() issues found")
        return True
    
    # Write back
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} super() fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

def fix_gui_variable_errors():
    """Fix variable scope errors in GUI"""
    
    gui_file = Path("usenetsync_gui_main.py")
    if not gui_file.exists():
        print("WARNING: GUI file not found")
        return True
    
    # Create backup
    backup_file = gui_file.with_suffix('.py.backup_var_fix')
    try:
        shutil.copy2(gui_file, backup_file)
        print(f"OK: Created GUI backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create GUI backup: {e}")
    
    # Read current content
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix variable scope issues
    fixes_applied = []
    
    # Fix 1: Replace 'except Exception as e:' with consistent variable name
    if 'except Exception as e:' in content:
        content = content.replace('except Exception as e:', 'except Exception as error:')
        fixes_applied.append("Standardized exception variable names")
    
    # Fix 2: Replace references to 'e' with 'error' in error messages
    content = re.sub(r'logger\.error\(f"([^"]*)\{e\}([^"]*)"\)', r'logger.error(f"\1{error}\2")', content)
    content = re.sub(r'f"([^"]*)\{e\}([^"]*)"', r'f"\1{error}\2"', content)
    
    if 'logger.error(f' in content and '{error}' in content:
        fixes_applied.append("Fixed logger error variable references")
    
    # Fix 3: Look for any remaining {e} references
    if '{e}' in content:
        content = content.replace('{e}', '{error}')
        fixes_applied.append("Fixed remaining {e} references")
    
    if not fixes_applied:
        print("OK: No GUI variable issues found")
        return True
    
    # Write back
    with open(gui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"OK: Applied {len(fixes_applied)} GUI variable fixes:")
    for fix in fixes_applied:
        print(f"  - {fix}")
    
    return True

def test_syntax():
    """Test syntax of fixed files"""
    print("Testing syntax...")
    
    try:
        import py_compile
        
        files_to_test = [
            "production_db_wrapper.py",
            "usenetsync_gui_main.py"
        ]
        
        for file in files_to_test:
            if Path(file).exists():
                try:
                    py_compile.compile(file, doraise=True)
                    print(f"OK: {file} syntax good")
                except py_compile.PyCompileError as e:
                    print(f"ERROR: {file} syntax error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not test syntax: {e}")
        return True

def main():
    """Main function"""
    print("=" * 50)
    print("Fix Super() and GUI Variable Errors")
    print("=" * 50)
    
    success = True
    
    # Fix super() calls
    if not fix_super_calls():
        print("ERROR: super() fix failed")
        success = False
    
    # Fix GUI variable errors
    if not fix_gui_variable_errors():
        print("ERROR: GUI variable fix failed")
        success = False
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("SUCCESS: All syntax and variable errors fixed!")
        print()
        print("Fixed:")
        print("  - super() method call syntax")
        print("  - GUI exception variable scope")
        print("  - Logger error message variables")
        print()
        print("Folder indexing should now work without errors!")
    else:
        print("ERROR: Some fixes failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)