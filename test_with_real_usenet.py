#!/usr/bin/env python3
"""
Test complete workflow with real Usenet credentials
"""

import subprocess
import json
import sqlite3
from pathlib import Path

def run_cmd(cmd):
    """Run CLI command and return result"""
    result = subprocess.run(
        f"python3 src/cli.py {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd="/workspace"
    )
    
    try:
        data = json.loads(result.stdout) if result.stdout else None
        return {'success': result.returncode == 0, 'data': data, 'stderr': result.stderr}
    except:
        return {'success': result.returncode == 0, 'data': result.stdout, 'stderr': result.stderr}

print("=" * 70)
print("TESTING WITH REAL USENET CONNECTION")
print("=" * 70)
print("\nServer: news.newshosting.com:563 (SSL)")
print("User: contemptx")
print("=" * 70)

# Create a small test folder
test_dir = Path('/tmp/usenet_test')
test_dir.mkdir(exist_ok=True)

# Create small test files
for i in range(2):
    content = f"Test file {i} for Usenet upload\n" * 50
    (test_dir / f'test_{i}.txt').write_text(content)

print(f"\n✓ Created test folder: {test_dir}")

# 1. Add folder
print("\n1. ADDING FOLDER...")
result = run_cmd(f'add-folder --path "{test_dir}" --name "Usenet Upload Test"')
if result['success'] and result['data']:
    folder_id = result['data'].get('folder_id')
    print(f"   ✅ Added: {folder_id}")
else:
    print(f"   ❌ Failed: {result.get('stderr', '')[:200]}")
    exit(1)

# 2. Index folder
print("\n2. INDEXING FOLDER...")
result = run_cmd(f'index-managed-folder --folder-id {folder_id}')
if result['success']:
    files = result['data'].get('files_indexed', 0)
    print(f"   ✅ Indexed: {files} files")
else:
    print(f"   ❌ Failed: {result.get('stderr', '')[:200]}")

# 3. Segment folder
print("\n3. SEGMENTING FOLDER...")
result = run_cmd(f'segment-folder --folder-id {folder_id}')
if result['success']:
    segments = result['data'].get('total_segments', 0)
    print(f"   ✅ Created: {segments} segments")
else:
    print(f"   ❌ Failed: {result.get('stderr', '')[:200]}")

# 4. Upload to Usenet
print("\n4. UPLOADING TO USENET...")
print("   Connecting to news.newshosting.com...")
result = run_cmd(f'upload-folder --folder-id {folder_id}')

if result['success'] and result['data']:
    uploaded = result['data'].get('uploaded', 0)
    failed = result['data'].get('failed', 0)
    total = result['data'].get('total_segments', 0)
    
    print(f"   Result: {uploaded}/{total} segments uploaded")
    if uploaded > 0:
        print(f"   ✅ UPLOAD SUCCESSFUL! {uploaded} segments uploaded to Usenet")
    elif failed > 0:
        print(f"   ⚠️ Upload attempted but failed: {failed} segments failed")
    else:
        print(f"   ❌ No segments uploaded")
else:
    error = str(result.get('stderr', ''))[:300]
    if 'Connection refused' in error:
        print("   ❌ Connection refused by server")
    elif 'Authentication' in error or '481' in error:
        print("   ❌ Authentication failed (check credentials)")
    elif 'ProductionNNTPClient' in error:
        print("   ❌ NNTP client error")
    else:
        print(f"   ❌ Error: {error}")

# 5. Publish folder
print("\n5. PUBLISHING FOLDER...")
result = run_cmd(f'publish-folder --folder-id {folder_id}')

if result['success'] and result['data']:
    share_id = result['data'].get('share_id')
    access_type = result['data'].get('access_type')
    
    if share_id:
        print(f"   ✅ PUBLISHED SUCCESSFULLY!")
        print(f"   Share ID: {share_id}")
        print(f"   Access Type: {access_type}")
    else:
        print(f"   ⚠️ Published but no share ID: {result['data']}")
else:
    error = str(result.get('stderr', ''))[:200] or str(result.get('data', ''))[:200]
    print(f"   ❌ Error: {error}")

# 6. Check database state
print("\n6. DATABASE STATE...")
conn = sqlite3.connect('/home/ubuntu/.usenetsync/data.db')
cursor = conn.cursor()

# Check segment states
cursor.execute('SELECT state, COUNT(*) FROM segments GROUP BY state')
print("   Segment states:")
for state, count in cursor.fetchall():
    print(f"     {state}: {count}")

# Check if any upload tables got populated
tables = ['uploads', 'upload_sessions', 'upload_queue', 'shares', 'publications']
print("   Table usage:")
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"     {table}: {count} rows ✓")

conn.close()

print("\n" + "=" * 70)
print("WORKFLOW TEST COMPLETE")
print("=" * 70)
