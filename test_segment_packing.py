#!/usr/bin/env python3
"""
Test to verify that segment packing combines small files into larger articles
"""

import os
import sys
import tempfile
import hashlib
from pathlib import Path

sys.path.insert(0, '/workspace')

from src.upload.segment_packing_system import SegmentPackingSystem, SegmentInfo
from src.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig


def test_segment_packing():
    """Test that small files are packed together efficiently"""
    print("\n" + "="*80)
    print("SEGMENT PACKING TEST - Verifying Small File Combination")
    print("="*80)
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp(prefix='packing_test_')
    db_path = os.path.join(temp_dir, 'test.db')
    
    # Initialize database
    db_config = DatabaseConfig()
    db_config.path = db_path
    db_manager = EnhancedDatabaseManager(db_config)
    
    # Create packing system with test config
    config = {
        'segment_size': 768000,  # 750KB segments
        'pack_size': 5 * 1024 * 1024,  # 5MB packs for testing
        'packing_strategy': 'optimized'
    }
    
    packing_system = SegmentPackingSystem(db_manager, config)
    
    print(f"\n📊 Configuration:")
    print(f"  Segment Size: {config['segment_size']:,} bytes (750KB)")
    print(f"  Pack Size: {config['pack_size']:,} bytes (5MB)")
    print(f"  Strategy: {config['packing_strategy']}")
    
    # Create test files of various sizes
    test_files = [
        # Small files that should be packed together
        {'name': 'file1.txt', 'size': 100 * 1024},   # 100KB
        {'name': 'file2.txt', 'size': 200 * 1024},   # 200KB
        {'name': 'file3.txt', 'size': 150 * 1024},   # 150KB
        {'name': 'file4.txt', 'size': 300 * 1024},   # 300KB
        {'name': 'file5.txt', 'size': 250 * 1024},   # 250KB
        # Total: 1MB - should fit in one pack
        
        # Medium files
        {'name': 'file6.txt', 'size': 500 * 1024},   # 500KB
        {'name': 'file7.txt', 'size': 600 * 1024},   # 600KB
        # Total: 1.1MB - should be in same or separate pack
        
        # Large file that needs multiple segments
        {'name': 'file8.txt', 'size': 2 * 1024 * 1024},  # 2MB
    ]
    
    print(f"\n📁 Creating {len(test_files)} test files:")
    print("-" * 50)
    
    segments = []
    total_size = 0
    
    for i, file_info in enumerate(test_files):
        # Create fake file data
        data = b'X' * file_info['size']
        file_hash = hashlib.sha256(data).hexdigest()
        
        # Create segments for this file
        file_segments = []
        segment_index = 0
        
        for offset in range(0, file_info['size'], config['segment_size']):
            segment_data = data[offset:offset + config['segment_size']]
            
            segment = SegmentInfo(
                segment_id=len(segments),
                file_id=i,
                segment_index=segment_index,
                data=segment_data,
                size=len(segment_data),
                hash=hashlib.sha256(segment_data).hexdigest(),
                offset=offset,  # Add the offset field
                compressed=False,
                redundancy_level=0,
                redundancy_index=0
            )
            
            segments.append(segment)
            file_segments.append(segment)
            segment_index += 1
            
        total_size += file_info['size']
        print(f"  • {file_info['name']}: {file_info['size']:,} bytes → {len(file_segments)} segment(s)")
    
    print(f"\n📊 Total: {total_size:,} bytes in {len(segments)} segments")
    
    # Now pack the segments
    print(f"\n📦 Packing segments into {config['pack_size']:,} byte articles...")
    print("-" * 50)
    
    packed_segments = packing_system._pack_optimized(segments, None)
    
    print(f"\n✅ Packing Results:")
    print(f"  Input: {len(segments)} segments, {total_size:,} bytes")
    print(f"  Output: {len(packed_segments)} packed articles")
    
    # Analyze packing efficiency
    print(f"\n📈 Packing Analysis:")
    for i, pack in enumerate(packed_segments):
        segments_in_pack = len(pack.segments)
        pack_size = len(pack.data)
        efficiency = (pack_size / config['pack_size']) * 100
        
        print(f"\n  Pack {i+1}:")
        print(f"    Segments: {segments_in_pack}")
        print(f"    Size: {pack_size:,} bytes")
        print(f"    Efficiency: {efficiency:.1f}% of max pack size")
        
        # Get segment IDs from pack.segments
        segment_ids = [seg.segment_id for seg in pack.segments]
        print(f"    Segment IDs: {segment_ids[:5]}{'...' if len(segment_ids) > 5 else ''}")
        
        # Check which files are in this pack
        file_ids = set()
        for seg_id in segment_ids:
            if seg_id < len(segments):
                file_ids.add(segments[seg_id].file_id)
        
        if len(file_ids) > 1:
            print(f"    ✅ Contains segments from {len(file_ids)} different files (good packing!)")
        else:
            print(f"    📄 Contains segments from 1 file only")
    
    # Calculate overall efficiency
    total_packed_size = sum(len(p.data) for p in packed_segments)
    max_possible_size = len(packed_segments) * config['pack_size']
    overall_efficiency = (total_packed_size / max_possible_size) * 100 if max_possible_size > 0 else 0
    
    print(f"\n📊 Overall Packing Efficiency: {overall_efficiency:.1f}%")
    
    # Verify that small files were combined
    small_files_packed_together = False
    for pack in packed_segments:
        file_ids = set()
        segment_ids = [seg.segment_id for seg in pack.segments]
        for seg_id in segment_ids:
            if seg_id < len(segments):
                file_ids.add(segments[seg_id].file_id)
        
        # Check if pack contains multiple small files (files 0-4)
        small_file_ids = set(range(5))  # First 5 files are small
        if len(file_ids.intersection(small_file_ids)) > 1:
            small_files_packed_together = True
            break
    
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    if small_files_packed_together:
        print("✅ SUCCESS: Small files are being packed together into larger articles!")
        print("   The segment packing system is working efficiently.")
    else:
        print("⚠️  WARNING: Small files may not be optimally packed together.")
        print("   Check packing strategy configuration.")
    
    print(f"\n📊 Summary:")
    print(f"  • {len(test_files)} files → {len(segments)} segments → {len(packed_segments)} articles")
    print(f"  • Packing reduced article count by {((1 - len(packed_segments)/len(segments)) * 100):.1f}%")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    return small_files_packed_together


if __name__ == "__main__":
    success = test_segment_packing()
    sys.exit(0 if success else 1)