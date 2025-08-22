#!/usr/bin/env python3
"""
Create a real share ID that can be tested locally
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
import uuid

# Add backend to path
sys.path.insert(0, '/workspace/backend/src')

DB_PATH = "/workspace/backend/data/usenetsync.db"
TEST_DIR = Path("/workspace/test_share_folder")

def create_test_data():
    """Create test folder with files"""
    TEST_DIR.mkdir(exist_ok=True)
    
    print("📁 Creating test files...")
    
    # Create some test files
    files = [
        ("readme.txt", b"This is a test file for share demonstration\n" * 100),
        ("data.json", json.dumps({"test": "data", "items": list(range(100))}).encode()),
        ("binary.dat", os.urandom(10000))
    ]
    
    for name, content in files:
        filepath = TEST_DIR / name
        filepath.write_bytes(content)
        print(f"  ✅ Created {name} ({len(content):,} bytes)")
    
    return str(TEST_DIR)

def add_to_database(folder_path):
    """Add folder and files to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generate folder ID
    folder_id = str(uuid.uuid4())
    
    print(f"\n📂 Adding folder to database...")
    print(f"  Folder ID: {folder_id}")
    
    # Insert folder
    cursor.execute("""
        INSERT INTO folders (folder_id, path, name, status, file_count, total_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (folder_id, folder_path, Path(folder_path).name, 'indexed', 3, 15000, datetime.now().isoformat()))
    
    # Insert files
    file_ids = []
    for filepath in Path(folder_path).glob("*"):
        if filepath.is_file():
            file_id = str(uuid.uuid4())
            file_ids.append(file_id)
            
            with open(filepath, 'rb') as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
            
            cursor.execute("""
                INSERT INTO files (file_id, folder_id, path, name, size, hash, mime_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (file_id, folder_id, str(filepath), filepath.name, len(content), file_hash, 'application/octet-stream', datetime.now().isoformat()))
            
            print(f"  ✅ Added {filepath.name} (ID: {file_id[:8]}...)")
    
    # Create segments (simplified)
    segment_count = 0
    for file_id in file_ids:
        for i in range(2):  # 2 segments per file for demo
            segment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO segments (segment_id, file_id, segment_index, size, hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (segment_id, file_id, i, 1000, hashlib.md5(f"{file_id}-{i}".encode()).hexdigest(), datetime.now().isoformat()))
            segment_count += 1
    
    print(f"  ✅ Created {segment_count} segments")
    
    # Create share
    share_id = "TEST-" + hashlib.md5(folder_id.encode()).hexdigest()[:8].upper()
    owner_id = str(uuid.uuid4())  # Generate owner ID
    
    cursor.execute("""
        INSERT INTO shares (share_id, folder_id, owner_id, share_type, access_type, access_level, download_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (share_id, folder_id, owner_id, 'full', 'public', 'public', 0, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return folder_id, share_id

def verify_share(share_id):
    """Verify the share exists in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.share_id, s.access_level, f.path, f.file_count
        FROM shares s
        JOIN folders f ON s.folder_id = f.folder_id
        WHERE s.share_id = ?
    """, (share_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "share_id": result[0],
            "access": result[1],
            "folder": result[2],
            "files": result[3]
        }
    return None

def main():
    print("="*70)
    print("🔧 CREATING TEST SHARE ID")
    print("="*70)
    
    # Create test data
    folder_path = create_test_data()
    
    # Add to database
    folder_id, share_id = add_to_database(folder_path)
    
    # Verify
    share_info = verify_share(share_id)
    
    if share_info:
        print("\n" + "="*70)
        print("✅ SHARE CREATED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📋 SHARE ID: {share_id}")
        print(f"   Access: {share_info['access']}")
        print(f"   Folder: {share_info['folder']}")
        print(f"   Files: {share_info['files']}")
        print("\n🔗 You can test this share ID with:")
        print(f"   1. Go to http://localhost:1420/download")
        print(f"   2. Enter share ID: {share_id}")
        print(f"   3. Click Download")
        print("\n📡 Or test via API:")
        print(f"   curl -X POST http://localhost:8000/api/v1/download_share \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"share_id\": \"{share_id}\"}}'")
    else:
        print("\n❌ Failed to create share")
    
    # Don't cleanup - keep for testing
    print("\n💾 Test files kept at:", folder_path)

if __name__ == "__main__":
    main()