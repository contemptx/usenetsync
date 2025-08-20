#!/usr/bin/env python3
"""
Unified yEnc Module - yEnc encoding and decoding for binary data
"""

import struct
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UnifiedYenc:
    """yEnc encoding/decoding for Usenet binary posts"""
    
    # yEnc special characters
    ESCAPE = 0x3D  # '='
    LF = 0x0A      # Line feed
    CR = 0x0D      # Carriage return
    TAB = 0x09     # Tab
    SPACE = 0x20   # Space
    DOT = 0x2E     # '.'
    
    @staticmethod
    def encode(data: bytes, line_length: int = 128) -> bytes:
        """
        Encode binary data to yEnc format
        
        Args:
            data: Binary data to encode
            line_length: Maximum line length
        
        Returns:
            yEnc encoded data
        """
        encoded = bytearray()
        column = 0
        
        for byte in data:
            # yEnc encoding: add 42 and wrap at 256
            encoded_byte = (byte + 42) & 0xFF
            
            # Check if escaping needed
            needs_escape = (
                encoded_byte == UnifiedYenc.ESCAPE or
                encoded_byte == UnifiedYenc.LF or
                encoded_byte == UnifiedYenc.CR or
                encoded_byte == UnifiedYenc.TAB or
                (column == 0 and encoded_byte == UnifiedYenc.DOT) or
                (column == 0 and encoded_byte == UnifiedYenc.SPACE)
            )
            
            if needs_escape:
                encoded.append(UnifiedYenc.ESCAPE)
                encoded.append((encoded_byte + 64) & 0xFF)
                column += 2
            else:
                encoded.append(encoded_byte)
                column += 1
            
            # Line wrapping
            if column >= line_length:
                encoded.extend(b'\r\n')
                column = 0
        
        return bytes(encoded)
    
    @staticmethod
    def decode(data: bytes) -> bytes:
        """
        Decode yEnc data to binary
        
        Args:
            data: yEnc encoded data
        
        Returns:
            Decoded binary data
        """
        decoded = bytearray()
        i = 0
        
        while i < len(data):
            byte = data[i]
            
            # Skip line endings
            if byte in (UnifiedYenc.LF, UnifiedYenc.CR):
                i += 1
                continue
            
            # Handle escape sequences
            if byte == UnifiedYenc.ESCAPE:
                i += 1
                if i < len(data):
                    byte = (data[i] - 64) & 0xFF
            
            # yEnc decoding: subtract 42 and wrap at 256
            decoded_byte = (byte - 42) & 0xFF
            decoded.append(decoded_byte)
            i += 1
        
        return bytes(decoded)
    
    @staticmethod
    def create_header(filename: str, size: int, part: int = 1, 
                     total: int = 1, line_length: int = 128) -> str:
        """
        Create yEnc header
        
        Args:
            filename: File name
            size: File size in bytes
            part: Part number
            total: Total parts
            line_length: Line length
        
        Returns:
            yEnc header string
        """
        if total > 1:
            header = f"=ybegin part={part} total={total} line={line_length} size={size} name={filename}"
        else:
            header = f"=ybegin line={line_length} size={size} name={filename}"
        
        return header
    
    @staticmethod
    def create_part_header(begin: int, end: int) -> str:
        """
        Create yEnc part header
        
        Args:
            begin: Begin offset
            end: End offset
        
        Returns:
            Part header string
        """
        return f"=ypart begin={begin} end={end}"
    
    @staticmethod
    def create_footer(part: int, size: int, crc32: Optional[int] = None) -> str:
        """
        Create yEnc footer
        
        Args:
            part: Part number
            size: Part size
            crc32: Optional CRC32 checksum
        
        Returns:
            yEnc footer string
        """
        footer = f"=yend size={size} part={part}"
        
        if crc32 is not None:
            footer += f" pcrc32={crc32:08x}"
        
        return footer
    
    @staticmethod
    def wrap_data(data: bytes, filename: str, part: int = 1,
                 total: int = 1, begin: int = 1) -> bytes:
        """
        Wrap binary data with yEnc headers and encoding
        
        Args:
            data: Binary data
            filename: File name
            part: Part number
            total: Total parts
            begin: Begin offset
        
        Returns:
            Complete yEnc message
        """
        # Encode data
        encoded = UnifiedYenc.encode(data)
        
        # Create headers and footers
        header = UnifiedYenc.create_header(filename, len(data), part, total)
        
        if total > 1:
            part_header = UnifiedYenc.create_part_header(begin, begin + len(data) - 1)
            header = f"{header}\r\n{part_header}"
        
        footer = UnifiedYenc.create_footer(part, len(data))
        
        # Combine
        message = f"{header}\r\n".encode('utf-8')
        message += encoded
        message += f"\r\n{footer}\r\n".encode('utf-8')
        
        return message
    
    @staticmethod
    def parse_header(header_line: str) -> Dict[str, Any]:
        """
        Parse yEnc header line
        
        Args:
            header_line: Header line to parse
        
        Returns:
            Parsed header information
        """
        info = {}
        
        if not header_line.startswith('=ybegin'):
            return info
        
        # Parse key=value pairs
        parts = header_line.split()
        for part in parts[1:]:  # Skip =ybegin
            if '=' in part:
                key, value = part.split('=', 1)
                
                # Convert numeric values
                if key in ['part', 'total', 'line', 'size', 'begin', 'end']:
                    try:
                        info[key] = int(value)
                    except ValueError:
                        info[key] = value
                else:
                    info[key] = value
        
        return info