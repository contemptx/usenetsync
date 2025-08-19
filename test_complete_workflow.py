#!/usr/bin/env python3
"""Complete workflow test using REAL functionality"""

import asyncio
import json
import sys
import os
sys.path.insert(0, '/workspace/src')

from folder_management.folder_manager import FolderManager
from folder_management.folder_operations import FolderUploadManager, FolderPublisher

async def test_workflow():
    """Test the complete workflow with real functionality"""
    
    print("=" * 60)
    print("COMPLETE WORKFLOW TEST - USING REAL FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize components
    fm = FolderManager()
    uploader = FolderUploadManager(fm)
    publisher = FolderPublisher(fm)
    
    folder_id = "06220197-3000-4ccd-8149-34a49aab617c"
    
    # 1. Check folder status
    print("\n1. CHECKING FOLDER STATUS")
    folder = await fm._get_folder(folder_id)
    if folder:
        print(f"   Folder: {folder['display_name']}")
        print(f"   Path: {folder['folder_path']}")
        print(f"   Files: {folder['total_files']}")
        print(f"   Size: {folder['total_size']} bytes")
        print(f"   State: {folder['state']}")
    else:
        print("   ERROR: Folder not found!")
        return
    
    # 2. Check segments
    print("\n2. CHECKING SEGMENTS")
    segments = await uploader._get_folder_segments(folder_id)
    print(f"   Found {len(segments)} segments")
    
    # 3. Test Upload
    print("\n3. TESTING UPLOAD")
    try:
        uploader.total_segments = len(segments)
        
        # Test building subject and headers
        if segments:
            subject = uploader._build_subject(folder, segments[0])
            print(f"   Subject: {subject}")
        
        # Try actual upload
        print("\n   Attempting upload...")
        result = await uploader.upload_folder(folder_id)
        print(f"   Upload result: {json.dumps(result, indent=4)}")
        
    except Exception as e:
        print(f"   Upload failed: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_workflow())
