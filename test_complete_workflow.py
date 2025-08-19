#!/usr/bin/env python3
"""
Test the COMPLETE workflow: Add → Index → Segment → Upload → Publish → Download
Track which database tables are actually used
"""

import subprocess
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime

def get_table_counts():
    """Get row counts for all tables"""
    conn = sqlite3.connect('/home/ubuntu/.usenetsync/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    counts = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        counts[table_name] = cursor.fetchone()[0]
    conn.close()
    return counts

def run_cmd(cmd):
    """Run CLI command and return result"""
    result = subprocess.run(
        f"python3 src/cli.py {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd="/workspace"
    )
    
    # Filter out expected warnings
    stderr_lines = result.stderr.split('\n')
    real_errors = [line for line in stderr_lines 
                   if line and 
                   'ALTER TABLE' not in line and
                   'ADD COLUMN' not in line and
                   'last_operation' not in line and
                   'Params: None' not in line]
    
    try:
        data = json.loads(result.stdout) if result.stdout else None
        return {
            'success': result.returncode == 0, 
            'data': data,
            'errors': real_errors[:3] if real_errors else None
        }
    except:
        return {
            'success': result.returncode == 0, 
            'data': result.stdout,
            'errors': real_errors[:3] if real_errors else None
        }

print("=" * 70)
print("COMPLETE WORKFLOW TEST WITH TABLE TRACKING")
print("=" * 70)

# Get initial table state
initial_counts = get_table_counts()
print("\nInitial non-empty tables:")
for table, count in initial_counts.items():
    if count > 0:
        print(f"  {table}: {count} rows")

# Create test folder
test_dir = Path('/tmp/workflow_test')
test_dir.mkdir(exist_ok=True)
for i in range(2):  # Just 2 small files for quick testing
    (test_dir / f'test_{i}.txt').write_text(f'Test content {i}\n' * 10)

print(f"\n✓ Created test folder: {test_dir}")

# Track table changes after each operation
table_changes = {}

# 1. ADD FOLDER
print("\n" + "="*50)
print("1. ADD FOLDER")
print("-"*50)
before = get_table_counts()
result = run_cmd(f'add-folder --path "{test_dir}" --name "Workflow Test"')
after = get_table_counts()

if result['success'] and result['data']:
    folder_id = result['data'].get('folder_id')
    print(f"✅ Added folder: {folder_id}")
    
    # Check what changed
    changes = []
    for table in after:
        if after[table] != before[table]:
            changes.append(f"{table}: +{after[table] - before[table]}")
    if changes:
        print("Tables modified:")
        for change in changes:
            print(f"  - {change}")
else:
    print(f"❌ Failed: {result.get('errors', 'Unknown error')}")
    exit(1)

# 2. INDEX FOLDER
print("\n" + "="*50)
print("2. INDEX FOLDER")
print("-"*50)
before = get_table_counts()
result = run_cmd(f'index-managed-folder --folder-id {folder_id}')
after = get_table_counts()

if result['success']:
    print(f"✅ Indexed: {result['data'].get('files_indexed', 0)} files")
    
    changes = []
    for table in after:
        if after[table] != before[table]:
            changes.append(f"{table}: +{after[table] - before[table]}")
    if changes:
        print("Tables modified:")
        for change in changes:
            print(f"  - {change}")
else:
    print(f"❌ Failed: {result.get('errors', 'Unknown error')}")

# 3. SEGMENT FOLDER
print("\n" + "="*50)
print("3. SEGMENT FOLDER")
print("-"*50)
before = get_table_counts()
result = run_cmd(f'segment-folder --folder-id {folder_id}')
after = get_table_counts()

if result['success']:
    print(f"✅ Segmented: {result['data'].get('total_segments', 0)} segments")
    
    changes = []
    for table in after:
        if after[table] != before[table]:
            changes.append(f"{table}: +{after[table] - before[table]}")
    if changes:
        print("Tables modified:")
        for change in changes:
            print(f"  - {change}")
else:
    print(f"❌ Failed: {result.get('errors', 'Unknown error')}")

# 4. UPLOAD FOLDER (This might fail without real Usenet connection)
print("\n" + "="*50)
print("4. UPLOAD FOLDER")
print("-"*50)
before = get_table_counts()
result = run_cmd(f'upload-folder --folder-id {folder_id}')
after = get_table_counts()

if result['success']:
    print(f"✅ Uploaded successfully")
    
    changes = []
    for table in after:
        if after[table] != before[table]:
            changes.append(f"{table}: +{after[table] - before[table]}")
    if changes:
        print("Tables modified:")
        for change in changes:
            print(f"  - {change}")
else:
    print(f"⚠️  Upload failed (expected without real Usenet): {result.get('errors', ['Unknown'])[0] if result.get('errors') else 'Unknown'}")
    # Continue anyway to see what tables would be used

# 5. PUBLISH FOLDER
print("\n" + "="*50)
print("5. PUBLISH FOLDER")
print("-"*50)
before = get_table_counts()
result = run_cmd(f'publish-folder --folder-id {folder_id}')
after = get_table_counts()

if result['success']:
    print(f"✅ Published: Share ID = {result['data'].get('share_id', 'Unknown')}")
    
    changes = []
    for table in after:
        if after[table] != before[table]:
            changes.append(f"{table}: +{after[table] - before[table]}")
    if changes:
        print("Tables modified:")
        for change in changes:
            print(f"  - {change}")
else:
    print(f"⚠️  Publish failed: {result.get('errors', ['Unknown'])[0] if result.get('errors') else 'Unknown'}")

# 6. Check for download command
print("\n" + "="*50)
print("6. DOWNLOAD (Checking if command exists)")
print("-"*50)
result = run_cmd('download-folder --help')
if 'download-folder' in str(result['data']):
    print("✅ Download command exists")
else:
    print("❌ Download command not found in CLI")

# Final summary
print("\n" + "="*70)
print("FINAL TABLE USAGE SUMMARY")
print("="*70)

final_counts = get_table_counts()
print("\nTables with data after workflow:")
tables_used = []
for table, count in final_counts.items():
    if count > 0:
        initial = initial_counts.get(table, 0)
        if count != initial:
            print(f"  {table}: {count} rows (changed from {initial})")
            tables_used.append(table)
        else:
            print(f"  {table}: {count} rows (unchanged)")

print(f"\nTotal tables modified during workflow: {len(tables_used)}")
print(f"Tables modified: {', '.join(tables_used)}")

# Check which tables are still empty
empty_tables = [table for table, count in final_counts.items() if count == 0]
print(f"\nStill empty tables ({len(empty_tables)}): {', '.join(empty_tables[:5])}...")
