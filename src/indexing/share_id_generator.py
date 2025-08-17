#!/usr/bin/env python3
"""
Share ID Generator and Access String Management for UsenetSync
Handles creation and validation of share identifiers
"""

import os
import time
import json
import base64
import hashlib
import secrets
import struct
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ShareFormat(Enum):
    """Share access string formats"""
    STANDARD = "standard"      # Base64 JSON
    COMPACT = "compact"        # Binary format
    LEGACY = "legacy"          # Backward compatible

@dataclass
class ShareMetadata:
    """Metadata embedded in share"""
    created_timestamp: int
    client_version: str
    compression: bool
    encryption: bool
    checksum: str

class ShareIDGenerator:
    """
    Generates unique share IDs with embedded metadata
    Format: TYPE_HASH_CHECKSUM
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ShareIDGenerator")
        
    def generate_share_id(self, folder_id: str, share_type: str,
                         version: int = 1) -> str:
        """
        Generate unique share ID
        Format: TYPE_XXXXXXXX_YYYY
        """
        # Type prefix
        type_prefix = share_type[0].upper()  # P, R, O (Public, pRivate, prOtected)
        
        # Generate unique component
        unique_data = f"{folder_id}:{share_type}:{version}:{time.time()}:{secrets.token_hex(8)}"
        unique_hash = hashlib.sha256(unique_data.encode()).hexdigest()
        
        # Take first 16 chars of hash
        main_id = unique_hash[:16].upper()
        
        # Generate checksum (last 4 chars)
        checksum_data = f"{type_prefix}{main_id}"
        checksum = hashlib.sha256(checksum_data.encode()).hexdigest()[:4].upper()
        
        share_id = f"{type_prefix}{main_id}_{checksum}"
        
        self.logger.debug(f"Generated share ID: {share_id}")
        return share_id
        
    def validate_share_id(self, share_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate share ID format and checksum
        Returns: (is_valid, share_type)
        """
        try:
            # Check format
            if len(share_id) != 22:  # P + 16 chars + _ + 4 chars
                return False, None
                
            if share_id[17] != '_':
                return False, None
                
            # Extract components
            type_prefix = share_id[0]
            main_id = share_id[1:17]
            provided_checksum = share_id[18:22]
            
            # Validate type
            type_map = {'P': 'public', 'R': 'private', 'O': 'protected'}
            if type_prefix not in type_map:
                return False, None
                
            # Verify checksum
            checksum_data = f"{type_prefix}{main_id}"
            expected_checksum = hashlib.sha256(checksum_data.encode()).hexdigest()[:4].upper()
            
            if provided_checksum != expected_checksum:
                return False, None
                
            return True, type_map[type_prefix]
            
        except Exception as e:
            self.logger.error(f"Error validating share ID: {e}")
            return False, None
            
    def extract_metadata(self, share_id: str) -> Dict[str, Any]:
        """Extract metadata from share ID"""
        is_valid, share_type = self.validate_share_id(share_id)
        
        if not is_valid:
            return {}
            
        return {
            'share_type': share_type,
            'id_component': share_id[1:17],
            'checksum': share_id[18:22]
        }

