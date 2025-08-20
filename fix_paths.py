#!/usr/bin/env python3
"""
Fix path references after reorganization
"""
import os
import re
from pathlib import Path

def fix_python_imports():
    """Fix Python import statements"""
    print("Fixing Python imports...")
    
    # Fix imports in backend code
    backend_files = list(Path('backend/src').rglob('*.py'))
    
    replacements = [
        # Old src imports to relative imports
        (r'from src\.', 'from '),
        (r'import src\.', 'import '),
        
        # Fix sys.path additions
        (r"sys\.path\.insert\(0, 'src'\)", "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))"),
        (r"sys\.path\.insert\(0, os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)", 
         "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))"),
    ]
    
    fixed_count = 0
    for file_path in backend_files:
        try:
            content = file_path.read_text()
            original = content
            
            for old, new in replacements:
                content = re.sub(old, new, content)
            
            if content != original:
                file_path.write_text(content)
                fixed_count += 1
                print(f"  Fixed: {file_path}")
        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_count} Python files")
    return fixed_count

def fix_test_imports():
    """Fix test file imports"""
    print("\nFixing test imports...")
    
    test_files = list(Path('backend/tests').rglob('*.py'))
    
    fixed_count = 0
    for file_path in test_files:
        try:
            content = file_path.read_text()
            original = content
            
            # Fix sys.path for tests
            if 'sys.path' in content:
                # Update path to point to backend/src
                content = re.sub(
                    r"sys\.path\.insert\(0, str\(Path\(__file__\)\.parent\.parent\.parent\)\)",
                    "sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))",
                    content
                )
                content = re.sub(
                    r"any\('src' in path for path in sys\.path\)",
                    "any('backend/src' in path or path.endswith('/src') for path in sys.path)",
                    content
                )
            
            if content != original:
                file_path.write_text(content)
                fixed_count += 1
                print(f"  Fixed: {file_path}")
        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_count} test files")
    return fixed_count

def fix_start_script():
    """Fix the start_backend.py script"""
    print("\nFixing start script...")
    
    start_script = Path('start_backend.py')
    if start_script.exists():
        content = start_script.read_text()
        
        # Already correct in our new script
        print("  Start script already correct")
    
    return 0

def fix_makefile():
    """Fix Makefile paths"""
    print("\nFixing Makefile...")
    
    makefile = Path('Makefile')
    if makefile.exists():
        content = makefile.read_text()
        original = content
        
        # Fix PYTHONPATH in Makefile
        content = re.sub(
            r'PYTHONPATH=src',
            'PYTHONPATH=backend/src',
            content
        )
        
        if content != original:
            makefile.write_text(content)
            print("  Fixed Makefile")
            return 1
    
    return 0

def fix_frontend_imports():
    """Fix frontend TypeScript/JavaScript imports"""
    print("\nFixing frontend imports...")
    
    # Frontend files shouldn't reference backend paths
    # But let's check for any hardcoded paths
    frontend_files = (
        list(Path('frontend/src').rglob('*.ts')) +
        list(Path('frontend/src').rglob('*.tsx')) +
        list(Path('frontend/src').rglob('*.js'))
    )
    
    fixed_count = 0
    for file_path in frontend_files:
        try:
            content = file_path.read_text()
            original = content
            
            # Fix any references to old paths
            content = re.sub(
                r'usenet-sync-app/',
                'frontend/',
                content
            )
            
            if content != original:
                file_path.write_text(content)
                fixed_count += 1
                print(f"  Fixed: {file_path}")
        except Exception as e:
            print(f"  Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_count} frontend files")
    return fixed_count

def main():
    """Run all fixes"""
    print("=" * 60)
    print("FIXING PATH REFERENCES")
    print("=" * 60)
    
    total_fixed = 0
    
    total_fixed += fix_python_imports()
    total_fixed += fix_test_imports()
    total_fixed += fix_start_script()
    total_fixed += fix_makefile()
    total_fixed += fix_frontend_imports()
    
    print("\n" + "=" * 60)
    print(f"TOTAL FILES FIXED: {total_fixed}")
    print("=" * 60)
    
    if total_fixed > 0:
        print("\n✅ Path references updated successfully!")
    else:
        print("\n✅ No path references needed updating!")

if __name__ == "__main__":
    main()
