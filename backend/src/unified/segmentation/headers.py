#!/usr/bin/env python3
"""
Unified Headers Module - Segment header creation
"""

import struct
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedHeaders:
    """Unified segment header management"""
    
    MAGIC = b'USEG'  # UsenetSync Segment
    VERSION = 1
    
    @staticmethod
    def create_header(segment_index: int, total_segments: int,
                     file_id: str, file_size: int,
                     metadata: Optional[Dict[str, Any]] = None) -> bytes:
        """Create segment header"""
        header_data = {
            'version': UnifiedHeaders.VERSION,
            'segment_index': segment_index,
            'total_segments': total_segments,
            'file_id': file_id,
            'file_size': file_size,
            'metadata': metadata or {}
        }
        
        # Serialize to JSON
        header_json = json.dumps(header_data).encode('utf-8')
        
        # Create binary header
        header = struct.pack(
            '<4sHI',
            UnifiedHeaders.MAGIC,
            UnifiedHeaders.VERSION,
            len(header_json)
        ) + header_json
        
        return header
    
    @staticmethod
    def parse_header(data: bytes) -> Dict[str, Any]:
        """Parse segment header"""
        # Check magic
        magic = data[:4]
        if magic != UnifiedHeaders.MAGIC:
            raise ValueError("Invalid segment header")
        
        # Parse header
        version, json_size = struct.unpack('<HI', data[4:10])
        
        # Parse JSON data
        header_json = data[10:10+json_size]
        header_data = json.loads(header_json.decode('utf-8'))
        
        return header_data
    
    @staticmethod
    def add_yenc_header(data: bytes, filename: str, part: int, 
                       total: int, size: int) -> bytes:
        """Add yEnc header to data"""
        header = f"=ybegin part={part} total={total} line=128 size={size} name={filename}\r\n"
        footer = f"\r\n=yend size={len(data)} part={part}\r\n"
        
        return header.encode('utf-8') + data + footer.encode('utf-8')