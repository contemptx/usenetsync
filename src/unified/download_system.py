#!/usr/bin/env python3
"""
Unified Download and Retrieval System for UsenetSync
Handles downloading, segment retrieval, and file reconstruction
"""

import os
import sys
import hashlib
import logging
import time
import json
import base64
import threading
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DownloadTask:
    """Represents a download task"""
    share_id: str
    folder_id: str
    destination_path: str
    share_type: str  # PUBLIC, PRIVATE, PROTECTED
    access_string: str
    total_files: int = 0
    completed_files: int = 0
    total_segments: int = 0
    completed_segments: int = 0
    total_size: int = 0
    downloaded_size: int = 0
    status: str = 'pending'
    error_message: Optional[str] = None

@dataclass
class SegmentRetrievalTask:
    """Task for retrieving a segment"""
    segment_id: int
    file_id: int
    segment_index: int
    message_id: str
    usenet_subject: str
    internal_subject: str
    encrypted_location: str
    retry_count: int = 0
    status: str = 'pending'

@dataclass
class FileReconstruction:
    """Information for reconstructing a file"""
    file_id: int
    file_path: str  # Relative path with folder structure
    file_hash: str
    file_size: int
    segment_count: int
    segments_retrieved: List[bytes] = field(default_factory=list)
    final_path: Optional[str] = None

# ============================================================================
# UNIFIED DOWNLOAD SYSTEM
# ============================================================================

