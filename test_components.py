#!/usr/bin/env python3
"""
Test that all major components are complete and can be instantiated
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_component_completeness():
    """Test that all components have their essential methods"""
    print("=" * 60)
    print("COMPONENT COMPLETENESS TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Test Upload System
    print("Testing EnhancedUploadSystem...")
    try:
        from src.upload.enhanced_upload_system import EnhancedUploadSystem
        
        # Check essential methods
        essential_methods = [
            'upload_segments',
            'get_session_progress',
            'cancel_session',
            'pause_uploads',
            'resume_uploads'
        ]
        
        for method in essential_methods:
            if not hasattr(EnhancedUploadSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("EnhancedUploadSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("EnhancedUploadSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("EnhancedUploadSystem", False))
    
    # Test Download System
    print("\nTesting EnhancedDownloadSystem...")
    try:
        from src.download.enhanced_download_system import EnhancedDownloadSystem
        
        essential_methods = [
            'download_from_access_string',
            'pause_session',
            'resume_session',
            'cancel_session',
            'get_session_status'
        ]
        
        for method in essential_methods:
            if not hasattr(EnhancedDownloadSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("EnhancedDownloadSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("EnhancedDownloadSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("EnhancedDownloadSystem", False))
    
    # Test Publishing System
    print("\nTesting PublishingSystem...")
    try:
        from src.upload.publishing_system import PublishingSystem
        
        essential_methods = [
            'publish_folder',
            'get_share_info',
            'list_shares',
            'revoke_share',
            'get_job_status'
        ]
        
        for method in essential_methods:
            if not hasattr(PublishingSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("PublishingSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("PublishingSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("PublishingSystem", False))
    
    # Test Segment Packing
    print("\nTesting SegmentPackingSystem...")
    try:
        from src.upload.segment_packing_system import SegmentPackingSystem
        
        essential_methods = [
            'pack_file_segments',
            'unpack_segment',
            'verify_packed_segment'
        ]
        
        for method in essential_methods:
            if not hasattr(SegmentPackingSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("SegmentPackingSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("SegmentPackingSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("SegmentPackingSystem", False))
    
    # Test Segment Retrieval
    print("\nTesting SegmentRetrievalSystem...")
    try:
        from src.download.segment_retrieval_system import SegmentRetrievalSystem
        
        essential_methods = [
            'retrieve_segment',
            'batch_retrieve',
            'get_statistics'
        ]
        
        for method in essential_methods:
            if not hasattr(SegmentRetrievalSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("SegmentRetrievalSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("SegmentRetrievalSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("SegmentRetrievalSystem", False))
    
    # Test Core Index System
    print("\nTesting VersionedCoreIndexSystem...")
    try:
        from src.indexing.versioned_core_index_system import VersionedCoreIndexSystem
        
        essential_methods = [
            'index_folder',
            're_index_folder',
            'verify_file_segments'
        ]
        
        for method in essential_methods:
            if not hasattr(VersionedCoreIndexSystem, method):
                print(f"  ❌ Missing method: {method}")
                results.append(("VersionedCoreIndexSystem", False))
                break
        else:
            print("  ✅ All essential methods present")
            results.append(("VersionedCoreIndexSystem", True))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append(("VersionedCoreIndexSystem", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for component, success in results:
        status = "✅ COMPLETE" if success else "❌ INCOMPLETE"
        print(f"{component:30} {status}")
    
    all_complete = all(success for _, success in results)
    
    if all_complete:
        print("\n🎉 All components are complete!")
    else:
        print("\n⚠️ Some components are incomplete or have errors")
    
    return all_complete

if __name__ == "__main__":
    success = test_component_completeness()
    sys.exit(0 if success else 1)