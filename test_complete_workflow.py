#!/usr/bin/env python3
"""
Complete Folder Workflow Test
Tests: Add -> Index -> Segment -> Upload -> Publish -> Share -> Download
"""

import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
TEST_FOLDER = "/workspace/test_workflow_folder"

def print_section(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def api_call(method, endpoint, data=None, params=None):
    """Make an API call and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"  → {method} {endpoint}: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ✗ Error: {response.text[:200]}")
            return None
            
        result = response.json() if response.text else {}
        return result
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        return None

def test_workflow():
    """Test the complete folder workflow"""
    
    print_section("COMPLETE FOLDER WORKFLOW TEST")
    
    # 1. ADD FOLDER
    print_section("1. ADDING FOLDER")
    add_result = api_call("POST", "/add_folder", {
        "path": TEST_FOLDER,
        "name": "Test Workflow Folder"
    })
    
    if not add_result or not add_result.get("success"):
        print("  ✗ Failed to add folder")
        return False
    
    folder_id = add_result.get("folder_id")
    print(f"  ✓ Folder added successfully")
    print(f"    Folder ID: {folder_id}")
    print(f"    Files indexed: {add_result.get('files_indexed', 0)}")
    
    # 2. GET FOLDER DETAILS
    print_section("2. GETTING FOLDER DETAILS")
    folders = api_call("GET", "/folders")
    
    if folders:
        test_folder = None
        for folder in folders:
            if folder.get("folder_id") == folder_id:
                test_folder = folder
                break
        
        if test_folder:
            print(f"  ✓ Folder found in list")
            print(f"    Path: {test_folder.get('path')}")
            print(f"    Files: {test_folder.get('file_count')}")
            print(f"    Size: {test_folder.get('total_size')} bytes")
        else:
            print(f"  ⚠ Folder not found in list")
    
    # 3. INDEX FOLDER (Re-index to ensure all files are indexed)
    print_section("3. INDEXING FOLDER")
    index_result = api_call("POST", "/index_folder", params={"folder_id": folder_id})
    
    if index_result and index_result.get("success"):
        print(f"  ✓ Folder indexed successfully")
        print(f"    Files indexed: {index_result.get('files_indexed', 0)}")
        print(f"    Total size: {index_result.get('total_size', 0)} bytes")
    else:
        print(f"  ✗ Failed to index folder")
    
    # 4. GET FILES IN FOLDER
    print_section("4. LISTING FILES")
    files_result = api_call("GET", f"/folders/{folder_id}/files")
    
    if files_result:
        files = files_result if isinstance(files_result, list) else files_result.get("files", [])
        print(f"  ✓ Found {len(files)} files:")
        for file in files[:5]:  # Show first 5 files
            print(f"    - {file.get('name', 'Unknown')}: {file.get('size', 0)} bytes")
    else:
        print("  ⚠ Could not list files")
    
    # 5. SEGMENT FOLDER
    print_section("5. SEGMENTING FOLDER")
    segment_result = api_call("POST", "/process_folder", {
        "folder_id": folder_id,
        "segment_size": 700000  # 700KB segments
    })
    
    if segment_result and segment_result.get("success"):
        print(f"  ✓ Folder segmented successfully")
        print(f"    Segments created: {segment_result.get('segments_created', 0)}")
        print(f"    Total size: {segment_result.get('total_size', 0)} bytes")
    else:
        print(f"  ⚠ Segmentation may have failed or no segments needed")
    
    # 6. UPLOAD FOLDER
    print_section("6. UPLOADING TO USENET")
    upload_result = api_call("POST", "/upload_folder", {
        "folder_id": folder_id
    })
    
    if upload_result:
        if upload_result.get("success"):
            print(f"  ✓ Upload initiated successfully")
            print(f"    Articles uploaded: {upload_result.get('articles_uploaded', 0)}")
        elif "already uploaded" in str(upload_result).lower():
            print(f"  ℹ Folder already uploaded")
        else:
            print(f"  ⚠ Upload may have issues: {upload_result}")
    else:
        print(f"  ✗ Upload failed")
    
    # 7. CREATE SHARE
    print_section("7. CREATING SHARE")
    share_result = api_call("POST", "/create_share", {
        "folder_id": folder_id,
        "title": "Test Workflow Share",
        "description": "Testing complete workflow",
        "expires_in_days": 7
    })
    
    if share_result and share_result.get("success"):
        share_id = share_result.get("share_id")
        share_url = share_result.get("share_url")
        print(f"  ✓ Share created successfully")
        print(f"    Share ID: {share_id}")
        print(f"    Share URL: {share_url}")
        
        # 8. GET SHARE DETAILS
        print_section("8. VERIFYING SHARE")
        share_details = api_call("GET", f"/shares/{share_id}")
        
        if share_details:
            print(f"  ✓ Share verified")
            print(f"    Title: {share_details.get('title')}")
            print(f"    Files: {share_details.get('file_count', 0)}")
            print(f"    Size: {share_details.get('total_size', 0)} bytes")
    else:
        print(f"  ✗ Failed to create share")
        share_id = None
    
    # 9. LIST ALL SHARES
    print_section("9. LISTING ALL SHARES")
    shares = api_call("GET", "/shares")
    
    if shares:
        print(f"  ✓ Found {len(shares)} total shares")
        for share in shares[:3]:  # Show first 3
            print(f"    - {share.get('title', 'Untitled')}: {share.get('share_id', '')[:8]}...")
    
    # 10. TEST DOWNLOAD (if share was created)
    if share_id:
        print_section("10. TESTING DOWNLOAD")
        download_result = api_call("POST", f"/shares/{share_id}/download", {
            "output_path": "/workspace/test_download"
        })
        
        if download_result:
            if download_result.get("success"):
                print(f"  ✓ Download initiated")
                print(f"    Output path: {download_result.get('output_path')}")
            else:
                print(f"  ⚠ Download status: {download_result}")
        else:
            print(f"  ✗ Download failed")
    
    # 11. CHECK FOLDER STATS
    print_section("11. FINAL FOLDER STATS")
    folders = api_call("GET", "/folders")
    
    if folders:
        for folder in folders:
            if folder.get("folder_id") == folder_id:
                print(f"  ✓ Final folder status:")
                print(f"    Files: {folder.get('file_count', 0)}")
                print(f"    Segments: {folder.get('segment_count', 0)}")
                print(f"    Total size: {folder.get('total_size', 0)} bytes")
                print(f"    Status: {folder.get('status', 'unknown')}")
                break
    
    # 12. CLEANUP TEST
    print_section("12. TESTING FOLDER DELETION")
    delete_result = api_call("DELETE", f"/folders/{folder_id}")
    
    if delete_result and delete_result.get("success"):
        print(f"  ✓ Folder deleted successfully")
    else:
        print(f"  ⚠ Could not delete folder (may not be implemented)")
    
    print_section("TEST COMPLETE")
    return True

if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            print("✓ Backend is running")
        else:
            print("✗ Backend returned error:", response.status_code)
    except:
        print("✗ Backend is not running! Start it with: python run_backend.py")
        exit(1)
    
    # Run the workflow test
    test_workflow()