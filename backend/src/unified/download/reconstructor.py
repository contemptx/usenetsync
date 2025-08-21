#!/usr/bin/env python3
"""
Unified Reconstructor - Reconstruct files from segments
Production-ready with integrity verification and streaming
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

class UnifiedReconstructor:
    """
    Unified file reconstructor
    Reconstructs files from downloaded segments
    """
    
    def __init__(self, config=None):
        """Initialize reconstructor"""
        self.config = config or {}
        self.verify_hashes = self.config.get('verify_hashes', True)
        self.buffer_size = self.config.get('buffer_size', 65536)
        self._statistics = {
            'files_reconstructed': 0,
            'bytes_written': 0,
            'hash_failures': 0
        }
    
    def reconstruct_file(self, segments: List[Dict[str, Any]], 
                        output_path: str,
                        file_hash: Optional[str] = None,
                        progress_callback: Optional[callable] = None) -> bool:
        """
        Reconstruct file from segments
        
        Args:
            segments: List of segment data with metadata
            output_path: Output file path
            file_hash: Optional expected file hash
            progress_callback: Progress callback
        
        Returns:
            True if successful
        """
        try:
            # Sort segments by index
            segments.sort(key=lambda s: s.get('segment_index', 0))
            
            # Verify segment continuity
            for i, segment in enumerate(segments):
                expected_index = i
                actual_index = segment.get('segment_index', -1)
                
                if actual_index != expected_index:
                    logger.error(f"Missing segment {expected_index}")
                    return False
            
            # Calculate total size
            total_size = sum(len(s.get('data', b'')) for s in segments)
            bytes_written = 0
            
            # Create output directory if needed
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write segments to file
            hasher = hashlib.sha256() if file_hash else None
            
            with open(output_path, 'wb') as f:
                for segment in segments:
                    data = segment.get('data', b'')
                    
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    
                    # Verify segment hash if available
                    if self.verify_hashes and 'hash' in segment:
                        segment_hash = hashlib.sha256(data).hexdigest()
                        if segment_hash != segment['hash']:
                            logger.error(f"Hash mismatch for segment {segment.get('segment_index')}")
                            self._statistics['hash_failures'] += 1
                            return False
                    
                    # Write data
                    f.write(data)
                    bytes_written += len(data)
                    
                    # Update file hash
                    if hasher:
                        hasher.update(data)
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(bytes_written, total_size)
            
            # Verify file hash
            if file_hash and hasher:
                calculated_hash = hasher.hexdigest()
                if calculated_hash != file_hash:
                    logger.error(f"File hash mismatch: expected {file_hash}, got {calculated_hash}")
                    os.remove(output_path)
                    return False
            
            self._statistics['files_reconstructed'] += 1
            self._statistics['bytes_written'] += bytes_written
            
            logger.info(f"Reconstructed file: {output_path} ({bytes_written:,} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Reconstruction failed: {e}")
            # Clean up partial file
            if output_path.exists():
                os.remove(output_path)
            return False
    
    def reconstruct_packed_files(self, packed_data: bytes,
                                output_dir: str) -> List[str]:
        """
        Reconstruct packed files
        
        Args:
            packed_data: Packed segment data
            output_dir: Output directory
        
        Returns:
            List of extracted file paths
        """
        from ..segmentation.packing import UnifiedPacking
        
        packing = UnifiedPacking()
        extracted_files = []
        
        try:
            # Unpack files
            files = packing.unpack_segment(packed_data)
            
            # Write each file
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, data in files:
                file_path = output_dir / filename
                
                # Ensure safe path
                if not str(file_path).startswith(str(output_dir)):
                    logger.warning(f"Skipping unsafe path: {filename}")
                    continue
                
                # Write file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(data)
                
                extracted_files.append(str(file_path))
                logger.debug(f"Extracted: {file_path}")
            
            logger.info(f"Extracted {len(extracted_files)} packed files")
            
        except Exception as e:
            logger.error(f"Failed to unpack files: {e}")
        
        return extracted_files
    
    def streaming_reconstruct(self, segment_generator,
                            output_path: str,
                            expected_segments: int) -> bool:
        """
        Reconstruct file with streaming (memory efficient)
        
        Args:
            segment_generator: Generator yielding segments
            output_path: Output file path
            expected_segments: Expected number of segments
        
        Returns:
            True if successful
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            segments_received = 0
            bytes_written = 0
            
            with open(output_path, 'wb') as f:
                for segment in segment_generator:
                    # Extract data
                    data = segment.get('data', b'')
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    
                    # Verify index
                    expected_index = segments_received
                    actual_index = segment.get('segment_index', -1)
                    
                    if actual_index != expected_index:
                        logger.error(f"Out of order segment: expected {expected_index}, got {actual_index}")
                        return False
                    
                    # Write data
                    f.write(data)
                    bytes_written += len(data)
                    segments_received += 1
                    
                    logger.debug(f"Wrote segment {segments_received}/{expected_segments}")
            
            # Verify we got all segments
            if segments_received != expected_segments:
                logger.error(f"Incomplete: got {segments_received}, expected {expected_segments}")
                os.remove(output_path)
                return False
            
            logger.info(f"Streaming reconstruction complete: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Streaming reconstruction failed: {e}")
            if output_path.exists():
                os.remove(output_path)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reconstruction statistics"""
        return self._statistics.copy()