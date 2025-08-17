#!/usr/bin/env python3
"""
Fix import paths for the new project structure
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Define import mappings
IMPORT_MAPPINGS = {
    # Database imports
    'enhanced_database_manager': 'src.database.enhanced_database_manager',
    'production_db_wrapper': 'src.database.production_db_wrapper',
    'init_database': 'src.database.init_database',
    'ensure_database_schema': 'src.database.ensure_database_schema',
    'ensure_db_schema': 'src.database.ensure_db_schema',
    
    # Security imports
    'enhanced_security_system': 'src.security.enhanced_security_system',
    'security_audit_system': 'src.security.security_audit_system',
    'user_management': 'src.security.user_management',
    'encrypted_index_cache': 'src.security.encrypted_index_cache',
    
    # Networking imports
    'production_nntp_client': 'src.networking.production_nntp_client',
    'connection_pool': 'src.networking.connection_pool',
    
    # Upload imports
    'enhanced_upload_system': 'src.upload.enhanced_upload_system',
    'upload_queue_manager': 'src.upload.upload_queue_manager',
    'segment_packing_system': 'src.upload.segment_packing_system',
    'publishing_system': 'src.upload.publishing_system',
    
    # Download imports
    'enhanced_download_system': 'src.download.enhanced_download_system',
    'segment_retrieval_system': 'src.download.segment_retrieval_system',
    
    # Indexing imports
    'versioned_core_index_system': 'src.indexing.versioned_core_index_system',
    'simplified_binary_index': 'src.indexing.simplified_binary_index',
    'share_id_generator': 'src.indexing.share_id_generator',
    
    # Monitoring imports
    'monitoring_system': 'src.monitoring.monitoring_system',
    'monitoring_dashboard': 'src.monitoring.monitoring_dashboard',
    'monitoring_cli': 'src.monitoring.monitoring_cli',
    'production_monitoring': 'src.monitoring.production_monitoring',
    'usenet_sync_monitor': 'src.monitoring.usenet_sync_monitor',
    
    # Config imports
    'configuration_manager': 'src.config.configuration_manager',
    'newsgroup_config': 'src.config.newsgroup_config',
    'setup_config': 'src.config.setup_config',
    'secure_config': 'src.config.secure_config',
    
    # Core imports
    'main': 'src.core.main',
    'usenet_sync_integrated': 'src.core.usenet_sync_integrated',
}

def get_python_files() -> List[Path]:
    """Get all Python files in src directory"""
    src_dir = Path('src')
    python_files = []
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def fix_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Fix imports in a single file"""
    changes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 'from X import Y' style imports
    for old_module, new_module in IMPORT_MAPPINGS.items():
        # Pattern for: from old_module import Something
        pattern = rf'^from {re.escape(old_module)} import (.+)$'
        replacement = rf'from {new_module} import \1'
        
        content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            changes.append(f"Fixed {count} imports of '{old_module}'")
    
    # Fix 'import X' style imports (less common for our modules)
    for old_module, new_module in IMPORT_MAPPINGS.items():
        pattern = rf'^import {re.escape(old_module)}$'
        replacement = f'import {new_module}'
        
        content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            changes.append(f"Fixed {count} direct imports of '{old_module}'")
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return len(changes), changes

def add_relative_imports(file_path: Path) -> Tuple[int, List[str]]:
    """Add relative imports for files in the same package"""
    changes = []
    
    # Determine the package of this file
    relative_path = file_path.relative_to('src')
    package_parts = relative_path.parent.parts
    
    if not package_parts:
        return 0, changes
    
    current_package = package_parts[0]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Find imports from the same package and convert to relative
    for module_name, full_path in IMPORT_MAPPINGS.items():
        if full_path.startswith(f'src.{current_package}.'):
            # This module is in the same package
            module_only = full_path.split('.')[-1]
            
            # Check if we're importing from this module
            pattern = rf'^from {re.escape(full_path)} import (.+)$'
            
            # Check if this import exists
            if re.search(pattern, content, flags=re.MULTILINE):
                # Convert to relative import
                replacement = rf'from .{module_only} import \1'
                content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
                
                if count > 0:
                    changes.append(f"Converted {count} imports to relative for '{module_only}'")
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return len(changes), changes

def main():
    """Main function to fix all imports"""
    print("=" * 60)
    print("FIXING IMPORT PATHS")
    print("=" * 60)
    print()
    
    # Get all Python files
    python_files = get_python_files()
    print(f"Found {len(python_files)} Python files in src/")
    print()
    
    total_changes = 0
    files_changed = 0
    
    for file_path in python_files:
        print(f"Processing: {file_path}")
        
        # Fix absolute imports
        num_changes, changes = fix_imports_in_file(file_path)
        
        # Optionally add relative imports for same-package modules
        # num_relative, relative_changes = add_relative_imports(file_path)
        # num_changes += num_relative
        # changes.extend(relative_changes)
        
        if num_changes > 0:
            files_changed += 1
            total_changes += num_changes
            for change in changes:
                print(f"  - {change}")
        else:
            print("  - No changes needed")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {len(python_files)}")
    print(f"Files changed: {files_changed}")
    print(f"Total import fixes: {total_changes}")
    
    # Also fix test files
    print()
    print("Fixing test imports...")
    test_file = Path('tests/e2e/test_production_e2e.py')
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the imports in test file
        content = content.replace(
            'from src.core.main import UsenetSync',
            'from src.core.main import UsenetSync'
        )
        content = content.replace(
            'from src.config.configuration_manager import ConfigurationManager',
            'from src.config.configuration_manager import ConfigurationManager'
        )
        content = content.replace(
            'from src.security.enhanced_security_system import ShareType',
            'from src.security.enhanced_security_system import ShareType'
        )
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed imports in {test_file}")
    
    print()
    print("Import fixing complete!")
    print()
    print("Next steps:")
    print("1. Set environment variables:")
    print("   export NNTP_USERNAME='your_username'")
    print("   export NNTP_PASSWORD='your_password'")
    print("2. Run tests:")
    print("   python run_tests.py --test test_01_connection_health")

if __name__ == "__main__":
    main()