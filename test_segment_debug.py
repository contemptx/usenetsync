#!/usr/bin/env python3
"""Debug segmentation issue"""

import sys
import os
sys.path.insert(0, '/workspace/backend/src')

from unified.segmentation.processor import UnifiedSegmentProcessor

# Test direct segmentation
processor = UnifiedSegmentProcessor()

test_file = "/workspace/test_workflow_folder/file1.txt"
print(f"Testing segmentation of: {test_file}")

try:
    segments = processor.segment_file(test_file, file_id="test_file_1")
    print(f"Success! Created {len(segments)} segments")
    for i, seg in enumerate(segments):
        print(f"  Segment {i}: ID={seg.segment_id[:8]}... size={seg.size} bytes")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()