class UnifiedDownloadSystem:
    """Unified download system with segment retrieval and file reconstruction"""
    
    def __init__(self, nntp_client, db_manager, security_system=None):
        self.nntp = nntp_client
        self.db = db_manager
        self.security = security_system
        self.active_downloads = {}
        self._lock = threading.Lock()
        
    def download_share(self, share_id: str, destination_path: str,
                       password: Optional[str] = None,
                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a complete share
        
        Args:
            share_id: Share ID to download
            destination_path: Where to save files
            password: Password for PROTECTED shares
            user_id: User ID for PRIVATE shares
            
        Returns:
            Download statistics
        """
        logger.info(f"Starting download for share {share_id}")
        
        # Get share information
        share_info = self._get_share_info(share_id)
        if not share_info:
            raise ValueError(f"Share not found: {share_id}")
            
        # Create download task
        task = DownloadTask(
            share_id=share_id,
            folder_id=share_info['folder_id'],
            destination_path=destination_path,
            share_type=share_info['share_type'],
            access_string=share_info['access_string'],
            status='downloading'
        )
        
        # Store active download
        with self._lock:
            self.active_downloads[share_id] = task
            
        try:
            # Decrypt index based on share type
            index_data = self._decrypt_index(
                share_info['encrypted_index'],
                share_info['share_type'],
                password,
                user_id,
                share_info
            )
            
            # Parse index to get file list
            files = self._parse_index(index_data)
            task.total_files = len(files)
            
            # Count total segments
            for file_info in files:
                task.total_segments += file_info['segment_count']
                task.total_size += file_info['file_size']
                
            # Download each file
            for file_info in files:
                success = self._download_file(task, file_info)
                if success:
                    task.completed_files += 1
                else:
                    logger.error(f"Failed to download: {file_info['file_path']}")
                    
            task.status = 'completed'
            
            # Calculate statistics
            stats = {
                'share_id': share_id,
                'total_files': task.total_files,
                'completed_files': task.completed_files,
                'total_segments': task.total_segments,
                'completed_segments': task.completed_segments,
                'total_size': task.total_size,
                'downloaded_size': task.downloaded_size,
                'success_rate': task.completed_files / task.total_files if task.total_files > 0 else 0
            }
            
            logger.info(f"Download complete: {task.completed_files}/{task.total_files} files")
            
            return stats
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            logger.error(f"Download failed: {e}")
            raise
            
        finally:
            # Remove from active downloads
            with self._lock:
                if share_id in self.active_downloads:
                    del self.active_downloads[share_id]
                    
    def _download_file(self, task: DownloadTask, file_info: dict) -> bool:
        """Download a single file"""
        try:
            logger.info(f"Downloading file: {file_info['file_path']}")
            
            # Create file reconstruction info
            reconstruction = FileReconstruction(
                file_id=file_info['file_id'],
                file_path=file_info['file_path'],
                file_hash=file_info['file_hash'],
                file_size=file_info['file_size'],
                segment_count=file_info['segment_count']
            )
            
            # Get segment information
            segments = self._get_file_segments(file_info['file_id'])
            
            # Download each segment
            for segment in segments:
                segment_data = self._retrieve_segment(segment)
                if segment_data:
                    reconstruction.segments_retrieved.append(segment_data)
                    task.completed_segments += 1
                    task.downloaded_size += len(segment_data)
                else:
                    # Try redundancy copies
                    segment_data = self._retrieve_redundancy(segment)
                    if segment_data:
                        reconstruction.segments_retrieved.append(segment_data)
                        task.completed_segments += 1
                        task.downloaded_size += len(segment_data)
                    else:
                        logger.error(f"Failed to retrieve segment {segment['segment_index']}")
                        return False
                        
            # Reconstruct file
            success = self._reconstruct_file(reconstruction, task.destination_path)
            
            if success:
                # Verify hash
                if self._verify_file_hash(reconstruction):
                    logger.info(f"Successfully downloaded: {file_info['file_path']}")
                    return True
                else:
                    logger.error(f"Hash verification failed: {file_info['file_path']}")
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error downloading file {file_info['file_path']}: {e}")
            return False
            
    def _retrieve_segment(self, segment: dict) -> Optional[bytes]:
        """Retrieve a segment from Usenet"""
        try:
            # Decrypt location if encrypted
            if segment.get('encrypted_location'):
                location = base64.b64decode(segment['encrypted_location']).decode()
            else:
                location = segment.get('message_id')
                
            if not location:
                # Try by subject
                return self._retrieve_by_subject(segment['usenet_subject'])
                
            # Retrieve by message ID
            success, data = self.nntp.retrieve_article(location)
            
            if success:
                # Decode if needed (yEnc, base64, etc.)
                decoded_data = self._decode_segment_data(data)
                
                # Decrypt if security system available
                if self.security:
                    decoded_data = self.security.decrypt_data(decoded_data)
                    
                return decoded_data
                
        except Exception as e:
            logger.error(f"Failed to retrieve segment: {e}")
            
        return None
        
    def _retrieve_by_subject(self, subject: str) -> Optional[bytes]:
        """Retrieve segment by subject search"""
        try:
            # Search for article by subject
            articles = self.nntp.search_by_subject(subject)
            
            if articles:
                # Get first matching article
                success, data = self.nntp.retrieve_article(articles[0])
                if success:
                    return self._decode_segment_data(data)
                    
        except Exception as e:
            logger.error(f"Failed to retrieve by subject: {e}")
            
        return None
        
    def _retrieve_redundancy(self, segment: dict) -> Optional[bytes]:
        """Try to retrieve redundancy copies"""
        # Get redundancy segments
        redundancy_segments = self.db.fetchall("""
            SELECT * FROM segments
            WHERE file_id = %s 
            AND segment_index = %s
            AND redundancy_level > 0
            ORDER BY redundancy_level
        """, (segment['file_id'], segment['segment_index']))
        
        for r_segment in redundancy_segments:
            r_data = self._retrieve_segment(dict(r_segment))
            if r_data:
                # Extract original data from redundancy copy
                return self._extract_from_redundancy(r_data)
                
        return None
        
    def _extract_from_redundancy(self, redundant_data: bytes) -> bytes:
        """Extract original data from redundancy copy"""
        # Remove redundancy metadata
        lines = redundant_data.split(b'\n')
        if lines[0].startswith(b'REDUNDANCY_COPY_'):
            return b'\n'.join(lines[1:])
        return redundant_data
        
    def _reconstruct_file(self, reconstruction: FileReconstruction,
                          destination_base: str) -> bool:
        """Reconstruct file from segments"""
        try:
            # Build full path preserving folder structure
            full_path = Path(destination_base) / reconstruction.file_path
            
            # Create directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write segments to file
            with open(full_path, 'wb') as f:
                for segment_data in reconstruction.segments_retrieved:
                    f.write(segment_data)
                    
            reconstruction.final_path = str(full_path)
            
            logger.info(f"Reconstructed file: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reconstruct file: {e}")
            return False
            
    def _verify_file_hash(self, reconstruction: FileReconstruction) -> bool:
        """Verify reconstructed file hash"""
        if not reconstruction.final_path:
            return False
            
        try:
            hasher = hashlib.sha256()
            with open(reconstruction.final_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
                    
            calculated_hash = hasher.hexdigest()
            expected_hash = reconstruction.file_hash
            
            if calculated_hash == expected_hash:
                logger.info(f"Hash verification passed: {reconstruction.file_path}")
                return True
            else:
                logger.error(f"Hash mismatch: expected {expected_hash}, got {calculated_hash}")
                return False
                
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False
            
    def _get_share_info(self, share_id: str) -> Optional[dict]:
        """Get share information from database"""
        result = self.db.fetchone("""
            SELECT * FROM shares
            WHERE share_id = %s AND active = TRUE
        """, (share_id,))
        
        if result:
            return dict(result)
        return None
        
    def _get_file_segments(self, file_id: int) -> List[dict]:
        """Get all segments for a file"""
        segments = self.db.fetchall("""
            SELECT * FROM segments
            WHERE file_id = %s AND redundancy_level = 0
            ORDER BY segment_index
        """, (file_id,))
        
        return [dict(s) for s in segments]
        
    def _decrypt_index(self, encrypted_index: str, share_type: str,
                      password: Optional[str], user_id: Optional[str],
                      share_info: dict) -> dict:
        """Decrypt index based on share type"""
        if not self.security:
            # For testing without security
            return json.loads(encrypted_index)
            
        if share_type == 'PUBLIC':
            # Public shares include key in index
            return self.security.decrypt_public_index(encrypted_index)
            
        elif share_type == 'PRIVATE':
            # Private shares need user verification
            if not user_id:
                raise ValueError("User ID required for private share")
                
            return self.security.decrypt_private_index(
                encrypted_index,
                user_id,
                share_info.get('access_commitments')
            )
            
        elif share_type == 'PROTECTED':
            # Password-protected shares
            if not password:
                raise ValueError("Password required for protected share")
                
            return self.security.decrypt_protected_index(
                encrypted_index,
                password,
                share_info.get('password_salt'),
                share_info.get('password_iterations')
            )
            
        else:
            raise ValueError(f"Unknown share type: {share_type}")
            
    def _parse_index(self, index_data: dict) -> List[dict]:
        """Parse index data to get file list"""
        files = []
        
        # Handle different index formats
        if 'files' in index_data:
            files = index_data['files']
        elif 'file_list' in index_data:
            files = index_data['file_list']
        else:
            # Try to parse as list directly
            if isinstance(index_data, list):
                files = index_data
                
        return files
        
    def _decode_segment_data(self, data: bytes) -> bytes:
        """Decode segment data (yEnc, base64, etc.)"""
        # Check for yEnc encoding
        if data.startswith(b'=ybegin'):
            return self._decode_yenc(data)
            
        # Check for base64
        try:
            # Try base64 decode
            return base64.b64decode(data)
        except:
            # Assume raw data
            return data
            
    def _decode_yenc(self, data: bytes) -> bytes:
        """Decode yEnc encoded data"""
        # Simple yEnc decoder (production would use proper library)
        lines = data.split(b'\n')
        decoded = bytearray()
        
        in_data = False
        for line in lines:
            if line.startswith(b'=ybegin'):
                in_data = True
                continue
            elif line.startswith(b'=yend'):
                break
            elif in_data:
                # Decode line
                i = 0
                while i < len(line):
                    if line[i] == ord('='):
                        i += 1
                        if i < len(line):
                            decoded.append((line[i] - 64 - 42) & 0xFF)
                    else:
                        decoded.append((line[i] - 42) & 0xFF)
                    i += 1
                    
        return bytes(decoded)

# ============================================================================
# INTELLIGENT RETRIEVAL SYSTEM
# ============================================================================

class IntelligentRetrievalSystem:
    """Advanced retrieval with fallback mechanisms"""
    
    def __init__(self, nntp_client, db_manager):
        self.nntp = nntp_client
        self.db = db_manager
        self.retrieval_cache = {}
        self.server_health = {}
        
    def retrieve_with_fallback(self, segment_info: dict) -> Optional[bytes]:
        """Retrieve segment with multiple fallback strategies"""
        strategies = [
            ('message_id', self._retrieve_by_message_id),
            ('subject', self._retrieve_by_subject_search),
            ('redundancy', self._retrieve_from_redundancy),
            ('pattern', self._retrieve_by_pattern_match),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                logger.debug(f"Trying retrieval strategy: {strategy_name}")
                data = strategy_func(segment_info)
                if data:
                    logger.info(f"Successfully retrieved via {strategy_name}")
                    return data
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                
        return None
        
    def _retrieve_by_message_id(self, segment_info: dict) -> Optional[bytes]:
        """Retrieve by message ID"""
        message_id = segment_info.get('message_id')
        if not message_id:
            return None
            
        success, data = self.nntp.retrieve_article(message_id)
        return data if success else None
        
    def _retrieve_by_subject_search(self, segment_info: dict) -> Optional[bytes]:
        """Search by subject"""
        subject = segment_info.get('usenet_subject')
        if not subject:
            return None
            
        # Search in newsgroup
        articles = self.nntp.search_by_subject(subject, limit=10)
        
        for article_id in articles:
            success, data = self.nntp.retrieve_article(article_id)
            if success:
                # Verify it's the right segment
                if self._verify_segment(data, segment_info):
                    return data
                    
        return None
        
    def _retrieve_from_redundancy(self, segment_info: dict) -> Optional[bytes]:
        """Retrieve from redundancy copies"""
        redundancy_info = self.db.fetchall("""
            SELECT * FROM segments
            WHERE file_id = %s
            AND segment_index = %s
            AND redundancy_level > 0
        """, (segment_info['file_id'], segment_info['segment_index']))
        
        for r_info in redundancy_info:
            data = self._retrieve_by_message_id(dict(r_info))
            if data:
                return self._extract_original_from_redundancy(data)
                
        return None
        
    def _retrieve_by_pattern_match(self, segment_info: dict) -> Optional[bytes]:
        """Try pattern matching as last resort"""
        # Build search pattern from segment info
        patterns = []
        
        if segment_info.get('internal_subject'):
            patterns.append(segment_info['internal_subject'][:16])
            
        if segment_info.get('segment_hash'):
            patterns.append(segment_info['segment_hash'][:8])
            
        for pattern in patterns:
            articles = self.nntp.search_by_pattern(pattern)
            for article_id in articles[:5]:  # Check first 5 matches
                success, data = self.nntp.retrieve_article(article_id)
                if success and self._verify_segment(data, segment_info):
                    return data
                    
        return None
        
    def _verify_segment(self, data: bytes, segment_info: dict) -> bool:
        """Verify retrieved data matches segment"""
        # Calculate hash of retrieved data
        data_hash = hashlib.sha256(data).hexdigest()
        
        # Check against expected hash
        return data_hash == segment_info.get('segment_hash', '')
        
    def _extract_original_from_redundancy(self, data: bytes) -> bytes:
        """Extract original data from redundancy copy"""
        # Remove redundancy headers
        if b'REDUNDANCY_COPY_' in data[:100]:
            lines = data.split(b'\n', 1)
            if len(lines) > 1:
                return lines[1]
        return data


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Unified Download System module loaded successfully")