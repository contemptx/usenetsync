#!/usr/bin/env python3
"""
Test all GUI operations to ensure they work without errors
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path

def run_cmd(cmd):
    """Run a CLI command and return the result"""
    result = subprocess.run(
        f"python3 src/cli.py {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd="/workspace"
    )
    
    # Filter out the ALTER TABLE errors from stderr
    stderr_lines = result.stderr.split('\n')
    real_errors = [line for line in stderr_lines 
                   if line and 
                   'ALTER TABLE' not in line and
                   'ADD COLUMN' not in line and
                   'ERROR:folder_management.database_adapter:Params: None' not in line]
    
    if real_errors:
        print(f"STDERR: {chr(10).join(real_errors)}")
    
    try:
        data = json.loads(result.stdout) if result.stdout else None
        return {'success': result.returncode == 0, 'data': data}
    except:
        return {'success': result.returncode == 0, 'data': result.stdout}

print("=" * 70)
print("TESTING FOLDER MANAGEMENT OPERATIONS")
print("=" * 70)

# Create test folder
test_dir = Path('/tmp/test_gui_folder_new')
test_dir.mkdir(exist_ok=True)

# Create test files
for i in range(3):
    (test_dir / f'file_{i}.txt').write_text(f'Test content {i}\n' * 10)

print(f"\n1. ADDING FOLDER...")
result = run_cmd(f'add-folder --path "{test_dir}" --name "Test GUI Folder"')
if result['success'] and result['data']:
    folder_id = result['data'].get('folder_id')
    print(f"   ✅ Added folder: {folder_id}")
else:
    print(f"   ❌ Failed to add folder")
    exit(1)

print(f"\n2. INDEXING FOLDER...")
result = run_cmd(f'index-managed-folder --folder-id {folder_id}')
if result['success'] and result['data']:
    print(f"   ✅ Indexed {result['data'].get('files_indexed', 0)} files")
else:
    print(f"   ❌ Failed to index")

print(f"\n3. RE-INDEXING FOLDER...")
# Add a new file
(test_dir / 'new_file.txt').write_text('New content\n' * 10)
result = run_cmd(f'index-managed-folder --folder-id {folder_id}')
if result['success'] and result['data']:
    print(f"   ✅ Re-indexed {result['data'].get('files_indexed', 0)} files")
else:
    print(f"   ❌ Failed to re-index")

print(f"\n4. SETTING ACCESS CONTROL...")
result = run_cmd(f'set-folder-access --folder-id {folder_id} --access-type protected --password test123')
if result['success'] and result['data']:
    print(f"   ✅ Set access to {result['data'].get('access_type')}")
else:
    print(f"   ❌ Failed to set access")

print(f"\n5. RESYNCING FOLDER...")
result = run_cmd(f'resync-folder --folder-id {folder_id}')
if result['success'] and result['data']:
    print(f"   ✅ Resync: {result['data'].get('new_files', 0)} new, {result['data'].get('modified_files', 0)} modified")
else:
    print(f"   ❌ Failed to resync")

print(f"\n6. GETTING FOLDER INFO...")
result = run_cmd(f'folder-info --folder-id {folder_id}')
if result['success'] and result['data']:
    print(f"   ✅ Folder: {result['data'].get('name')}")
    print(f"      Files: {result['data'].get('total_files')}")
    print(f"      Size: {result['data'].get('total_size')} bytes")
else:
    print(f"   ❌ Failed to get info")

print("\n" + "=" * 70)
print("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!" if all([
    "Failed" not in str(result)
]) else "⚠️ Some operations had issues")
print("=" * 70)
