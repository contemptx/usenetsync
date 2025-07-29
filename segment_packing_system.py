#!/usr/bin/env python3
"""
Segment Packing and Redundancy System for UsenetSync
Optimizes segment creation, packing, and redundancy management
Production implementation with real data handling
"""

import os
import io
import time
import hashlib
import struct
import zlib
import logging
import threading
from typing import List, Dict, Optional, Tuple, Generator, BinaryIO, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

logger = logging.getLogger(__name__)

class PackingStrategy(Enum):
    """Segment packing strategies"""
    SIMPLE = "simple"          # Basic packing without compression
    OPTIMIZED = "optimized"    # Size-optimized packing
    REDUNDANT = "redundant"    # With redundancy
    COMPRESSED = "compressed"  # Pre-compression

@dataclass
class SegmentInfo:
    """Information about a segment"""
    segment_id: int
    file_id: int
    segment_index: int
    data: bytes
    size: int
    hash: str
    offset: int
    redundancy_level: int = 0
    redundancy_index: int = 0  # 0 = original, 1+ = redundant copies
    compressed: bool = False

@dataclass
class PackedSegment:
    """Packed segment ready for upload"""
    packed_id: str
    segments: List[SegmentInfo]
    total_size: int
    header: bytes
    data: bytes
    checksum: str
    redundancy_data: Optional[bytes] = None

@dataclass
class RedundancyInfo:
    """Redundancy information for recovery"""
    redundancy_level: int
    redundant_segments: List[SegmentInfo]  # The redundant copies
    segment_map: Dict[int, List[int]]  # segment_index -> [redundant segment indices]

class SegmentBuffer:
    """Efficient segment buffering and management"""
    
    def __init__(self, max_size: int = 100 * 1024 * 1024):  # 100MB default
        self.max_size = max_size
        self.buffer = io.BytesIO()
        self.segments: List[SegmentInfo] = []
        self.current_size = 0
        self._lock = threading.Lock()
        
    def add_segment(self, segment: SegmentInfo) -> bool:
        """Add segment to buffer"""
        with self._lock:
            if self.current_size + segment.size > self.max_size:
                return False
                
            # Write segment with header
            header = self._create_segment_header(segment)
            self.buffer.write(header)
            self.buffer.write(segment.data)
            
            self.segments.append(segment)
            self.current_size += segment.size + len(header)
            
            return True
            
    def _create_segment_header(self, segment: SegmentInfo) -> bytes:
        """Create segment header with metadata"""
        # Header format:
        # 4 bytes: segment_id
        # 4 bytes: file_id  
        # 4 bytes: segment_index
        # 4 bytes: data_size
        # 32 bytes: hash
        # 1 byte: flags (compressed, redundancy_level)
        # 1 byte: redundancy_index
        
        flags = 0
        if segment.compressed:
            flags |= 0x01
        flags |= (segment.redundancy_level & 0x0F) << 4
        
        header = struct.pack(
            '<IIII32sBB',
            segment.segment_id,
            segment.file_id,
            segment.segment_index,
            segment.size,
            bytes.fromhex(segment.hash),
            flags,
            segment.redundancy_index
        )
        
        return header
        
    def get_packed_data(self) -> bytes:
        """Get all buffered data"""
        with self._lock:
            return self.buffer.getvalue()
            
    def clear(self):
        """Clear buffer"""
        with self._lock:
            self.buffer = io.BytesIO()
            self.segments.clear()
            self.current_size = 0

