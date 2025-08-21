#!/usr/bin/env python3
"""
Unified Packing Module - Pack small files together for efficiency
Production-ready with multiple packing strategies
"""

import uuid
import struct
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PackedSegment:
    """Packed segment containing multiple small files"""
    packed_id: str
    files: List[Dict[str, Any]]
    total_size: int
    data: bytes
    metadata: Dict[str, Any]

class UnifiedPacking:
    """
    Unified packing system for small files
    Packs files < 750KB together for efficiency
    """
    
    def __init__(self, segment_size: int = 768000):
        """Initialize packing system"""
        self.segment_size = segment_size
        self.min_pack_size = segment_size // 2  # Pack files smaller than half segment
    
    def pack_files(self, files: List[Tuple[str, bytes]]) -> List[PackedSegment]:
        """
        Pack multiple small files together
        
        Args:
            files: List of (filename, data) tuples
        
        Returns:
            List of packed segments
        """
        packed_segments = []
        current_pack = []
        current_size = 0
        
        for filename, data in files:
            file_size = len(data)
            
            # If file is too large to pack, skip it
            if file_size >= self.min_pack_size:
                continue
            
            # If adding this file would exceed segment size, create new pack
            if current_size + file_size + 256 > self.segment_size:  # 256 bytes for headers
                if current_pack:
                    packed_segments.append(self._create_packed_segment(current_pack))
                current_pack = []
                current_size = 0
            
            current_pack.append((filename, data))
            current_size += file_size
        
        # Pack remaining files
        if current_pack:
            packed_segments.append(self._create_packed_segment(current_pack))
        
        logger.info(f"Packed {len(files)} files into {len(packed_segments)} segments")
        
        return packed_segments
    
    def _create_packed_segment(self, files: List[Tuple[str, bytes]]) -> PackedSegment:
        """Create a packed segment from files"""
        packed_id = str(uuid.uuid4())
        
        # Create header
        header = {
            'version': 1,
            'file_count': len(files),
            'files': []
        }
        
        # Pack files
        packed_data = bytearray()
        offset = 0
        
        for filename, data in files:
            file_info = {
                'name': filename,
                'offset': offset,
                'size': len(data)
            }
            header['files'].append(file_info)
            
            packed_data.extend(data)
            offset += len(data)
        
        # Serialize header
        header_json = json.dumps(header).encode('utf-8')
        header_size = len(header_json)
        
        # Create final packed data with header
        final_data = struct.pack('<I', header_size) + header_json + packed_data
        
        return PackedSegment(
            packed_id=packed_id,
            files=header['files'],
            total_size=len(final_data),
            data=bytes(final_data),
            metadata=header
        )
    
    def unpack_segment(self, packed_data: bytes) -> List[Tuple[str, bytes]]:
        """
        Unpack a packed segment
        
        Args:
            packed_data: Packed segment data
        
        Returns:
            List of (filename, data) tuples
        """
        # Read header size
        header_size = struct.unpack('<I', packed_data[:4])[0]
        
        # Read header
        header_json = packed_data[4:4+header_size]
        header = json.loads(header_json.decode('utf-8'))
        
        # Extract files
        files = []
        data_start = 4 + header_size
        
        for file_info in header['files']:
            offset = data_start + file_info['offset']
            size = file_info['size']
            
            file_data = packed_data[offset:offset+size]
            files.append((file_info['name'], file_data))
        
        return files
    
    def should_pack_file(self, file_size: int) -> bool:
        """
        Determine if file should be packed
        
        Args:
            file_size: Size of file in bytes
        
        Returns:
            True if file should be packed
        """
        return file_size < self.min_pack_size
    
    def optimize_packing(self, files: List[Tuple[str, int]]) -> List[List[str]]:
        """
        Optimize file packing arrangement
        
        Args:
            files: List of (filename, size) tuples
        
        Returns:
            List of file groups for packing
        """
        # Sort files by size (descending) for better packing
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
        
        packs = []
        current_pack = []
        current_size = 0
        
        for filename, size in sorted_files:
            if size >= self.min_pack_size:
                continue
            
            if current_size + size <= self.segment_size - 256:
                current_pack.append(filename)
                current_size += size
            else:
                if current_pack:
                    packs.append(current_pack)
                current_pack = [filename]
                current_size = size
        
        if current_pack:
            packs.append(current_pack)
        
        return packs