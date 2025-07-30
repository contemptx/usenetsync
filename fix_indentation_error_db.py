#!/usr/bin/env python3
"""
Fix indentation error in production_db_wrapper.py
"""

import shutil
from pathlib import Path

def fix_indentation_error():
    """Fix the indentation error in production_db_wrapper.py"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_indent_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix indentation issues
    fixed_lines = []
    in_method = False
    expected_indent = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Skip empty lines
        if line.strip() == "":
            fixed_lines.append(line)
            continue
        
        # Calculate current indentation
        current_indent = len(line) - len(line.lstrip())
        
        # Detect method definitions
        if line.strip().startswith('def '):
            in_method = True
            expected_indent = current_indent + 4
            fixed_lines.append(line)
            continue
        
        # Detect class definitions
        if line.strip().startswith('class '):
            in_method = False
            expected_indent = current_indent + 4
            fixed_lines.append(line)
            continue
        
        # Fix line 346 specifically if it's problematic
        if line_num == 346 and line.strip() == 'conn.commit()':
            # This should be indented to match the surrounding code
            # Look at previous lines to determine correct indentation
            for j in range(i-1, max(0, i-10), -1):
                prev_line = lines[j]
                if prev_line.strip() and not prev_line.strip().startswith('#'):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    # If previous line is a statement, use same indent
                    if not prev_line.strip().endswith(':'):
                        correct_line = ' ' * prev_indent + line.lstrip()
                        fixed_lines.append(correct_line)
                        print(f"FIXED line {line_num}: Adjusted indentation from {current_indent} to {prev_indent}")
                        break
                    else:
                        # Previous line ends with :, so we need to be indented more
                        correct_line = ' ' * (prev_indent + 4) + line.lstrip()
                        fixed_lines.append(correct_line)
                        print(f"FIXED line {line_num}: Adjusted indentation from {current_indent} to {prev_indent + 4}")
                        break
            else:
                # Fallback: use standard method indentation
                correct_line = '            ' + line.lstrip()  # 12 spaces for method body
                fixed_lines.append(correct_line)
                print(f"FIXED line {line_num}: Used fallback indentation")
            continue
        
        # For other lines, check if indentation looks wrong
        if current_indent % 4 != 0 and line.strip():
            # Round to nearest multiple of 4
            correct_indent = ((current_indent + 2) // 4) * 4
            correct_line = ' ' * correct_indent + line.lstrip()
            fixed_lines.append(correct_line)
            if line_num >= 340 and line_num <= 350:  # Only report fixes near the error
                print(f"FIXED line {line_num}: Adjusted indentation from {current_indent} to {correct_indent}")
        else:
            fixed_lines.append(line)
    
    # Write the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("OK: Fixed indentation issues")
    return True

def test_syntax():
    """Test if the file has valid Python syntax now"""
    try:
        import py_compile
        py_compile.compile('production_db_wrapper.py', doraise=True)
        print("OK: Syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"ERROR: Syntax error still exists: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Could not test syntax: {e}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("Fix Indentation Error")
    print("=" * 50)
    
    if fix_indentation_error():
        if test_syntax():
            print()
            print("SUCCESS: Indentation error fixed!")
            print()
            print("You can now run the GUI:")
            print("  python production_launcher.py")
            return 0
        else:
            print()
            print("ERROR: Syntax errors remain after fix")
            print("You may need to manually check the indentation")
            return 1
    else:
        print("ERROR: Could not fix indentation")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)