#!/usr/bin/env python3
"""
Unified Segment Processor - File segmentation with 768KB segments
Production-ready with streaming and parallel processing
"""

import os
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass, asdict
import concurrent.futures
import logging

logger = logging.getLogger(__name__)

@dataclass
class Segment:
    """Segment data structure"""
    segment_id: str
    file_id: str
    segment_index: int
    data: bytes
    size: int
    hash: str
    offset_start: int
    offset_end: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without data)"""
        d = asdict(self)
        del d['data']  # Don't include raw data in dict
        return d

class UnifiedSegmentProcessor:
    """
    Unified segment processor
    Creates 768KB segments from files with streaming support
    """
    
    # Standard segment size (750KB)
    SEGMENT_SIZE = 768000
    
    def __init__(self, db=None, config=None):
        """Initialize segment processor"""
        self.db = db
        self.config = config or {}
        self.segment_size = self.config.get('segment_size', self.SEGMENT_SIZE)
        self.buffer_size = self.config.get('buffer_size', 65536)
        self.worker_threads = self.config.get('worker_threads', 4)
        self._segment_cache = {}
    
    def segment_file(self, file_path: str, file_id: Optional[str] = None,
                    calculate_hash: bool = True,
                    progress_callback: Optional[callable] = None) -> List[Segment]:
        """
        Segment file into chunks
        
        Args:
            file_path: Path to file to segment
            file_id: Optional file ID
            calculate_hash: Whether to calculate segment hashes
            progress_callback: Progress callback function
        
        Returns:
            List of segments
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        file_size = file_path.stat().st_size
        file_id = file_id or str(uuid.uuid4())
        
        logger.info(f"Segmenting file: {file_path} ({file_size} bytes)")
        
        segments = []
        segment_index = 0
        bytes_processed = 0
        
        with open(file_path, 'rb') as f:
            while True:
                offset_start = f.tell()
                data = f.read(self.segment_size)
                
                if not data:
                    break
                
                offset_end = f.tell()
                
                # Create segment
                segment = Segment(
                    segment_id=str(uuid.uuid4()),
                    file_id=file_id,
                    segment_index=segment_index,
                    data=data,
                    size=len(data),
                    hash=self._calculate_hash(data) if calculate_hash else "",
                    offset_start=offset_start,
                    offset_end=offset_end
                )
                
                segments.append(segment)
                segment_index += 1
                bytes_processed += len(data)
                
                if progress_callback:
                    progress_callback(bytes_processed, file_size)
        
        logger.info(f"Created {len(segments)} segments from {file_path}")
        
        return segments
    
    def segment_file_streaming(self, file_path: str, file_id: Optional[str] = None,
                              calculate_hash: bool = True) -> Generator[Segment, None, None]:
        """
        Segment file with streaming (memory efficient)
        
        Args:
            file_path: Path to file
            file_id: Optional file ID
            calculate_hash: Whether to calculate hashes
        
        Yields:
            Segments one at a time
        """
        file_path = Path(file_path)
        file_id = file_id or str(uuid.uuid4())
        
        segment_index = 0
        
        with open(file_path, 'rb') as f:
            while True:
                offset_start = f.tell()
                data = f.read(self.segment_size)
                
                if not data:
                    break
                
                offset_end = f.tell()
                
                yield Segment(
                    segment_id=str(uuid.uuid4()),
                    file_id=file_id,
                    segment_index=segment_index,
                    data=data,
                    size=len(data),
                    hash=self._calculate_hash(data) if calculate_hash else "",
                    offset_start=offset_start,
                    offset_end=offset_end
                )
                
                segment_index += 1
    
    def segment_data(self, data: bytes, file_id: Optional[str] = None,
                    calculate_hash: bool = True) -> List[Segment]:
        """
        Segment raw data
        
        Args:
            data: Data to segment
            file_id: Optional file ID
            calculate_hash: Whether to calculate hashes
        
        Returns:
            List of segments
        """
        file_id = file_id or str(uuid.uuid4())
        segments = []
        
        for i in range(0, len(data), self.segment_size):
            segment_data = data[i:i + self.segment_size]
            
            segments.append(Segment(
                segment_id=str(uuid.uuid4()),
                file_id=file_id,
                segment_index=len(segments),
                data=segment_data,
                size=len(segment_data),
                hash=self._calculate_hash(segment_data) if calculate_hash else "",
                offset_start=i,
                offset_end=i + len(segment_data)
            ))
        
        return segments
    
    def reconstruct_file(self, segments: List[Segment], output_path: str,
                        verify_hash: bool = True,
                        progress_callback: Optional[callable] = None) -> bool:
        """
        Reconstruct file from segments
        
        Args:
            segments: List of segments
            output_path: Output file path
            verify_hash: Whether to verify segment hashes
            progress_callback: Progress callback
        
        Returns:
            True if successful
        """
        # Sort segments by index
        segments.sort(key=lambda s: s.segment_index)
        
        # Verify continuity
        for i, segment in enumerate(segments):
            if segment.segment_index != i:
                raise ValueError(f"Missing segment {i}")
        
        total_size = sum(s.size for s in segments)
        bytes_written = 0
        
        with open(output_path, 'wb') as f:
            for segment in segments:
                # Verify hash if requested
                if verify_hash and segment.hash:
                    calculated_hash = self._calculate_hash(segment.data)
                    if calculated_hash != segment.hash:
                        raise ValueError(f"Hash mismatch for segment {segment.segment_index}")
                
                f.write(segment.data)
                bytes_written += segment.size
                
                if progress_callback:
                    progress_callback(bytes_written, total_size)
        
        logger.info(f"Reconstructed file: {output_path} ({bytes_written} bytes)")
        
        return True
    
    def parallel_segment_files(self, file_paths: List[str],
                              calculate_hash: bool = True) -> Dict[str, List[Segment]]:
        """
        Segment multiple files in parallel
        
        Args:
            file_paths: List of file paths
            calculate_hash: Whether to calculate hashes
        
        Returns:
            Dictionary of file_path -> segments
        """
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.worker_threads) as executor:
            futures = {
                executor.submit(self.segment_file, path, calculate_hash=calculate_hash): path
                for path in file_paths
            }
            
            for future in concurrent.futures.as_completed(futures):
                path = futures[future]
                try:
                    segments = future.result()
                    results[path] = segments
                except Exception as e:
                    logger.error(f"Error segmenting {path}: {e}")
                    results[path] = []
        
        return results
    
    def calculate_segment_tree_hash(self, segments: List[Segment]) -> str:
        """
        Calculate Merkle tree hash of segments
        
        Args:
            segments: List of segments
        
        Returns:
            Root hash of Merkle tree
        """
        if not segments:
            return ""
        
        # Sort segments
        segments.sort(key=lambda s: s.segment_index)
        
        # Build Merkle tree
        hashes = [s.hash for s in segments]
        
        while len(hashes) > 1:
            new_hashes = []
            
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate last if odd
                
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            hashes = new_hashes
        
        return hashes[0]
    
    def verify_segments(self, segments: List[Segment]) -> Tuple[bool, List[int]]:
        """
        Verify segment integrity
        
        Args:
            segments: List of segments to verify
        
        Returns:
            Tuple of (all_valid, list_of_invalid_indices)
        """
        invalid_indices = []
        
        for segment in segments:
            if segment.hash:
                calculated_hash = self._calculate_hash(segment.data)
                if calculated_hash != segment.hash:
                    invalid_indices.append(segment.segment_index)
        
        return len(invalid_indices) == 0, invalid_indices
    
    def get_segment_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get segmentation information for a file
        
        Args:
            file_path: Path to file
        
        Returns:
            Segmentation information
        """
        file_size = os.path.getsize(file_path)
        num_segments = (file_size + self.segment_size - 1) // self.segment_size
        last_segment_size = file_size % self.segment_size or self.segment_size
        
        return {
            'file_size': file_size,
            'segment_size': self.segment_size,
            'num_segments': num_segments,
            'last_segment_size': last_segment_size,
            'total_overhead': num_segments * 64  # Hash overhead per segment
        }
    
    def _calculate_hash(self, data: bytes) -> str:
        """Calculate SHA256 hash of data"""
        return hashlib.sha256(data).hexdigest()
    
    def store_segments(self, segments: List[Segment]) -> bool:
        """
        Store segments in database
        
        Args:
            segments: List of segments to store
        
        Returns:
            True if successful
        """
        if not self.db:
            raise ValueError("Database not configured")
        
        for segment in segments:
            segment_data = segment.to_dict()
            
            # Store in database (without raw data)
            self.db.insert('segments', segment_data)
        
        logger.info(f"Stored {len(segments)} segments in database")
        
        return True
    
    def load_segments(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Load segment metadata from database
        
        Args:
            file_id: File ID to load segments for
        
        Returns:
            List of segment metadata
        """
        if not self.db:
            raise ValueError("Database not configured")
        
        segments = self.db.fetch_all(
            "SELECT * FROM segments WHERE file_id = ? ORDER BY segment_index",
            (file_id,)
        )
        
        return segments