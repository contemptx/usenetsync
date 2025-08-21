#!/usr/bin/env python3
"""
Unified Compression Module - Zlib compression for segments
"""

import zlib
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class UnifiedCompression:
    """Unified compression for segments"""
    
    def __init__(self, level: int = 9):
        """Initialize with compression level (1-9)"""
        self.level = level
    
    def compress(self, data: bytes) -> Tuple[bytes, float]:
        """
        Compress data
        Returns: (compressed_data, compression_ratio)
        """
        compressed = zlib.compress(data, self.level)
        ratio = len(compressed) / len(data) if data else 0
        
        logger.debug(f"Compressed {len(data)} bytes to {len(compressed)} (ratio: {ratio:.2f})")
        
        return compressed, ratio
    
    def decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        return zlib.decompress(data)
    
    def should_compress(self, data: bytes, threshold: float = 0.9) -> bool:
        """
        Determine if data should be compressed
        Only compress if ratio < threshold
        """
        # Quick test with lower compression
        test_compressed = zlib.compress(data[:1024], 1)
        test_ratio = len(test_compressed) / min(len(data), 1024)
        
        return test_ratio < threshold