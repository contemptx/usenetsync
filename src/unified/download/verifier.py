#!/usr/bin/env python3
"""
Unified Verifier - Verify download integrity
Production-ready with hash verification and completeness checks
"""

import hashlib
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class UnifiedVerifier:
    """
    Unified download verifier
    Verifies integrity and completeness of downloads
    """
    
    def __init__(self):
        """Initialize verifier"""
        self._verification_cache = {}
        self._statistics = {
            'files_verified': 0,
            'segments_verified': 0,
            'hash_failures': 0,
            'completeness_failures': 0
        }
    
    def verify_file(self, file_path: str, expected_hash: str,
                   hash_type: str = 'sha256') -> bool:
        """
        Verify file integrity
        
        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            hash_type: Hash algorithm (sha256, md5, sha1)
        
        Returns:
            True if file is valid
        """
        try:
            # Calculate file hash
            if hash_type == 'sha256':
                hasher = hashlib.sha256()
            elif hash_type == 'md5':
                hasher = hashlib.md5()
            elif hash_type == 'sha1':
                hasher = hashlib.sha1()
            else:
                raise ValueError(f"Unsupported hash type: {hash_type}")
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            
            calculated_hash = hasher.hexdigest()
            
            if calculated_hash == expected_hash:
                self._statistics['files_verified'] += 1
                logger.info(f"File verified: {file_path}")
                return True
            else:
                self._statistics['hash_failures'] += 1
                logger.error(f"Hash mismatch for {file_path}: expected {expected_hash}, got {calculated_hash}")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def verify_segments(self, segments: List[Dict[str, Any]]) -> Tuple[bool, List[int]]:
        """
        Verify segment integrity
        
        Args:
            segments: List of segments with data and hashes
        
        Returns:
            Tuple of (all_valid, list_of_invalid_indices)
        """
        invalid_indices = []
        
        for i, segment in enumerate(segments):
            if 'hash' in segment and 'data' in segment:
                data = segment['data']
                if isinstance(data, str):
                    data = data.encode('utf-8')
                
                calculated_hash = hashlib.sha256(data).hexdigest()
                
                if calculated_hash != segment['hash']:
                    invalid_indices.append(i)
                    self._statistics['hash_failures'] += 1
                    logger.warning(f"Segment {i} hash mismatch")
                else:
                    self._statistics['segments_verified'] += 1
        
        return len(invalid_indices) == 0, invalid_indices
    
    def verify_completeness(self, segments: List[Dict[str, Any]],
                          expected_count: int) -> Tuple[bool, List[int]]:
        """
        Verify download completeness
        
        Args:
            segments: List of segments
            expected_count: Expected number of segments
        
        Returns:
            Tuple of (complete, list_of_missing_indices)
        """
        # Check segment count
        if len(segments) != expected_count:
            self._statistics['completeness_failures'] += 1
            logger.error(f"Segment count mismatch: got {len(segments)}, expected {expected_count}")
        
        # Check for missing indices
        segment_indices = set(s.get('segment_index', -1) for s in segments)
        expected_indices = set(range(expected_count))
        missing_indices = list(expected_indices - segment_indices)
        
        if missing_indices:
            self._statistics['completeness_failures'] += 1
            logger.error(f"Missing segments: {missing_indices}")
            return False, missing_indices
        
        return True, []
    
    def verify_merkle_tree(self, segments: List[Dict[str, Any]],
                          root_hash: str) -> bool:
        """
        Verify segments using Merkle tree
        
        Args:
            segments: List of segments with hashes
            root_hash: Expected Merkle root hash
        
        Returns:
            True if Merkle tree is valid
        """
        from ..segmentation.hashing import UnifiedHashing
        
        # Extract segment hashes
        hashes = []
        for segment in sorted(segments, key=lambda s: s.get('segment_index', 0)):
            if 'hash' in segment:
                hashes.append(segment['hash'])
            else:
                # Calculate hash if missing
                data = segment.get('data', b'')
                if isinstance(data, str):
                    data = data.encode('utf-8')
                hashes.append(hashlib.sha256(data).hexdigest())
        
        # Calculate Merkle root
        hashing = UnifiedHashing()
        calculated_root = hashing.calculate_merkle_root(hashes)
        
        if calculated_root == root_hash:
            logger.info("Merkle tree verification successful")
            return True
        else:
            logger.error(f"Merkle root mismatch: expected {root_hash}, got {calculated_root}")
            return False
    
    def verify_redundancy(self, primary_data: bytes,
                         redundant_data: List[bytes]) -> bool:
        """
        Verify redundant copies
        
        Args:
            primary_data: Primary data
            redundant_data: List of redundant copies
        
        Returns:
            True if redundancy is valid
        """
        from ..segmentation.redundancy import UnifiedRedundancy
        
        redundancy = UnifiedRedundancy()
        
        for i, data in enumerate(redundant_data):
            # Extract original data from redundant copy
            original = redundancy.extract_original_data(data)
            
            if original != primary_data:
                logger.error(f"Redundant copy {i} mismatch")
                return False
        
        logger.info(f"Verified {len(redundant_data)} redundant copies")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics"""
        total_verified = self._statistics['files_verified'] + self._statistics['segments_verified']
        total_failures = self._statistics['hash_failures'] + self._statistics['completeness_failures']
        
        return {
            **self._statistics,
            'total_verified': total_verified,
            'total_failures': total_failures,
            'success_rate': total_verified / (total_verified + total_failures) if (total_verified + total_failures) > 0 else 0
        }