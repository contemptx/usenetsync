#!/usr/bin/env python3
"""
Test REAL Usenet upload with Newshosting
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_FOLDER = "/workspace/test_workflow_folder"

def test_real_upload():
    print("="*70)
    print(" TESTING REAL USENET UPLOAD TO NEWSHOSTING")
    print("="*70)
    
    # 1. Add folder
    print("\n1. Adding test folder...")
    r = requests.post(f"{BASE_URL}/add_folder", json={
        "path": TEST_FOLDER,
        "name": "Real Upload Test"
    })
    
    if r.status_code != 200:
        print(f"   ✗ Failed to add folder: {r.status_code}")
        return
    
    result = r.json()
    folder_id = result['folder_id']
    print(f"   ✓ Folder added: {folder_id}")
    print(f"   Files indexed: {result.get('files_indexed', 0)}")
    
    # 2. Segment the folder
    print("\n2. Segmenting files...")
    r = requests.post(f"{BASE_URL}/process_folder", json={
        "folderId": folder_id
    })
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✓ Segmentation complete")
        print(f"   Segments created: {result.get('segments_created', 0)}")
    else:
        print(f"   ✗ Segmentation failed: {r.status_code}")
    
    # 3. Upload to Usenet
    print("\n3. Uploading to Newshosting...")
    print("   Server: news.newshosting.com")
    print("   User: contemptx")
    print("   Newsgroup: alt.binaries.test")
    
    r = requests.post(f"{BASE_URL}/upload_folder", json={
        "folderId": folder_id
    })
    
    if r.status_code == 200:
        result = r.json()
        if result.get('success'):
            print(f"   ✓ UPLOAD SUCCESSFUL!")
            print(f"   Articles uploaded: {result.get('articles_uploaded', 0)}")
            print(f"   Queue ID: {result.get('queue_id', 'N/A')}")
            
            # Show message IDs
            message_ids = result.get('message_ids', [])
            if message_ids:
                print(f"\n   Message IDs posted to Usenet:")
                for mid in message_ids[:5]:  # Show first 5
                    print(f"     - {mid}")
        else:
            print(f"   ⚠ Upload completed but no articles posted")
    else:
        print(f"   ✗ Upload failed: {r.status_code}")
        print(f"   Response: {r.text[:200]}")
    
    # 4. Create a share
    print("\n4. Creating public share...")
    r = requests.post(f"{BASE_URL}/create_share", json={
        "folderId": folder_id,
        "shareType": "public"
    })
    
    if r.status_code == 200:
        result = r.json()
        if result.get('success'):
            print(f"   ✓ Share created")
            print(f"   Share ID: {result.get('share_id', 'N/A')}")
            print(f"   Share URL: {result.get('share_url', 'N/A')}")
    else:
        print(f"   ✗ Share creation failed: {r.status_code}")
    
    # 5. Check system stats
    print("\n5. System statistics...")
    r = requests.get(f"{BASE_URL}/stats")
    if r.status_code == 200:
        stats = r.json()
        print(f"   Total folders: {stats.get('total_folders', 0)}")
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Total segments: {stats.get('total_segments', 0)}")
        print(f"   Total shares: {stats.get('total_shares', 0)}")
    
    print("\n" + "="*70)
    print(" TEST COMPLETE - CHECK alt.binaries.test ON NEWSHOSTING")
    print("="*70)

if __name__ == "__main__":
    test_real_upload()