#!/usr/bin/env python3
"""
Test the COMPLETE Usenet workflow with enhanced endpoints
"""

import json
import requests
import time

API_URL = "http://localhost:8000/api/v1"

def test_complete_workflow():
    print("\n" + "="*70)
    print("TESTING COMPLETE USENET WORKFLOW")
    print("="*70)
    
    folder_id = "53718dea-ebae-4750-adbb-44681b97a936"
    
    # Step 1: Create share
    print("\n📝 Step 1: Create Share")
    response = requests.post(
        f"{API_URL}/create_share",
        json={
            "folder_id": folder_id,
            "owner_id": "test_user_54",
            "shareType": "public"
        }
    )
    
    if response.ok:
        share_result = response.json()
        share_id = share_result["share_id"]
        print(f"✅ Share created: {share_id}")
        print(f"   Access string: {share_result['access_string']}")
    else:
        print(f"❌ Failed to create share: {response.text}")
        return
    
    # Step 2: Upload to Usenet
    print("\n📤 Step 2: Upload to Usenet")
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
        print(f"   Segments uploaded: {upload_result.get('segments_uploaded', 0)}")
        print(f"   Core index message ID: {upload_result.get('core_index_message_id', 'N/A')}")
        print(f"   Upload time: {upload_result.get('upload_time_seconds', 0):.2f}s")
        print(f"   Status: {upload_result.get('status')}")
        
        if upload_result.get('errors'):
            print(f"   ⚠️  Errors: {upload_result['errors']}")
    else:
        print(f"❌ Failed to upload: {response.text}")
        return
    
    # Step 3: Download from Usenet (as end user)
    print("\n📥 Step 3: Download from Usenet (END USER - NO DATABASE)")
    print(f"   End user has ONLY: {share_id}")
    
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
        print(f"   Files downloaded: {download_result.get('files_downloaded', 0)}")
        print(f"   Download time: {download_result.get('download_time_seconds', 0):.2f}s")
        print(f"   Status: {download_result.get('status')}")
        
        if download_result.get('end_user_note'):
            print(f"\n📌 {download_result['end_user_note']}")
        
        if download_result.get('errors'):
            print(f"   ⚠️  Errors: {download_result['errors']}")
    else:
        print(f"❌ Failed to download: {response.text}")
    
    print("\n" + "="*70)
    print("WORKFLOW TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    # Wait for backend to start
    time.sleep(3)
    test_complete_workflow()