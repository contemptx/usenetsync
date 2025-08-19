#!/usr/bin/env python3
"""
Unified Decoder - Decode yEnc and other encodings
Production-ready with multiple encoding support
"""

import base64
import zlib
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedDecoder:
    """
    Unified decoder for various encodings
    Handles yEnc, base64, and compressed data
    """
    
    def __init__(self):
        """Initialize decoder"""
        from ..networking.yenc import UnifiedYenc
        self.yenc = UnifiedYenc()
        self._statistics = {
            'yenc_decoded': 0,
            'base64_decoded': 0,
            'zlib_decompressed': 0,
            'bytes_decoded': 0
        }
    
    def decode_yenc(self, data: bytes) -> bytes:
        """
        Decode yEnc encoded data
        
        Args:
            data: yEnc encoded data
        
        Returns:
            Decoded binary data
        """
        decoded = self.yenc.decode(data)
        self._statistics['yenc_decoded'] += 1
        self._statistics['bytes_decoded'] += len(decoded)
        return decoded
    
    def extract_yenc_data(self, article_lines: list) -> Tuple[bytes, Dict[str, Any]]:
        """
        Extract and decode yEnc data from article
        
        Args:
            article_lines: Lines from NNTP article
        
        Returns:
            Tuple of (decoded_data, metadata)
        """
        in_yenc = False
        yenc_lines = []
        metadata = {}
        
        for line in article_lines:
            if isinstance(line, bytes):
                line = line.decode('latin-1', errors='ignore')
            
            if line.startswith('=ybegin'):
                in_yenc = True
                metadata.update(self.yenc.parse_header(line))
            elif line.startswith('=ypart'):
                # Parse part header
                parts = line.split()
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        try:
                            metadata[f"part_{key}"] = int(value)
                        except ValueError:
                            metadata[f"part_{key}"] = value
            elif line.startswith('=yend'):
                # Parse end line
                parts = line.split()
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        metadata[f"end_{key}"] = value
                break
            elif in_yenc:
                yenc_lines.append(line)
        
        if yenc_lines:
            # Join and encode lines
            encoded_data = '\n'.join(yenc_lines).encode('latin-1')
            
            # Decode yEnc
            decoded_data = self.decode_yenc(encoded_data)
            
            return decoded_data, metadata
        else:
            return b'', metadata
    
    def decode_base64(self, data: str) -> bytes:
        """
        Decode base64 encoded data
        
        Args:
            data: Base64 encoded string
        
        Returns:
            Decoded binary data
        """
        decoded = base64.b64decode(data)
        self._statistics['base64_decoded'] += 1
        self._statistics['bytes_decoded'] += len(decoded)
        return decoded
    
    def decompress_zlib(self, data: bytes) -> bytes:
        """
        Decompress zlib compressed data
        
        Args:
            data: Compressed data
        
        Returns:
            Decompressed data
        """
        decompressed = zlib.decompress(data)
        self._statistics['zlib_decompressed'] += 1
        self._statistics['bytes_decoded'] += len(decompressed)
        return decompressed
    
    def auto_decode(self, data: bytes) -> Tuple[bytes, str]:
        """
        Automatically detect and decode data
        
        Args:
            data: Encoded data
        
        Returns:
            Tuple of (decoded_data, encoding_type)
        """
        # Check for yEnc
        if data.startswith(b'=ybegin'):
            lines = data.decode('latin-1', errors='ignore').split('\n')
            decoded, _ = self.extract_yenc_data(lines)
            return decoded, 'yenc'
        
        # Check for base64
        try:
            # Try to decode as base64
            if all(c in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data[:100]):
                decoded = base64.b64decode(data)
                return decoded, 'base64'
        except:
            pass
        
        # Check for zlib compression
        if data[:2] == b'\x78\x9c':  # zlib magic number
            try:
                decompressed = zlib.decompress(data)
                return decompressed, 'zlib'
            except:
                pass
        
        # No encoding detected
        return data, 'none'
    
    def decode_multipart(self, parts: list) -> bytes:
        """
        Decode and combine multipart data
        
        Args:
            parts: List of encoded parts
        
        Returns:
            Combined decoded data
        """
        decoded_parts = []
        
        for part in parts:
            if isinstance(part, dict):
                # Part with metadata
                data = part.get('data', b'')
                encoding = part.get('encoding', 'none')
                
                if encoding == 'yenc':
                    decoded = self.decode_yenc(data)
                elif encoding == 'base64':
                    decoded = self.decode_base64(data)
                elif encoding == 'zlib':
                    decoded = self.decompress_zlib(data)
                else:
                    decoded = data
                    
                decoded_parts.append(decoded)
            else:
                # Raw data
                decoded, _ = self.auto_decode(part)
                decoded_parts.append(decoded)
        
        # Combine parts
        return b''.join(decoded_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decoder statistics"""
        return self._statistics.copy()