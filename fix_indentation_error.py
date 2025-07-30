#!/usr/bin/env python3
"""
Fix the indentation error in main.py caused by the cleanup method replacement
"""

import shutil
from pathlib import Path

def fix_indentation_error():
    """Fix the indentation error in main.py"""
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("❌ main.py not found")
        return False
    
    # Create backup
    backup_file = main_file.with_suffix('.py.backup_indent_fix')
    try:
        shutil.copy2(main_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠ Could not create backup: {e}")
    
    # Read current content
    with open(main_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the problematic line around line 322-323
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for the function definition that's missing its body
        if line.strip().startswith('def ') and line.strip().endswith(':\n'):
            # This is a function definition
            next_line_idx = i + 1
            
            # Check if the next line is properly indented or is a docstring
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                
                # If next line is not indented properly, it's likely the issue
                if (next_line.strip() and 
                    not next_line.startswith('    ') and 
                    not next_line.startswith('\t')):
                    
                    # This function is missing its body - add a pass statement
                    fixed_lines.append(line)  # The function definition
                    if next_line.strip().startswith('"""'):
                        # It's a docstring that needs proper indentation
                        fixed_lines.append('    ' + next_line.lstrip())
                        i += 1
                    else:
                        # Add a pass statement
                        fixed_lines.append('    pass\n')
                        fixed_lines.append('\n')
                else:
                    fixed_lines.append(line)
            else:
                # Function at end of file with no body
                fixed_lines.append(line)
                fixed_lines.append('    pass\n')
        else:
            fixed_lines.append(line)
        
        i += 1
    
    # Write the fixed content
    with open(main_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed indentation errors in main.py")
    return True

def test_syntax():
    """Test if the fixed file has valid Python syntax"""
    try:
        import py_compile
        py_compile.compile('main.py', doraise=True)
        print("✅ Syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error still exists: {e}")
        return False

def restore_backup_and_apply_simple_fix():
    """Restore from backup and apply a simpler fix"""
    main_file = Path("main.py")
    
    # Look for the most recent backup
    backups = [
        "main.py.backup_all_cleanup",
        "main.py.backup_comprehensive", 
        "main.py.backup_final",
        "main.py.backup2"
    ]
    
    backup_to_restore = None
    for backup in backups:
        if Path(backup).exists():
            backup_to_restore = backup
            break
    
    if not backup_to_restore:
        print("❌ No backup found to restore from")
        return False
    
    print(f"🔄 Restoring from backup: {backup_to_restore}")
    
    # Restore backup
    shutil.copy2(backup_to_restore, main_file)
    
    # Apply simple fixes without complex regex
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple string replacements
    replacements = [
        ('self.monitoring.cleanup()', 'self.monitoring.shutdown()'),
        ('self.nntp.connection_pool.close()', 'self.nntp.connection_pool.close_all()'),
    ]
    
    fixes_applied = []
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            fixes_applied.append(f"{old} → {new}")
    
    # Write back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {len(fixes_applied)} simple fixes:")
    for fix in fixes_applied:
        print(f"  • {fix}")
    
    return True

def main():
    """Main fix function"""
    print("=" * 50)
    print("    Fixing Indentation Error")
    print("=" * 50)
    print()
    
    # First try to fix the indentation
    if fix_indentation_error():
        if test_syntax():
            print()
            print("✅ Indentation error fixed successfully!")
            return 0
        else:
            print("⚠ Syntax errors remain, trying backup restore...")
    
    # If that didn't work, restore from backup and apply simple fixes
    if restore_backup_and_apply_simple_fix():
        if test_syntax():
            print()
            print("✅ Restored from backup and applied simple fixes!")
            print()
            print("Test with: python test_backend_final.py")
            return 0
        else:
            print("❌ Still have syntax errors after backup restore")
            return 1
    else:
        print("❌ Could not fix the indentation error")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)