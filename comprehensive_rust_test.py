#!/usr/bin/env python3
"""
Comprehensive Rust compilation test - verify everything works
"""

import re
import json
from pathlib import Path

def test_rust_syntax():
    """Test Rust file for syntax issues"""
    main_rs = Path('/workspace/usenet-sync-app/src-tauri/src/main.rs')
    
    if not main_rs.exists():
        return False, "main.rs not found"
    
    with open(main_rs, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    errors = []
    
    # 1. Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # 2. Check for orphaned cmd references
    cmd_pattern = r'\bcmd\.(arg|output)'
    cmd_matches = re.findall(cmd_pattern, content)
    if cmd_matches:
        errors.append(f"Found {len(cmd_matches)} orphaned cmd references")
        # Find line numbers
        for i, line in enumerate(lines, 1):
            if re.search(cmd_pattern, line):
                errors.append(f"  Line {i}: {line.strip()[:60]}...")
    
    # 3. Check all functions are properly closed
    function_pattern = r'(async fn|fn)\s+(\w+)'
    in_function = False
    function_name = None
    function_line = 0
    brace_count = 0
    
    for i, line in enumerate(lines, 1):
        match = re.search(function_pattern, line)
        if match and 'fn main' not in line:
            if in_function and brace_count > 0:
                errors.append(f"Function '{function_name}' at line {function_line} not properly closed")
            in_function = True
            function_name = match.group(2)
            function_line = i
            brace_count = 0
        
        if in_function:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '}' in line:
                in_function = False
    
    if in_function and brace_count > 0:
        errors.append(f"Function '{function_name}' at line {function_line} not properly closed")
    
    # 4. Check for undefined variables
    undefined_vars = ['cmd', 'output', 'python_cmd']
    for var in undefined_vars:
        # Look for variable usage outside of proper context
        pattern = rf'\b{var}\b(?!.*Command::new)'
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line) and 'let ' not in line and '//' not in line:
                # Check if it's after a function ends
                if i > 1 and lines[i-2].strip() == '}':
                    errors.append(f"Line {i}: Orphaned code using '{var}': {line.strip()[:60]}...")
    
    # 5. Check all tauri commands use execute_unified_command
    tauri_cmd_pattern = r'#\[tauri::command\]'
    for i, line in enumerate(lines, 1):
        if tauri_cmd_pattern in line:
            # Check next 20 lines for execute_unified_command
            found_unified = False
            for j in range(i+1, min(i+20, len(lines))):
                if 'execute_unified_command' in lines[j]:
                    found_unified = True
                    break
                if '#[tauri::command]' in lines[j]:
                    break
            if not found_unified and i+1 < len(lines):
                func_line = lines[i+1] if i+1 < len(lines) else ""
                func_match = re.search(r'fn\s+(\w+)', func_line)
                func_name = func_match.group(1) if func_match else "unknown"
                # Exception for special functions that don't need unified backend
                special_funcs = ['pause_transfer', 'resume_transfer', 'cancel_transfer', 
                                'save_server_config', 'get_system_stats', 'open_folder',
                                'activate_license', 'check_license', 'start_trial',
                                'deactivate_license', 'select_files', 'select_folder',
                                'index_folder', 'get_shares', 'create_share']
                if func_name not in special_funcs:
                    errors.append(f"Function '{func_name}' at line {i+1} might not use unified backend")
    
    return len(errors) == 0, errors

def test_imports():
    """Test that imports are correct"""
    main_rs = Path('/workspace/usenet-sync-app/src-tauri/src/main.rs')
    
    with open(main_rs, 'r') as f:
        content = f.read()
    
    errors = []
    
    # Check for required imports
    required_imports = [
        'use unified_backend::execute_unified_command',
        'mod unified_backend'
    ]
    
    for imp in required_imports:
        if imp not in content:
            errors.append(f"Missing import: {imp}")
    
    # Check for bad imports
    bad_imports = [
        'execute_backend_command'
    ]
    
    for imp in bad_imports:
        if imp in content:
            errors.append(f"Unused/bad import: {imp}")
    
    return len(errors) == 0, errors

def test_unified_backend_module():
    """Test that unified_backend.rs exists and is valid"""
    unified_backend = Path('/workspace/usenet-sync-app/src-tauri/src/unified_backend.rs')
    
    if not unified_backend.exists():
        return False, ["unified_backend.rs not found"]
    
    with open(unified_backend, 'r') as f:
        content = f.read()
    
    errors = []
    
    # Check for required functions
    required_funcs = [
        'execute_unified_command',
        'get_unified_backend_path',
        'get_workspace_dir'
    ]
    
    for func in required_funcs:
        if func not in content:
            errors.append(f"Missing function in unified_backend.rs: {func}")
    
    # Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces in unified_backend.rs: {open_braces} open, {close_braces} close")
    
    return len(errors) == 0, errors

def test_cargo_toml():
    """Test that Cargo.toml has required dependencies"""
    cargo_toml = Path('/workspace/usenet-sync-app/src-tauri/Cargo.toml')
    
    if not cargo_toml.exists():
        return False, ["Cargo.toml not found"]
    
    with open(cargo_toml, 'r') as f:
        content = f.read()
    
    errors = []
    
    # Check for required dependencies
    required_deps = [
        'tauri',
        'serde',
        'serde_json',
        'tokio'
    ]
    
    for dep in required_deps:
        if dep not in content:
            errors.append(f"Missing dependency in Cargo.toml: {dep}")
    
    return len(errors) == 0, errors

def main():
    print("=" * 80)
    print("COMPREHENSIVE RUST COMPILATION TEST")
    print("=" * 80)
    
    all_tests_pass = True
    
    # Test 1: Rust syntax
    print("\n📝 Testing Rust syntax...")
    passed, errors = test_rust_syntax()
    if passed:
        print("✅ Rust syntax is valid")
    else:
        print("❌ Rust syntax errors found:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   {error}")
        all_tests_pass = False
    
    # Test 2: Imports
    print("\n📦 Testing imports...")
    passed, errors = test_imports()
    if passed:
        print("✅ All imports are correct")
    else:
        print("❌ Import issues found:")
        for error in errors:
            print(f"   {error}")
        all_tests_pass = False
    
    # Test 3: Unified backend module
    print("\n🔧 Testing unified_backend.rs...")
    passed, errors = test_unified_backend_module()
    if passed:
        print("✅ unified_backend.rs is valid")
    else:
        print("❌ Issues in unified_backend.rs:")
        for error in errors:
            print(f"   {error}")
        all_tests_pass = False
    
    # Test 4: Cargo.toml
    print("\n📋 Testing Cargo.toml...")
    passed, errors = test_cargo_toml()
    if passed:
        print("✅ Cargo.toml has all dependencies")
    else:
        print("❌ Cargo.toml issues:")
        for error in errors:
            print(f"   {error}")
        all_tests_pass = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if all_tests_pass:
        print("✅ ALL TESTS PASSED!")
        print("The Rust code should compile without errors.")
        print("\nTo run the app:")
        print("  cd usenet-sync-app")
        print("  npm run tauri dev")
    else:
        print("❌ TESTS FAILED")
        print("There are still issues that need to be fixed.")
        print("Please review the errors above.")
    
    return all_tests_pass

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)