#!/usr/bin/env python3
"""
Complete Folder Workflow Test - Fixed Version
Tests: Add -> Index -> Segment -> Upload -> Publish -> Share
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
        
        if response.status_code not in [200, 201]:
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
            print(f"    Segments: {test_folder.get('segment_count')}")
        else:
            print(f"  ⚠ Folder not found in list")
    
    # 3. INDEX FOLDER (using correct parameters)
    print_section("3. INDEXING FOLDER")
    index_result = api_call("POST", "/index_folder", {
        "folderPath": TEST_FOLDER,  # Using folderPath instead of folder_id
        "path": TEST_FOLDER  # Also try with path
    })
    
    if index_result and index_result.get("success"):
        print(f"  ✓ Folder indexed successfully")
        print(f"    Files indexed: {index_result.get('files_indexed', 0)}")
        print(f"    Total size: {index_result.get('total_size', 0)} bytes")
    else:
        print(f"  ⚠ Index result: {index_result}")
    
    # 4. SEGMENT FOLDER (using correct parameter name)
    print_section("4. SEGMENTING FOLDER")
    segment_result = api_call("POST", "/process_folder", {
        "folderId": folder_id,  # Using camelCase
        "segmentSize": 700000  # 700KB segments
    })
    
    if segment_result and segment_result.get("success"):
        print(f"  ✓ Folder segmented successfully")
        print(f"    Segments created: {segment_result.get('segments_created', 0)}")
        print(f"    Total size: {segment_result.get('total_size', 0)} bytes")
    else:
        print(f"  ⚠ Segment result: {segment_result}")
    
    # Check folder stats after segmentation
    print_section("5. CHECKING SEGMENTS")
    folders = api_call("GET", "/folders")
    if folders:
        for folder in folders:
            if folder.get("folder_id") == folder_id:
                print(f"  ✓ Folder stats after segmentation:")
                print(f"    Segments: {folder.get('segment_count')}")
                break
    
    # 6. UPLOAD FOLDER (using correct parameter)
    print_section("6. UPLOADING TO USENET")
    upload_result = api_call("POST", "/upload_folder", {
        "folderId": folder_id  # Using camelCase
    })
    
    if upload_result:
        if upload_result.get("success"):
            print(f"  ✓ Upload completed successfully")
            print(f"    Articles uploaded: {upload_result.get('articles_uploaded', 0)}")
            print(f"    Message IDs: {upload_result.get('message_ids', [])[:3]}...")
        else:
            print(f"  ⚠ Upload result: {upload_result}")
    
    # 7. CREATE SHARE (using correct parameters)
    print_section("7. CREATING SHARE")
    share_result = api_call("POST", "/create_share", {
        "folderId": folder_id,  # Using camelCase
        "shareType": "public",
        "password": None
    })
    
    if share_result and share_result.get("success"):
        share_id = share_result.get("share_id")
        share_url = share_result.get("share_url")
        print(f"  ✓ Share created successfully")
        print(f"    Share ID: {share_id}")
        print(f"    Share URL: {share_url}")
        
        # 8. VERIFY SHARE
        print_section("8. VERIFYING SHARE")
        shares = api_call("GET", "/shares")
        
        if shares:
            for share in shares:
                if share.get("share_id") == share_id:
                    print(f"  ✓ Share found in list")
                    print(f"    Title: {share.get('title', 'Untitled')}")
                    print(f"    Type: {share.get('share_type', 'unknown')}")
                    print(f"    Created: {share.get('created_at', 'unknown')}")
                    break
    else:
        print(f"  ⚠ Share result: {share_result}")
        share_id = None
    
    # 9. LIST ALL SHARES
    print_section("9. ALL SHARES")
    shares = api_call("GET", "/shares")
    
    if shares:
        print(f"  ✓ Total shares in system: {len(shares)}")
        # Show recent shares
        recent = sorted(shares, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
        for share in recent:
            print(f"    - {share.get('title', 'Untitled')[:30]}: {share.get('share_id', '')[:8]}...")
    
    # 10. TEST STATS
    print_section("10. SYSTEM STATS")
    stats = api_call("GET", "/stats")
    
    if stats:
        print(f"  ✓ System statistics:")
        print(f"    Total folders: {stats.get('total_folders', 0)}")
        print(f"    Total files: {stats.get('total_files', 0)}")
        print(f"    Total segments: {stats.get('total_segments', 0)}")
        print(f"    Total shares: {stats.get('total_shares', 0)}")
        print(f"    Storage used: {stats.get('total_size', 0)} bytes")
    
    # 11. FINAL FOLDER CHECK
    print_section("11. FINAL FOLDER STATUS")
    folders = api_call("GET", "/folders")
    
    if folders:
        for folder in folders:
            if folder.get("folder_id") == folder_id:
                print(f"  ✓ Final folder details:")
                print(f"    Status: {folder.get('status', 'unknown')}")
                print(f"    Files: {folder.get('file_count', 0)}")
                print(f"    Segments: {folder.get('segment_count', 0)}")
                print(f"    Total size: {folder.get('total_size', 0)} bytes")
                print(f"    Last indexed: {folder.get('last_indexed', 'unknown')}")
                break
    
    print_section("WORKFLOW TEST COMPLETE")
    print("\nSummary:")
    print(f"  • Folder ID: {folder_id}")
    print(f"  • Share ID: {share_id if share_id else 'Not created'}")
    print(f"  • Test folder: {TEST_FOLDER}")
    
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