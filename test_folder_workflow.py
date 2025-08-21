#!/usr/bin/env python3
"""Test the complete folder workflow through the API"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_folder_workflow():
    """Test complete folder workflow"""
    
    print("=" * 60)
    print("TESTING FOLDER MANAGEMENT WORKFLOW")
    print("=" * 60)
    
    # 1. Add a folder
    print("\n1. Adding folder...")
    response = requests.post(f"{BASE_URL}/add_folder", json={"path": "/workspace/test_folder"})
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {json.dumps(data, indent=2)}")
        folder_id = data.get("folder_id")
        print(f"Folder ID: {folder_id}")
    else:
        print(f"Error: {response.text}")
        return False
    
    # 2. Get folders list
    print("\n2. Getting folders list...")
    response = requests.get(f"{BASE_URL}/folders")
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        folders = response.json()
        print(f"Folders count: {len(folders)}")
        for folder in folders[:3]:  # Show first 3
            print(f"  - {folder.get('path', 'N/A')} (ID: {folder.get('folder_id', 'N/A')})")
    
    # 3. Index the folder
    print("\n3. Indexing folder...")
    response = requests.post(f"{BASE_URL}/index_folder", json={"folderId": folder_id})
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # 4. Process segments
    print("\n4. Processing segments...")
    response = requests.post(f"{BASE_URL}/process_folder", json={"folderId": folder_id})
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # 5. Create a share
    print("\n5. Creating share...")
    response = requests.post(f"{BASE_URL}/create_share", json={
        "folderId": folder_id,
        "shareType": "public"
    })
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {json.dumps(data, indent=2)}")
        share_id = data.get("share_id")
    else:
        print(f"Error: {response.text}")
    
    # 6. Get shares list
    print("\n6. Getting shares list...")
    response = requests.get(f"{BASE_URL}/shares")
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        shares = response.json()
        print(f"Shares count: {len(shares)}")
        for share in shares[:3]:  # Show first 3
            print(f"  - Share {share.get('share_id', 'N/A')} for folder {share.get('folder_id', 'N/A')}")
    
    # 7. Upload folder (queue it)
    print("\n7. Queueing folder for upload...")
    response = requests.post(f"{BASE_URL}/upload_folder", json={"folderId": folder_id})
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # 8. Check upload queue
    print("\n8. Checking upload queue...")
    response = requests.get(f"{BASE_URL}/events/transfers")
    print(f"Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        events = data.get("events", [])
        print(f"Transfer events: {len(events)}")
        for event in events[:3]:
            print(f"  - {event.get('type', 'N/A')}: {event.get('state', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("WORKFLOW TEST COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_folder_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)