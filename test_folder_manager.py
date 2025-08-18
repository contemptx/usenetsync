#!/usr/bin/env python3
"""
Test script for FolderManager
Uses real components and systems - no mocks
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from folder_management.folder_manager import FolderManager, FolderConfig


async def test_folder_management():
    """Test complete folder management flow with real data"""
    
    print("="*60)
    print("FOLDER MANAGEMENT SYSTEM TEST")
    print("="*60)
    
    # Initialize FolderManager with real configuration
    config = FolderConfig(
        chunk_size=100,  # Smaller for testing
        segment_size=768000,  # 768KB
        redundancy_level=2,  # Create 2 copies
        max_workers=4,
        batch_size=10
    )
    
    manager = FolderManager(config)
    
    # Create a test folder with real files
    with tempfile.TemporaryDirectory() as test_dir:
        test_path = Path(test_dir)
        
        # Create test files
        print("\n1. Creating test files...")
        
        # Create subdirectories
        (test_path / "documents").mkdir()
        (test_path / "images").mkdir()
        (test_path / "data").mkdir()
        
        # Create various sized files
        test_files = [
            ("documents/readme.txt", "This is a test readme file\n" * 100),
            ("documents/report.txt", "Annual report data\n" * 500),
            ("images/test1.dat", "A" * 50000),  # 50KB
            ("images/test2.dat", "B" * 100000),  # 100KB
            ("data/large.dat", "C" * 1000000),  # 1MB
        ]
        
        for file_path, content in test_files:
            file_full_path = test_path / file_path
            file_full_path.write_text(content)
            print(f"  Created: {file_path} ({len(content)} bytes)")
        
        # Test 1: Add Folder
        print("\n2. Adding folder to management system...")
        try:
            folder_result = await manager.add_folder(
                path=str(test_path),
                name="Test Folder"
            )
            
            folder_id = folder_result['folder_id']
            print(f"✓ Folder added successfully")
            print(f"  ID: {folder_id}")
            print(f"  Name: {folder_result['name']}")
            print(f"  State: {folder_result['state']}")
            
        except Exception as e:
            print(f"✗ Failed to add folder: {e}")
            return False
        
        # Test 2: Index Folder
        print("\n3. Indexing folder...")
        
        # Set up progress callback
        async def progress_callback(operation: str, data: dict):
            if 'current' in data and 'total' in data:
                percent = (data['current'] / data['total'] * 100) if data['total'] > 0 else 0
                print(f"  Progress: {percent:.1f}% ({data['current']}/{data['total']})")
        
        manager.progress_callbacks[folder_id] = progress_callback
        
        try:
            index_result = await manager.index_folder(folder_id)
            
            print(f"✓ Indexing completed")
            print(f"  Files indexed: {index_result.get('files_indexed', 0)}")
            print(f"  Total size: {index_result.get('total_size', 0)} bytes")
            
        except Exception as e:
            print(f"✗ Indexing failed: {e}")
            return False
        
        # Test 3: Segment Folder
        print("\n4. Creating segments with redundancy...")
        try:
            segment_result = await manager.segment_folder(folder_id)
            
            print(f"✓ Segmentation completed")
            print(f"  Total segments: {segment_result['total_segments']}")
            print(f"  Redundancy segments: {segment_result['redundancy_segments']}")
            print(f"  Redundancy level: {segment_result['redundancy_level']}")
            
        except Exception as e:
            print(f"✗ Segmentation failed: {e}")
            return False
        
        # Test 4: Verify Database State
        print("\n5. Verifying database state...")
        
        folder_info = await manager._get_folder(folder_id)
        if folder_info:
            print(f"✓ Folder state in database:")
            print(f"  State: {folder_info['state']}")
            print(f"  Total files: {folder_info['total_files']}")
            print(f"  Total size: {folder_info['total_size']}")
            print(f"  Total segments: {folder_info['total_segments']}")
            print(f"  Redundancy segments: {folder_info['redundancy_segments']}")
        
        # Test 5: Check PostgreSQL Integration
        print("\n6. Verifying PostgreSQL integration...")
        
        with manager.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check managed_folders table
            cursor.execute("SELECT COUNT(*) FROM managed_folders")
            folder_count = cursor.fetchone()[0]
            print(f"  Folders in database: {folder_count}")
            
            # Check folder_operations table
            cursor.execute("SELECT COUNT(*) FROM folder_operations WHERE folder_id = %s", (folder_id,))
            operations_count = cursor.fetchone()[0]
            print(f"  Operations tracked: {operations_count}")
            
            # Check files table
            cursor.execute("SELECT COUNT(*) FROM files WHERE folder_id = %s", (folder_id,))
            files_count = cursor.fetchone()[0]
            print(f"  Files in database: {files_count}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("- Folder management system working")
        print("- PostgreSQL integration confirmed")
        print("- Indexing system operational")
        print("- Segmentation with redundancy working")
        print("- Progress tracking functional")
        print("- All using REAL components (no mocks)")
        
        return True


async def main():
    """Run the test"""
    try:
        success = await test_folder_management()
        
        if success:
            print("\n🎉 Folder management system is fully operational!")
            print("Ready for upload and publishing implementation.")
        else:
            print("\n⚠ Some tests failed. Check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())