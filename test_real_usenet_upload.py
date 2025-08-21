#!/usr/bin/env python3
"""
Test real Usenet upload with actual credentials
Server: news.newshosting.com
User: contemptx
Password: Kia211101#
"""

import requests
import json
import time
import os

def test_real_usenet_upload():
    print("="*80)
    print(" TESTING REAL USENET UPLOAD")
    print(" Server: news.newshosting.com:563 (SSL)")
    print(" User: contemptx")
    print("="*80)
    
    # First, get list of folders
    print("\n1. Getting folder list...")
    response = requests.get("http://localhost:8000/api/v1/folders")
    if response.ok:
        folders = response.json()
        print(f"   Found {len(folders)} folders")
        
        if len(folders) > 0:
            # Use the first folder
            folder = folders[0]
            folder_id = folder.get('folder_id')
            print(f"   Using folder: {folder.get('name', 'Unknown')}")
            print(f"   Folder ID: {folder_id}")
            print(f"   State: {folder.get('state', 'unknown')}")
            
            # Check if folder needs indexing
            if folder.get('state') == 'added':
                print("\n2. Indexing folder...")
                index_response = requests.post(
                    "http://localhost:8000/api/v1/index_folder",
                    json={"folderId": folder_id}
                )
                if index_response.ok:
                    result = index_response.json()
                    print(f"   ✓ Indexed {result.get('files_indexed', 0)} files")
                else:
                    print(f"   ✗ Index failed: {index_response.text}")
                time.sleep(2)
            
            # Check if folder needs segmentation
            if folder.get('state') in ['added', 'indexed']:
                print("\n3. Creating segments...")
                segment_response = requests.post(
                    "http://localhost:8000/api/v1/process_folder",
                    json={"folderId": folder_id}
                )
                if segment_response.ok:
                    result = segment_response.json()
                    print(f"   ✓ Created {result.get('segments_created', 0)} segments")
                else:
                    print(f"   ✗ Segmentation failed: {segment_response.text}")
                time.sleep(2)
            
            # Now upload to Usenet
            print("\n4. UPLOADING TO USENET...")
            print("   This will post real data to news.newshosting.com")
            print("   Using NNTP over SSL on port 563")
            
            upload_response = requests.post(
                "http://localhost:8000/api/v1/upload_folder",
                json={"folderId": folder_id}
            )
            
            if upload_response.ok:
                result = upload_response.json()
                print("   ✓ Upload initiated successfully!")
                print(f"   Response: {json.dumps(result, indent=2)}")
                
                # Wait for upload to complete
                print("\n   Waiting for upload to complete...")
                time.sleep(10)
                
                # Check upload status
                print("\n5. Checking upload status...")
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/folders/{folder_id}/status"
                )
                if status_response.ok:
                    status = status_response.json()
                    print(f"   Folder state: {status.get('state', 'unknown')}")
                    print(f"   Uploaded: {status.get('uploaded', False)}")
            else:
                print(f"   ✗ Upload failed: {upload_response.status_code}")
                print(f"   Error: {upload_response.text}")
            
            # Create a share
            print("\n6. Creating share...")
            share_response = requests.post(
                "http://localhost:8000/api/v1/publish_folder",
                json={
                    "folderId": folder_id,
                    "shareType": "public"
                }
            )
            
            if share_response.ok:
                share = share_response.json()
                print(f"   ✓ Share created!")
                print(f"   Share ID: {share.get('share_id', 'unknown')}")
                print(f"   Access: {share.get('access_string', 'N/A')}")
            else:
                print(f"   ✗ Share creation failed: {share_response.text}")
                
    else:
        print(f"   Failed to get folders: {response.status_code}")
    
    print("\n" + "="*80)
    print(" TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_real_usenet_upload()