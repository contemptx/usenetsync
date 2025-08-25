#!/usr/bin/env python3
"""
Test the workflow using EXISTING functionality
"""

import json
import requests
import time
import os
from pathlib import Path

API_URL = "http://localhost:8000/api/v1"

def create_test_folder():
    """Create a test folder with files"""
    test_dir = Path("/tmp/test_usenet_workflow")
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    (test_dir / "test1.txt").write_text("Test content 1" * 100)
    (test_dir / "test2.txt").write_text("Test content 2" * 200)
    
    return str(test_dir)

def test_with_existing_system():
    print("\n" + "="*70)
    print("TESTING WITH EXISTING UNIFIED SYSTEM")
    print("="*70)
    
    # Step 1: Create and add folder
    test_path = create_test_folder()
    print(f"\n📁 Step 1: Add folder: {test_path}")
    
    response = requests.post(
        f"{API_URL}/add_folder",
        json={
            "path": test_path,
            "owner_id": "test_workflow_user"
        }
    )
    
    if response.ok:
        folder_result = response.json()
        folder_id = folder_result["folder_id"]
        print(f"✅ Folder added: {folder_id}")
    else:
        print(f"❌ Failed to add folder: {response.text}")
        return
    
    # Step 2: Index the folder
    print(f"\n📑 Step 2: Index folder")
    
    response = requests.post(
        f"{API_URL}/index_folder",
        json={"folder_id": folder_id}
    )
    
    if response.ok:
        print(f"✅ Folder indexed")
    else:
        print(f"❌ Failed to index: {response.text}")
        return
    
    # Step 3: Segment the folder
    print(f"\n✂️ Step 3: Segment folder")
    
    response = requests.post(
        f"{API_URL}/process_folder",
        json={"folderId": folder_id}
    )
    
    if response.ok:
        print(f"✅ Folder segmented")
    else:
        print(f"❌ Failed to segment: {response.text}")
        return
    
    # Step 4: Create share
    print(f"\n🔗 Step 4: Create share")
    
    response = requests.post(
        f"{API_URL}/create_share",
        json={
            "folder_id": folder_id,
            "owner_id": "test_workflow_user",
            "shareType": "public"
        }
    )
    
    if response.ok:
        share_result = response.json()
        share_id = share_result["share_id"]
        print(f"✅ Share created: {share_id}")
        print(f"   Access: {share_result['access_string']}")
    else:
        print(f"❌ Failed to create share: {response.text}")
        return
    
    # Step 5: Upload to Usenet using existing system
    print(f"\n📤 Step 5: Upload to Usenet (using existing UnifiedUploadSystem)")
    
    response = requests.post(
        f"{API_URL}/upload_folder",
        json={
            "folder_id": folder_id,
            "share_id": share_id
        }
    )
    
    if response.ok:
        upload_result = response.json()
        print(f"✅ Upload complete!")
        print(f"   Segments: {upload_result.get('segments_uploaded', 0)}")
        print(f"   Core Index: {upload_result.get('core_index_id', 'N/A')}")
        print(f"   Workflow: {upload_result.get('workflow', 'Unknown')}")
        print(f"   Time: {upload_result.get('upload_time_seconds', 0):.2f}s")
    else:
        print(f"❌ Failed to upload: {response.text}")
        return
    
    # Step 6: Download from Usenet
    print(f"\n📥 Step 6: Download (end user with only share ID)")
    
    response = requests.post(
        f"{API_URL}/download_share",
        json={
            "share_id": share_id,
            "outputPath": "/tmp/downloads"
        }
    )
    
    if response.ok:
        download_result = response.json()
        print(f"✅ Download complete!")
        print(f"   Files: {download_result.get('files_downloaded', 0)}")
        print(f"   Time: {download_result.get('download_time_seconds', 0):.2f}s")
        
        if download_result.get('end_user_note'):
            print(f"\n📌 {download_result['end_user_note']}")
    else:
        print(f"❌ Failed to download: {response.text}")
    
    print("\n" + "="*70)
    print("✅ EXISTING SYSTEM WORKFLOW COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_with_existing_system()