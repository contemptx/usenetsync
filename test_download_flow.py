#!/usr/bin/env python3
"""
Test complete download flow with real Usenet
"""

import os
import sys
import time
import json
import requests
import tempfile
import shutil
from pathlib import Path

API_URL = "http://localhost:8000/api/v1"

def test_download_flow():
    """Test complete upload and download flow"""
    
    print("=" * 70)
    print("TESTING COMPLETE DOWNLOAD FLOW WITH REAL USENET")
    print("=" * 70)
    
    # Create test folder with some files
    test_dir = Path("/tmp/test_download_flow")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create test files
    (test_dir / "file1.txt").write_text("This is test file 1 content" * 100)
    (test_dir / "file2.txt").write_text("This is test file 2 content" * 200)
    
    print(f"\n📁 Step 1: Add folder: {test_dir}")
    response = requests.post(f"{API_URL}/add_folder", json={
        "path": str(test_dir),
        "owner_id": "test_user"
    })
    folder_data = response.json()
    folder_id = folder_data["folder_id"]
    print(f"✅ Folder added: {folder_id}")
    
    print(f"\n📑 Step 2: Index folder")
    response = requests.post(f"{API_URL}/index_folder", json={
        "folder_id": folder_id
    })
    print(f"✅ Folder indexed")
    time.sleep(1)
    
    print(f"\n✂️ Step 3: Segment folder")
    response = requests.post(f"{API_URL}/process_folder", json={
        "folder_id": folder_id
    })
    segments_data = response.json()
    print(f"✅ Created {segments_data.get('segments_created', 0)} segments")
    
    print(f"\n🔗 Step 4: Create share")
    response = requests.post(f"{API_URL}/create_share", json={
        "folder_id": folder_id,
        "owner_id": "test_user",
        "access_level": "public",
        "expiry_days": 30
    })
    share_data = response.json()
    share_id = share_data["share_id"]
    access_string = share_data["access_string"]
    print(f"✅ Share created: {share_id}")
    print(f"   Access: {access_string}")
    
    print(f"\n📤 Step 5: Upload to Usenet")
    response = requests.post(f"{API_URL}/upload_folder", json={
        "folder_id": folder_id,
        "share_id": share_id
    })
    upload_data = response.json()
    if upload_data.get("success"):
        print(f"✅ Upload complete!")
        print(f"   Segments uploaded: {upload_data.get('segments_uploaded', 0)}")
        print(f"   Time: {upload_data.get('upload_time_seconds', 0):.2f}s")
    else:
        print(f"❌ Upload failed: {upload_data}")
        return False
    
    # Wait for upload to complete
    time.sleep(2)
    
    print(f"\n📥 Step 6: Download from Usenet (as end user)")
    download_dir = Path("/tmp/downloaded_files")
    if download_dir.exists():
        shutil.rmtree(download_dir)
    download_dir.mkdir()
    
    response = requests.post(f"{API_URL}/download_share", json={
        "share_id": share_id,
        "output_path": str(download_dir)
    })
    download_data = response.json()
    
    if download_data.get("success"):
        print(f"✅ Download complete!")
        print(f"   Files downloaded: {download_data.get('files_downloaded', 0)}")
        print(f"   Time: {download_data.get('download_time_seconds', 0):.2f}s")
        
        # Check downloaded files
        downloaded_files = list(download_dir.rglob("*"))
        if downloaded_files:
            print(f"\n📂 Downloaded files:")
            for f in downloaded_files:
                if f.is_file():
                    print(f"   - {f.name} ({f.stat().st_size} bytes)")
        else:
            print(f"⚠️ No files found in download directory")
    else:
        print(f"❌ Download failed:")
        print(f"   Errors: {download_data.get('errors', [])}")
        return False
    
    # Check the database for message IDs
    import sqlite3
    conn = sqlite3.connect('data/usenetsync.db')
    cursor = conn.cursor()
    
    # Check packed segments
    cursor.execute("""
        SELECT COUNT(*) FROM packed_segments 
        WHERE message_id IS NOT NULL AND message_id NOT LIKE '%example.com%'
    """)
    real_packed = cursor.fetchone()[0]
    
    # Check regular segments
    cursor.execute("""
        SELECT COUNT(*) FROM segments 
        WHERE message_id IS NOT NULL AND message_id NOT LIKE '%example.com%'
    """)
    real_segments = cursor.fetchone()[0]
    
    print(f"\n📊 Database check:")
    print(f"   Packed segments with real message IDs: {real_packed}")
    print(f"   Regular segments with real message IDs: {real_segments}")
    
    # Get a sample real message ID
    cursor.execute("""
        SELECT message_id FROM packed_segments 
        WHERE message_id IS NOT NULL AND message_id NOT LIKE '%example.com%'
        LIMIT 1
    """)
    sample = cursor.fetchone()
    if sample:
        print(f"   Sample real message ID: {sample[0]}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    if download_data.get("success"):
        print("✅ DOWNLOAD FLOW TEST COMPLETE")
    else:
        print("❌ DOWNLOAD FLOW TEST FAILED")
    print("=" * 70)
    
    return download_data.get("success", False)

if __name__ == "__main__":
    # Wait for backend to be ready
    time.sleep(3)
    
    try:
        success = test_download_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)