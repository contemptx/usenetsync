#!/usr/bin/env python3
"""
Unified Hashing Module - SHA256 verification for segments
"""

import hashlib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UnifiedHashing:
    """Unified hashing for segment verification"""
    
    @staticmethod
    def calculate_hash(data: bytes) -> str:
        """Calculate SHA256 hash"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify_hash(data: bytes, expected_hash: str) -> bool:
        """Verify data hash"""
        return UnifiedHashing.calculate_hash(data) == expected_hash
    
    @staticmethod
    def calculate_file_hash(file_path: str, buffer_size: int = 65536) -> str:
        """Calculate file hash"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(buffer_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def calculate_merkle_root(hashes: List[str]) -> str:
        """Calculate Merkle tree root"""
        if not hashes:
            return ""
        
        level = hashes.copy()
        
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    combined = level[i] + level[i + 1]
                else:
                    combined = level[i] + level[i]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            level = next_level
        
        return level[0]