class AccessStringManager:
    """
    Manages access string creation and parsing
    Supports multiple formats for different use cases
    """
    
    def __init__(self, security_system):
        self.security = security_system
        self.logger = logging.getLogger(f"{__name__}.AccessStringManager")
        self.share_id_gen = ShareIDGenerator()
        
    def create_access_string(self, share_data: Dict[str, Any],
                           format: ShareFormat = ShareFormat.STANDARD) -> str:
        """Create access string in specified format"""
        if format == ShareFormat.STANDARD:
            return self._create_standard_access_string(share_data)
        elif format == ShareFormat.COMPACT:
            return self._create_compact_access_string(share_data)
        elif format == ShareFormat.LEGACY:
            return self._create_legacy_access_string(share_data)
        else:
            raise ValueError(f"Unknown format: {format}")
            
    def _create_standard_access_string(self, share_data: Dict[str, Any]) -> str:
        """
        Create standard JSON-based access string
        Most flexible and extensible format
        """
        # Build access data
        access_data = {
            'v': '3.0',  # Version
            'id': share_data['share_id'],
            'type': share_data['share_type'],
            'folder': share_data['folder_id'][:32],  # Truncate for privacy
            'ver': share_data.get('version', 1),
            'ts': int(time.time()),
            'client': 'UsenetSync/1.0'
        }
        
        # Add index reference
        index_ref = share_data.get('index_reference', {})
        if index_ref.get('type') == 'single':
            access_data['idx'] = {
                't': 's',  # single
                'm': index_ref['message_id'],
                'n': index_ref['newsgroup']
            }
        elif index_ref.get('type') == 'multi':
            access_data['idx'] = {
                't': 'm',  # multi
                'c': index_ref['total'],
                's': [  # segments
                    {
                        'i': seg['index'],
                        'm': seg['message_id'],
                        'n': seg['newsgroup']
                    }
                    for seg in index_ref['segments']
                ]
            }
            
        # Add optional fields
        if share_data.get('password_hint'):
            access_data['hint'] = share_data['password_hint']
            
        if share_data.get('expires'):
            access_data['exp'] = share_data['expires']
            
        # Create checksum
        checksum = hashlib.sha256(
            json.dumps(access_data, sort_keys=True).encode()
        ).hexdigest()[:8]
        access_data['chk'] = checksum
        
        # Encode
        json_str = json.dumps(access_data, separators=(',', ':'))
        base64_str = base64.urlsafe_b64encode(json_str.encode()).decode()
        
        # Remove padding for cleaner URLs
        return base64_str.rstrip('=')
        
    def _create_compact_access_string(self, share_data: Dict[str, Any]) -> str:
        """
        Create compact binary access string
        More efficient for size-constrained scenarios
        """
        buffer = bytearray()
        
        # Version (1 byte)
        buffer.append(3)  # Version 3
        
        # Share type (1 byte)
        type_map = {'public': 0, 'private': 1, 'protected': 2}
        buffer.append(type_map.get(share_data['share_type'], 0))
        
        # Share ID (16 bytes - main component only)
        share_id = share_data['share_id']
        id_component = share_id[1:17]
        buffer.extend(bytes.fromhex(id_component))
        
        # Folder ID hash (8 bytes)
        folder_hash = hashlib.sha256(share_data['folder_id'].encode()).digest()[:8]
        buffer.extend(folder_hash)
        
        # Version (2 bytes)
        buffer.extend(struct.pack('>H', share_data.get('version', 1)))
        
        # Timestamp (4 bytes)
        buffer.extend(struct.pack('>I', int(time.time())))
        
        # Index reference type (1 byte)
        index_ref = share_data.get('index_reference', {})
        if index_ref.get('type') == 'single':
            buffer.append(1)
            # Message ID hash (16 bytes)
            msg_hash = hashlib.sha256(index_ref['message_id'].encode()).digest()[:16]
            buffer.extend(msg_hash)
        else:
            buffer.append(2)
            # Segment count (1 byte)
            buffer.append(min(255, index_ref.get('total', 1)))
            # First segment hash (16 bytes)
            if index_ref.get('segments'):
                first_msg = index_ref['segments'][0]['message_id']
                msg_hash = hashlib.sha256(first_msg.encode()).digest()[:16]
                buffer.extend(msg_hash)
            else:
                buffer.extend(b'\x00' * 16)
                
        # Checksum (4 bytes)
        checksum = hashlib.sha256(bytes(buffer)).digest()[:4]
        buffer.extend(checksum)
        
        # Encode
        return base64.urlsafe_b64encode(bytes(buffer)).decode().rstrip('=')
        
    def _create_legacy_access_string(self, share_data: Dict[str, Any]) -> str:
        """Create legacy format for backward compatibility"""
        # Simple format: share_id:message_id:newsgroup
        index_ref = share_data.get('index_reference', {})
        
        if index_ref.get('type') == 'single':
            parts = [
                share_data['share_id'],
                index_ref['message_id'],
                index_ref['newsgroup']
            ]
        else:
            # Use first segment for legacy
            first_seg = index_ref.get('segments', [{}])[0]
            parts = [
                share_data['share_id'],
                first_seg.get('message_id', ''),
                first_seg.get('newsgroup', 'alt.binaries.usenet-sync')
            ]
            
        legacy_str = ':'.join(parts)
        return base64.urlsafe_b64encode(legacy_str.encode()).decode().rstrip('=')
        
    def parse_access_string(self, access_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse any format access string
        Auto-detects format
        """
        try:
            # Add padding if needed
            padding = 4 - (len(access_string) % 4)
            if padding != 4:
                access_string += '=' * padding
                
            # Decode
            decoded = base64.urlsafe_b64decode(access_string)
            
            # Try to detect format
            if decoded[0:1] == b'{' or (len(decoded) > 10 and b'"v"' in decoded[:20]):
                # JSON format
                return self._parse_standard_format(decoded)
            elif len(decoded) in [52, 53, 54]:  # Compact format sizes
                # Binary format
                return self._parse_compact_format(decoded)
            else:
                # Try legacy
                return self._parse_legacy_format(decoded)
                
        except Exception as e:
            self.logger.error(f"Failed to parse access string: {e}")
            return None
            
    def _parse_standard_format(self, data: bytes) -> Dict[str, Any]:
        """Parse standard JSON format"""
        try:
            access_data = json.loads(data.decode('utf-8'))
            
            # Verify checksum
            provided_checksum = access_data.pop('chk', None)
            expected_checksum = hashlib.sha256(
                json.dumps(access_data, sort_keys=True).encode()
            ).hexdigest()[:8]
            
            if provided_checksum != expected_checksum:
                self.logger.warning("Access string checksum mismatch")
                
            # Convert to standard format
            result = {
                'version': access_data.get('v', '1.0'),
                'share_id': access_data.get('id'),
                'share_type': access_data.get('type'),
                'folder_id': access_data.get('folder'),
                'folder_version': access_data.get('ver', 1),
                'created': access_data.get('ts'),
                'client': access_data.get('client')
            }
            
            # Parse index reference
            idx = access_data.get('idx', {})
            if idx.get('t') == 's':
                result['index_reference'] = {
                    'type': 'single',
                    'message_id': idx.get('m'),
                    'newsgroup': idx.get('n')
                }
            elif idx.get('t') == 'm':
                result['index_reference'] = {
                    'type': 'multi',
                    'total': idx.get('c'),
                    'segments': [
                        {
                            'index': s.get('i'),
                            'message_id': s.get('m'),
                            'newsgroup': s.get('n')
                        }
                        for s in idx.get('s', [])
                    ]
                }
                
            # Optional fields
            if 'hint' in access_data:
                result['password_hint'] = access_data['hint']
            if 'exp' in access_data:
                result['expires'] = access_data['exp']
                
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse standard format: {e}")
            return None
            
    def _parse_compact_format(self, data: bytes) -> Dict[str, Any]:
        """Parse compact binary format"""
        try:
            buffer = bytearray(data)
            offset = 0
            
            # Version
            version = buffer[offset]
            offset += 1
            
            # Share type
            type_map = {0: 'public', 1: 'private', 2: 'protected'}
            share_type = type_map.get(buffer[offset], 'public')
            offset += 1
            
            # Share ID component
            id_component = buffer[offset:offset+16].hex().upper()
            offset += 16
            
            # Reconstruct full share ID
            type_prefix = share_type[0].upper()
            checksum = hashlib.sha256(f"{type_prefix}{id_component}".encode()).hexdigest()[:4].upper()
            share_id = f"{type_prefix}{id_component}_{checksum}"
            
            # Folder ID hash
            folder_hash = buffer[offset:offset+8]
            offset += 8
            
            # Version
            folder_version = struct.unpack('>H', buffer[offset:offset+2])[0]
            offset += 2
            
            # Timestamp
            timestamp = struct.unpack('>I', buffer[offset:offset+4])[0]
            offset += 4
            
            # Index reference type
            ref_type = buffer[offset]
            offset += 1
            
            # Parse index reference
            if ref_type == 1:
                # Single
                msg_hash = buffer[offset:offset+16]
                index_ref = {
                    'type': 'single',
                    'message_id_hash': msg_hash.hex()
                }
            else:
                # Multi
                seg_count = buffer[offset]
                offset += 1
                first_hash = buffer[offset:offset+16]
                index_ref = {
                    'type': 'multi',
                    'total': seg_count,
                    'first_segment_hash': first_hash.hex()
                }
                
            # Verify checksum
            provided_checksum = buffer[-4:]
            expected_checksum = hashlib.sha256(bytes(buffer[:-4])).digest()[:4]
            
            if provided_checksum != expected_checksum:
                self.logger.warning("Compact format checksum mismatch")
                
            return {
                'version': f"{version}.0",
                'share_id': share_id,
                'share_type': share_type,
                'folder_hash': folder_hash.hex(),
                'folder_version': folder_version,
                'created': timestamp,
                'index_reference': index_ref
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse compact format: {e}")
            return None
            
    def _parse_legacy_format(self, data: bytes) -> Dict[str, Any]:
        """Parse legacy format"""
        try:
            parts = data.decode('utf-8').split(':')
            
            if len(parts) != 3:
                return None
                
            return {
                'version': '1.0',
                'share_id': parts[0],
                'share_type': 'unknown',  # Can't determine from legacy
                'index_reference': {
                    'type': 'single',
                    'message_id': parts[1],
                    'newsgroup': parts[2]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse legacy format: {e}")
            return None
            
    def create_qr_friendly_string(self, access_string: str) -> str:
        """
        Create QR code friendly version of access string
        Shorter and uses alphanumeric mode
        """
        # Use compact format for QR codes
        # Could also use URL shortener integration
        
        # For now, just ensure uppercase for better QR efficiency
        return access_string.upper().replace('_', '-')
        
    def validate_access_string(self, access_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate access string
        Returns: (is_valid, error_message)
        """
        parsed = self.parse_access_string(access_string)
        
        if not parsed:
            return False, "Invalid format"
            
        # Check required fields
        required = ['share_id', 'index_reference']
        for field in required:
            if field not in parsed:
                return False, f"Missing {field}"
                
        # Validate share ID
        if 'share_id' in parsed:
            is_valid, _ = self.share_id_gen.validate_share_id(parsed['share_id'])
            if not is_valid:
                return False, "Invalid share ID"
                
        # Check expiration if present
        if 'expires' in parsed:
            if parsed['expires'] < time.time():
                return False, "Access string has expired"
                
        return True, None