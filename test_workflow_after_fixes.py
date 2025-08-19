#!/usr/bin/env python3
"""
Test workflow after state check fixes
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

def get_test_folder():
    """Get or create a test folder with segments"""
    conn = sqlite3.connect('/home/ubuntu/.usenetsync/data.db')
    cursor = conn.cursor()
    
    # Find a folder with segments
    cursor.execute("""
        SELECT DISTINCT fo.folder_unique_id, fo.display_name, COUNT(s.id) as segment_count
        FROM folders fo
        JOIN files f ON f.folder_id = fo.id
        JOIN segments s ON s.file_id = f.id
        GROUP BY fo.folder_unique_id
        HAVING segment_count > 0
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], result[1], result[2]
    return None, None, 0

print("=" * 70)
print("TESTING WORKFLOW AFTER STATE CHECK FIXES")
print("=" * 70)

# Get a folder with segments
folder_id, folder_name, segment_count = get_test_folder()

if not folder_id:
    print("\n❌ No folder with segments found. Creating one...")
    
    # Create test folder
    test_dir = Path('/tmp/fix_test')
    test_dir.mkdir(exist_ok=True)
    (test_dir / 'test.txt').write_text('Test content\n' * 100)
    
    # Add, index, and segment
    result = run_cmd(f'add-folder --path "{test_dir}" --name "Fix Test"')
    if result['success']:
        folder_id = result['data']['folder_id']
        run_cmd(f'index-managed-folder --folder-id {folder_id}')
        run_cmd(f'segment-folder --folder-id {folder_id}')
        folder_name = "Fix Test"
        segment_count = 2

print(f"\n✓ Using folder: {folder_name}")
print(f"  ID: {folder_id}")
print(f"  Segments: {segment_count}")

# Test 1: Upload (should pass state check now)
print("\n" + "="*50)
print("1. TESTING UPLOAD (State Check)")
print("-"*50)

result = run_cmd(f'upload-folder --folder-id {folder_id}')

if 'No segments found' in str(result.get('stderr', '')) or 'No segments found' in str(result.get('data', '')):
    print("❌ State check still failing - segments not found")
elif 'news.newshosting.com' in str(result.get('stderr', '')):
    print("✅ State check PASSED! (Failed on Usenet connection - expected)")
elif 'ProductionNNTPClient' in str(result.get('stderr', '')):
    print("✅ State check PASSED! (Failed on NNTP client - expected)")
elif result['success']:
    print("✅ Upload succeeded (unexpected - check if really connected)")
    print(f"   Result: {result['data']}")
else:
    error = str(result.get('stderr', ''))[:200]
    if 'must be segmented' in error:
        print("❌ State check NOT fixed - still checking for 'segmented' state")
    else:
        print(f"⚠️ Different error: {error}")

# Test 2: Publish (should pass state check now)
print("\n" + "="*50)
print("2. TESTING PUBLISH (State Check)")
print("-"*50)

result = run_cmd(f'publish-folder --folder-id {folder_id}')

if 'No segments found' in str(result.get('stderr', '')) or 'No segments found' in str(result.get('data', '')):
    print("❌ State check still failing - segments not found")
elif 'must be uploaded' in str(result.get('stderr', '')) or 'must be uploaded' in str(result.get('data', '')):
    print("❌ State check NOT fixed - still checking for 'uploaded' state")
elif result['success']:
    print("✅ Publish succeeded!")
    if result['data']:
        print(f"   Share ID: {result['data'].get('share_id', 'Unknown')}")
        print(f"   Access: {result['data'].get('access_type', 'Unknown')}")
else:
    error = str(result.get('stderr', ''))[:200] or str(result.get('data', ''))[:200]
    if 'SimplifiedBinaryIndex' in error:
        print("✅ State check PASSED! (Failed on binary index - different issue)")
    else:
        print(f"⚠️ Different error: {error}")

# Test 3: Check which tables got populated
print("\n" + "="*50)
print("3. DATABASE TABLE USAGE")
print("-"*50)

conn = sqlite3.connect('/home/ubuntu/.usenetsync/data.db')
cursor = conn.cursor()

tables_to_check = [
    'uploads', 'upload_sessions', 'upload_queue', 'segment_upload_queue',
    'shares', 'publications', 'published_indexes', 'authorized_users'
]

for table in tables_to_check:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"  {table}: {count} rows ✓")

conn.close()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