class RedundancyEngine:
    """Handles redundancy by creating additional segment copies based on redundancy level"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RedundancyEngine")
        
    def generate_redundancy(self, segments: List[SegmentInfo], level: int) -> RedundancyInfo:
        """
        Generate redundancy data for segments based on redundancy level
        
        Level 0: No redundancy
        Level 1: 1 additional copy of each segment
        Level 2: 2 additional copies of each segment
        etc.
        """
        if level <= 0:
            return RedundancyInfo(
                redundancy_level=0,
                redundant_segments=[],
                segment_map={}
            )
            
        redundant_segments = []
        segment_map = {}
        
        # For each original segment, create 'level' number of copies
        for segment in segments:
            copies_for_segment = []
            
            for copy_index in range(1, level + 1):  # Start from 1 since 0 is original
                # Create a copy with same data but different redundancy_index
                redundant_segment = SegmentInfo(
                    segment_id=self._generate_redundant_segment_id(segment.segment_id, copy_index),
                    file_id=segment.file_id,
                    segment_index=segment.segment_index,
                    data=segment.data,  # Same data
                    size=segment.size,
                    hash=segment.hash,  # Same hash
                    offset=segment.offset,
                    redundancy_level=level,
                    redundancy_index=copy_index,  # This identifies it as a redundant copy
                    compressed=segment.compressed
                )
                redundant_segments.append(redundant_segment)
                copies_for_segment.append(len(redundant_segments) - 1)
                
            # Map original segment index to its redundant copies
            segment_map[segment.segment_index] = copies_for_segment
            
        self.logger.info(
            f"Generated redundancy level {level}: "
            f"{len(segments)} original segments -> {len(redundant_segments)} redundant copies"
        )
            
        return RedundancyInfo(
            redundancy_level=level,
            redundant_segments=redundant_segments,
            segment_map=segment_map
        )
        
    def _generate_redundant_segment_id(self, original_id: int, copy_index: int) -> int:
        """Generate unique ID for redundant segment"""
        # Use high bits for copy index to ensure uniqueness
        return original_id | (copy_index << 24)
        
    def can_recover_segment(self, missing_indices: List[int], 
                           redundancy_info: RedundancyInfo) -> bool:
        """Check if missing segments can be recovered"""
        # With redundancy levels, we can recover any segment that has redundant copies
        for idx in missing_indices:
            if idx not in redundancy_info.segment_map or not redundancy_info.segment_map[idx]:
                return False
        return True
        
    def recover_segment(self, segment_index: int, redundancy_info: RedundancyInfo) -> Optional[SegmentInfo]:
        """Recover a missing segment using redundancy data"""
        if segment_index in redundancy_info.segment_map:
            # Get the first available redundant copy
            redundant_indices = redundancy_info.segment_map[segment_index]
            if redundant_indices:
                first_copy_idx = redundant_indices[0]
                if first_copy_idx < len(redundancy_info.redundant_segments):
                    return redundancy_info.redundant_segments[first_copy_idx]
        return None

class SegmentPackingSystem:
    """
    Main segment packing system
    Handles optimal packing, compression, and redundancy
    """
    
    def __init__(self, db_manager, config: Dict[str, Any]):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.segment_size = config.get('segment_size', 768000)  # 750KB
        self.pack_size = config.get('pack_size', 50 * 1024 * 1024)  # 50MB packs
        self.compression_threshold = config.get('compression_threshold', 0.9)
        self.redundancy_engine = RedundancyEngine()
        
        # Performance settings
        self.worker_threads = config.get('worker_threads', 4)
        self.batch_size = config.get('batch_size', 100)
        
        # Statistics
        self.stats = {
            'segments_packed': 0,
            'bytes_packed': 0,
            'compression_ratio': 1.0,
            'redundancy_overhead': 0,
            'files_packed': 0,
            'segments_created': 0,
            'bytes_processed': 0,
            'bytes_original': 0,
            'mb_packed': 0
        }
        
    def pack_file_segments(self, file_path: str, file_id: int,
                          strategy: PackingStrategy = PackingStrategy.OPTIMIZED,
                          redundancy_level: int = 0) -> List[PackedSegment]:
        """
        Pack file into segments with optional redundancy
        Returns list of packed segments ready for upload
        """
        start_time = time.time()
        packed_segments = []
        
        try:
            # Read file and create segments
            segments = self._create_file_segments(file_path, file_id)
            
            if strategy == PackingStrategy.COMPRESSED:
                segments = self._compress_segments(segments)
                
            # Add redundancy if requested
            redundancy_info = None
            if redundancy_level > 0:
                # Update original segments with redundancy level
                for seg in segments:
                    seg.redundancy_level = redundancy_level
                    seg.redundancy_index = 0  # Mark as original
                    
                redundancy_info = self._add_redundancy(segments, redundancy_level)
                
            # Pack segments
            if strategy == PackingStrategy.OPTIMIZED:
                packed = self._pack_optimized(segments, redundancy_info)
            else:
                packed = self._pack_sequential(segments, redundancy_info)
                
            packed_segments.extend(packed)
            
            # Update statistics
            self.stats['segments_packed'] += len(segments)
            self.stats['bytes_packed'] += os.path.getsize(file_path)
            self.stats['files_packed'] += 1
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"Packed {len(segments)} segments from {file_path} "
                f"into {len(packed_segments)} packs in {elapsed:.2f}s"
            )
            
            # Store segments in database including redundant ones
            if redundancy_info:
                self._store_redundant_segments(file_id, redundancy_info)
            
        except Exception as e:
            self.logger.error(f"Error packing file {file_path}: {e}")
            raise
            
        return packed_segments
        
    def _create_file_segments(self, file_path: str, file_id: int) -> List[SegmentInfo]:
        """Create segments from file"""
        segments = []
        segment_index = 0
        
        with open(file_path, 'rb') as f:
            while True:
                offset = f.tell()
                data = f.read(self.segment_size)
                if not data:
                    break
                    
                # Calculate hash
                segment_hash = hashlib.sha256(data).hexdigest()
                
                segment = SegmentInfo(
                    segment_id=self._generate_segment_id(file_id, segment_index),
                    file_id=file_id,
                    segment_index=segment_index,
                    data=data,
                    size=len(data),
                    hash=segment_hash,
                    offset=offset,
                    redundancy_level=0,
                    redundancy_index=0  # Original segment
                )
                
                segments.append(segment)
                segment_index += 1
                
        self.stats['segments_created'] += len(segments)
        self.stats['bytes_processed'] += sum(s.size for s in segments)
        
        return segments
        
    def _compress_segments(self, segments: List[SegmentInfo]) -> List[SegmentInfo]:
        """Compress segments if beneficial"""
        compressed_segments = []
        
        for segment in segments:
            compressed_data = zlib.compress(segment.data, level=6)
            
            # Only use compression if it saves space
            if len(compressed_data) < len(segment.data) * self.compression_threshold:
                new_segment = SegmentInfo(
                    segment_id=segment.segment_id,
                    file_id=segment.file_id,
                    segment_index=segment.segment_index,
                    data=compressed_data,
                    size=len(compressed_data),
                    hash=hashlib.sha256(compressed_data).hexdigest(),
                    offset=segment.offset,
                    redundancy_level=segment.redundancy_level,
                    redundancy_index=segment.redundancy_index,
                    compressed=True
                )
                compressed_segments.append(new_segment)
                self.logger.debug(
                    f"Compressed segment {segment.segment_index}: "
                    f"{segment.size} -> {new_segment.size} bytes"
                )
            else:
                compressed_segments.append(segment)
                
        return compressed_segments
        
    def _add_redundancy(self, segments: List[SegmentInfo], level: int) -> RedundancyInfo:
        """Add redundancy to segments"""
        # Generate redundancy info
        redundancy_info = self.redundancy_engine.generate_redundancy(segments, level)
        
        # Track overhead
        redundancy_size = sum(seg.size for seg in redundancy_info.redundant_segments)
        original_size = sum(seg.size for seg in segments)
        if original_size > 0:
            self.stats['redundancy_overhead'] = redundancy_size / original_size
        
        self.logger.info(
            f"Added redundancy level {level}: "
            f"{len(redundancy_info.redundant_segments)} redundant segments "
            f"({redundancy_size / 1024 / 1024:.2f} MB)"
        )
        
        return redundancy_info
        
    def _store_redundant_segments(self, file_id: int, redundancy_info: RedundancyInfo):
        """Store redundant segments in database"""
        # The redundant segments will be uploaded separately with different message IDs
        # but we need to track them in the database
        for red_segment in redundancy_info.redundant_segments:
            # Note: In actual upload, each redundant segment gets its own message_id
            self.db.add_segment(
                file_id=red_segment.file_id,
                segment_index=red_segment.segment_index,
                segment_hash=red_segment.hash,
                segment_size=red_segment.size,
                subject_hash=hashlib.sha256(
                    f"{red_segment.file_id}:{red_segment.segment_index}:{red_segment.redundancy_index}".encode()
                ).hexdigest(),
                newsgroup=self.config.get('newsgroup', 'alt.binaries.test'),
                redundancy_index=red_segment.redundancy_index
            )
        
    def _pack_sequential(self, segments: List[SegmentInfo],
                        redundancy_info: Optional[RedundancyInfo]) -> List[PackedSegment]:
        """Simple sequential packing"""
        packed = []
        buffer = SegmentBuffer(self.pack_size)
        
        # Pack original segments
        for segment in segments:
            if not buffer.add_segment(segment):
                # Buffer full, create pack
                packed.append(self._create_packed_segment(buffer, redundancy_info))
                buffer.clear()
                buffer.add_segment(segment)
                
        # Pack remaining
        if buffer.segments:
            packed.append(self._create_packed_segment(buffer, redundancy_info))
            
        return packed
        
    def _pack_optimized(self, segments: List[SegmentInfo],
                       redundancy_info: Optional[RedundancyInfo]) -> List[PackedSegment]:
        """Optimized packing to minimize waste"""
        packed = []
        
        # Sort segments by size for better packing
        sorted_segments = sorted(segments, key=lambda s: s.size, reverse=True)
        
        # Use first-fit decreasing algorithm
        buffers = []
        
        for segment in sorted_segments:
            placed = False
            
            # Try to fit in existing buffers
            for buffer in buffers:
                if buffer.current_size + segment.size <= self.pack_size:
                    buffer.add_segment(segment)
                    placed = True
                    break
                    
            # Create new buffer if needed
            if not placed:
                buffer = SegmentBuffer(self.pack_size)
                buffer.add_segment(segment)
                buffers.append(buffer)
                
        # Create packed segments
        for buffer in buffers:
            if buffer.segments:
                packed.append(self._create_packed_segment(buffer, redundancy_info))
                
        self.logger.info(
            f"Optimized packing: {len(segments)} segments -> {len(packed)} packs, "
            f"efficiency: {self._calculate_packing_efficiency(packed):.1f}%"
        )
        
        return packed
        
    def _create_packed_segment(self, buffer: SegmentBuffer,
                              redundancy_info: Optional[RedundancyInfo]) -> PackedSegment:
        """Create packed segment from buffer"""
        # Generate packed ID
        packed_id = self._generate_packed_id(buffer.segments)
        
        # Create header
        header = self._create_pack_header(buffer.segments, redundancy_info)
        
        # Get packed data
        data = buffer.get_packed_data()
        
        # Add redundancy data if present
        redundancy_data = None
        if redundancy_info:
            redundancy_data = self._pack_redundancy_data(redundancy_info)
            
        # Calculate checksum
        checksum = hashlib.sha256(header + data).hexdigest()
        
        return PackedSegment(
            packed_id=packed_id,
            segments=buffer.segments.copy(),
            total_size=len(header) + len(data),
            header=header,
            data=data,
            checksum=checksum,
            redundancy_data=redundancy_data
        )
        
    def _create_pack_header(self, segments: List[SegmentInfo],
                           redundancy_info: Optional[RedundancyInfo]) -> bytes:
        """Create pack header with metadata"""
        header = io.BytesIO()
        
        # Magic number
        header.write(b'USPK')  # UsenetSync Pack
        
        # Version
        header.write(struct.pack('<H', 1))
        
        # Flags
        flags = 0
        if any(seg.compressed for seg in segments):
            flags |= 0x01
        if redundancy_info:
            flags |= 0x02
        header.write(struct.pack('B', flags))
        
        # Segment count
        header.write(struct.pack('<I', len(segments)))
        
        # Redundancy info if present
        if redundancy_info:
            header.write(struct.pack('B', redundancy_info.redundancy_level))
            header.write(struct.pack('<I', len(redundancy_info.redundant_segments)))
            
        # Segment table
        for seg in segments:
            header.write(struct.pack('<III', seg.segment_id, seg.file_id, seg.segment_index))
            
        return header.getvalue()
        
    def _pack_redundancy_data(self, redundancy_info: RedundancyInfo) -> bytes:
        """Pack redundancy metadata"""
        buffer = io.BytesIO()
        
        # Write redundancy level
        buffer.write(struct.pack('B', redundancy_info.redundancy_level))
        
        # Write number of redundant segments
        buffer.write(struct.pack('<I', len(redundancy_info.redundant_segments)))
        
        # Write segment map
        buffer.write(struct.pack('<I', len(redundancy_info.segment_map)))
        for seg_idx, red_indices in redundancy_info.segment_map.items():
            buffer.write(struct.pack('<I', seg_idx))
            buffer.write(struct.pack('<I', len(red_indices)))
            for red_idx in red_indices:
                buffer.write(struct.pack('<I', red_idx))
                
        return buffer.getvalue()
        
    def _generate_segment_id(self, file_id: int, segment_index: int) -> int:
        """Generate unique segment ID"""
        # Simple but effective: combine file_id and segment_index
        return (file_id << 20) | (segment_index & 0xFFFFF)
        
    def _generate_packed_id(self, segments: List[SegmentInfo]) -> str:
        """Generate unique ID for packed segment"""
        # Use hash of segment IDs
        id_data = b''.join(
            struct.pack('<I', seg.segment_id) for seg in segments
        )
        return hashlib.sha256(id_data).hexdigest()[:16]
        
    def _calculate_packing_efficiency(self, packed: List[PackedSegment]) -> float:
        """Calculate packing efficiency percentage"""
        total_data = sum(sum(seg.size for seg in pack.segments) for pack in packed)
        total_packed = sum(pack.total_size for pack in packed)
        return (total_data / total_packed) * 100 if total_packed > 0 else 0
        
    def unpack_segment(self, packed_data: bytes) -> Tuple[List[SegmentInfo], Optional[RedundancyInfo]]:
        """Unpack a packed segment"""
        buffer = io.BytesIO(packed_data)
        
        # Read header
        magic = buffer.read(4)
        if magic != b'USPK':
            raise ValueError("Invalid pack format")
            
        version = struct.unpack('<H', buffer.read(2))[0]
        flags = struct.unpack('B', buffer.read(1))[0]
        segment_count = struct.unpack('<I', buffer.read(4))[0]
        
        # Read redundancy info if present
        redundancy_info = None
        if flags & 0x02:
            red_level = struct.unpack('B', buffer.read(1))[0]
            red_count = struct.unpack('<I', buffer.read(4))[0]
            redundancy_info = {
                'level': red_level,
                'count': red_count
            }
            
        # Read segment table
        segment_ids = []
        for _ in range(segment_count):
            seg_id, file_id, seg_idx = struct.unpack('<III', buffer.read(12))
            segment_ids.append((seg_id, file_id, seg_idx))
            
        # Read segments
        segments = []
        for seg_id, file_id, seg_idx in segment_ids:
            # Read segment header (50 bytes now with redundancy_index)
            header_data = buffer.read(50)
            
            seg_id_read, file_id_read, seg_idx_read, size, hash_bytes, flags, red_idx = struct.unpack(
                '<IIII32sBB', header_data
            )
            
            # Read segment data
            data = buffer.read(size)
            
            segment = SegmentInfo(
                segment_id=seg_id_read,
                file_id=file_id_read,
                segment_index=seg_idx_read,
                data=data,
                size=size,
                hash=hash_bytes.hex(),
                offset=0,  # Not stored in pack
                compressed=(flags & 0x01) != 0,
                redundancy_level=(flags >> 4) & 0x0F,
                redundancy_index=red_idx
            )
            segments.append(segment)
            
        return segments, redundancy_info
        
    def verify_packed_segment(self, packed: PackedSegment) -> bool:
        """Verify packed segment integrity"""
        # Recalculate checksum
        calculated = hashlib.sha256(packed.header + packed.data).hexdigest()
        return calculated == packed.checksum
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get packing statistics"""
        # Update derived stats
        if self.stats['bytes_packed'] > 0:
            self.stats['mb_packed'] = self.stats['bytes_packed'] / (1024 * 1024)
        
        if self.stats['bytes_original'] > 0:
            self.stats['compression_ratio'] = self.stats['bytes_packed'] / self.stats['bytes_original']
        
        return self.stats.copy()
        
    def optimize_pack_size(self, typical_file_size: int) -> int:
        """Calculate optimal pack size for given file sizes"""
        # Balance between upload efficiency and redundancy granularity
        if typical_file_size < 10 * 1024 * 1024:  # < 10MB files
            return 50 * 1024 * 1024  # 50MB packs
        elif typical_file_size < 100 * 1024 * 1024:  # < 100MB files
            return 100 * 1024 * 1024  # 100MB packs
        else:
            return 200 * 1024 * 1024  # 200MB packs for large files
