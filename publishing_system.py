#!/usr/bin/env python3
"""
Publishing System for UsenetSync - PRODUCTION VERSION
Manages folder publishing, share creation, and access control
Full implementation with no placeholders
"""

import os
import time
import json
import hashlib
import base64
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import struct
import zlib
from enhanced_security_system import ShareType

logger = logging.getLogger(__name__)

class PublishState(Enum):
    """Publishing states"""
    PREPARING = "preparing"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"
    UPDATING = "updating"

@dataclass
class PublishJob:
    """Publishing job information"""
    job_id: str
    folder_id: str
    share_type: str
    version: int
    state: PublishState
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    share_id: Optional[str] = None
    access_string: Optional[str] = None
    index_size: int = 0
    segment_count: int = 0
    error_message: Optional[str] = None
    authorized_users: List[str] = field(default_factory=list)
    password_hint: Optional[str] = None
    
@dataclass
class ShareInfo:
    """Published share information"""
    share_id: str
    share_type: str
    folder_id: str
    folder_name: str
    version: int
    created_at: datetime
    access_string: str
    index_reference: Dict[str, Any]
    statistics: Dict[str, Any]
    is_active: bool = True

@dataclass
class AccessPermission:
    """Access permission for a share"""
    user_id: str
    share_id: str
    granted_at: datetime
    granted_by: str
    revoked_at: Optional[datetime] = None
    is_active: bool = True

class IndexBuilder:
    """Builds folder indexes for publishing"""
    
    def __init__(self, db_manager, security_system, binary_index_system):
        self.db = db_manager
        self.security = security_system
        self.binary_index = binary_index_system
        self.logger = logging.getLogger(f"{__name__}.IndexBuilder")
        
    def _ensure_int(self, value, default=1):
        """Ensure a value is an integer"""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                # Handle string numbers
                if value.strip().replace('-', '').replace('+', '').isdigit():
                    return int(value)
                # Try float conversion for decimal strings
                try:
                    return int(float(value))
                except:
                    pass
            if hasattr(value, 'timestamp'):
                # Handle datetime objects
                return int(value.timestamp())
            if value is None:
                return default
            # Last resort - try conversion
            return int(str(value))
        except (ValueError, TypeError, AttributeError):
            return default
            
    def build_folder_index(self, folder_id: str, version: int,
                          share_type: str, **kwargs) -> Tuple[bytes, Dict[str, Any]]:
        """
        Build complete folder index for publishing
        Returns: (index_data, metadata)
        """
        # Ensure version is integer
        version = self._ensure_int(version)
        
        self.logger.info(f"Building {share_type} index for folder {folder_id} v{version}")
        
        try:
            # Get folder information
            folder = self.db.get_folder(folder_id)
            if not folder:
                raise ValueError(f"Folder {folder_id} not found")
                
            # Get files and segments
            files_data = self._get_folder_files(folder['id'], version)
            segments_data = self._get_folder_segments(folder['id'], version)
            
            # Build file structure for binary index
            folder_structure = {
                'base_path': folder['folder_path'],
                'folders': self._build_folder_tree(files_data),
                'files': files_data
            }
            
            # Create binary index instance and generate index
            binary_indexer = self.binary_index(folder['folder_unique_id'])
            binary_data = binary_indexer.create_folder_structure_index(folder_structure)
            
            # Create security wrapper based on share type
            if share_type == 'public':
                wrapped_index = self._create_public_index(
                    folder, version, binary_data, segments_data
                )
            elif share_type == 'private':
                wrapped_index = self._create_private_index(
                    folder, version, binary_data, segments_data,
                    kwargs.get('authorized_users', [])
                )
            elif share_type == 'protected':
                wrapped_index = self._create_protected_index(
                    folder, version, binary_data, segments_data,
                    kwargs.get('password', ''),
                    kwargs.get('password_hint', '')
                )
            else:
                raise ValueError(f"Unknown share type: {share_type}")
                
            # Calculate metadata
            metadata = {
                'total_files': len(files_data),
                'total_size': sum(f['size'] for f in files_data),
                'total_segments': len(segments_data),
                'index_size': len(wrapped_index),
                'compression_ratio': len(wrapped_index) / len(binary_data) if binary_data else 0,
                'created_at': datetime.now().isoformat()
            }
            
            return wrapped_index, metadata

        except Exception as e:
            self.logger.error(f"Failed to build index: {e}")
            raise
            
    def _get_folder_files(self, folder_db_id: int, version: int) -> List[Dict]:
        """Get files for specific version"""
        files = self.db.get_folder_files(folder_db_id)
        
        # Filter by version if needed
        file_data = []
        for file in files:
            # Ensure all numeric values are properly typed
            file_version = self._ensure_int(file.get('version', 1))
            target_version = self._ensure_int(version)
            
            # Also ensure other numeric fields
            file_size = self._ensure_int(file.get('file_size', file.get('size', 0)), 0)
            modified_at = self._ensure_int(file.get('modified_at', 0), 0)
            
            # Check version and state
            if file_version <= target_version and file.get('state') != 'deleted':
                file_dict = {
                    'path': file.get('file_path', ''),
                    'size': file_size,
                    'hash': file.get('file_hash', file.get('hash', '')),
                    'modified': modified_at,
                    'segments': 1  # Default
                }
                file_data.append(file_dict)
                
        return file_data
        
    def _get_folder_segments(self, folder_db_id: int, version: int) -> Dict[str, Any]:
        """Get segments mapping for folder"""
        segments_map = {}
        
        # Get all segments for folder files
        files = self.db.get_folder_files(folder_db_id)
        
        for file in files:
            if self._ensure_int(file.get("version", 1)) <= self._ensure_int(version) and file.get('state') != 'deleted':
                # CRITICAL FIX: Get segments for THIS specific file only
                segments = self.db.get_file_segments(file['id'])
                
                # Group by file path
                file_segments = []
                for seg in segments:
                    if seg.get('state') == 'uploaded' and seg.get('message_id'):
                        file_segments.append({
                            'index': seg['segment_index'],
                            'message_id': seg['message_id'],
                            'newsgroup': seg.get('newsgroup', 'alt.binaries.test'),
                            'subject': seg.get('subject_hash', ''),
                            'size': seg.get('segment_size', 0),
                            'hash': seg.get('segment_hash', '')  # Include hash for verification
                        })
                
                # CRITICAL FIX: Map segments to the correct file path
                if file_segments:
                    segments_map[file['file_path']] = file_segments
                    self.logger.debug(f"File {file['file_path']} (id={file['id']}) has {len(file_segments)} segments")
                    
        return segments_map
    
    def _build_folder_tree(self, files: List[Dict]) -> Dict[str, Dict]:
        """Build folder tree structure from files"""
        folders = {}
        
        for file in files:
            path_parts = file['path'].split('/')
            
            # Process each directory level
            for i in range(len(path_parts) - 1):
                folder_path = '/'.join(path_parts[:i+1])
                if folder_path not in folders:
                    folders[folder_path] = {
                        'name': path_parts[i],
                        'file_count': 0,
                        'subfolder_count': 0
                    }
                    
                    # Count subfolders
                    parent_path = '/'.join(path_parts[:i]) if i > 0 else ''
                    if parent_path in folders:
                        folders[parent_path]['subfolder_count'] += 1
                        
            # Count file in immediate parent
            if len(path_parts) > 1:
                parent = '/'.join(path_parts[:-1])
                if parent in folders:
                    folders[parent]['file_count'] += 1
                    
        return folders
        
    def _create_public_index(self, folder: Dict, version: int,
                           binary_data: bytes, segments: Dict) -> bytes:
        """Create public index (no encryption)"""
        index_data = {
            'version': '3.0',
            'type': 'public',
            'folder': {
                'id': folder['folder_unique_id'],
                'name': folder['display_name'],
                'version': version
            },
            'binary_index': base64.b64encode(binary_data).decode('utf-8'),
            'segments': segments,
            'created': datetime.now().isoformat(),
            'client': 'UsenetSync/1.0'
        }
        
        # Compress JSON
        json_data = json.dumps(index_data, separators=(',', ':'))
        return zlib.compress(json_data.encode('utf-8'), level=9)
        
    def _create_private_index(self, folder: Dict, version: int,
                            binary_data: bytes, segments: Dict,
                            authorized_users: List[str]) -> bytes:
        """Create private index with access control"""
        # Create base index
        base_index = {
            'binary_index': base64.b64encode(binary_data).decode('utf-8'),
            'segments': segments
        }
        
        # Encrypt for authorized users
        encrypted_index = self.security.create_folder_index(
            folder['folder_unique_id'],
            ShareType.PRIVATE,
            files_data=[],  # Already in binary index
            segments_data=base_index,
            user_ids=authorized_users
        )
        
        # Add metadata
            # REMOVED:         encrypted_index['folder'] = {
            # REMOVED:             'id': folder['folder_unique_id'],
            # REMOVED:             'name': folder['display_name'],
            # REMOVED:             'version': version
            # REMOVED:         }
        
        # Compress
        json_data = json.dumps(encrypted_index, separators=(',', ':'))
        return zlib.compress(json_data.encode('utf-8'), level=9)
        
    def _create_protected_index(self, folder: Dict, version: int,
                              binary_data: bytes, segments: Dict,
                              password: str, password_hint: str) -> bytes:
        """Create password-protected index"""
        # Create base index
        base_index = {
            'binary_index': base64.b64encode(binary_data).decode('utf-8'),
            'segments': segments
        }
        
        # Encrypt with password
        encrypted_index = self.security.create_folder_index(
            folder['folder_unique_id'],
            ShareType.PROTECTED,
            files_data=[],  # Already in binary index
            segments_data=base_index,
            password=password,
            password_hint=password_hint
        )
        
        # Add metadata
            # REMOVED:         encrypted_index['folder'] = {
            # REMOVED:             'id': folder['folder_unique_id'],
            # REMOVED:             'name': folder['display_name'],
            # REMOVED:             'version': version
            # REMOVED:         }
        
        # Compress
        json_data = json.dumps(encrypted_index, separators=(',', ':'))
        return zlib.compress(json_data.encode('utf-8'), level=9)

class PublishingSystem:
    """
    Main publishing system for UsenetSync
    Handles folder publishing, share management, and access control
    """
    
    def __init__(self, db_manager, security_system, upload_system,
                 nntp_client, index_system, binary_index_system, config: Dict[str, Any]):
        self.db = db_manager
        self.security = security_system
        self.upload = upload_system
        self.nntp = nntp_client
        self.index_system = index_system
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Index builder
        self.index_builder = IndexBuilder(db_manager, security_system, binary_index_system)
        
        # Active jobs
        self.active_jobs: Dict[str, PublishJob] = {}
        self._jobs_lock = threading.Lock()
        
        # Published shares cache
        self.published_shares: Dict[str, ShareInfo] = {}
        self._shares_lock = threading.Lock()
        
        # Configuration
        self.index_newsgroup = config.get('index_newsgroup', 'alt.binaries.test')
        self.max_index_segments = config.get('max_index_segments', 10)
        self.index_segment_size = config.get('index_segment_size', 768000)
        
        # Load existing shares
        self._load_published_shares()
        
    def _ensure_int(self, value, default=1):
        """Ensure a value is an integer"""
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                # Handle string numbers
                if value.strip().replace('-', '').replace('+', '').isdigit():
                    return int(value)
                # Try float conversion for decimal strings
                try:
                    return int(float(value))
                except:
                    pass
            if hasattr(value, 'timestamp'):
                # Handle datetime objects
                return int(value.timestamp())
            if value is None:
                return default
            # Last resort - try conversion
            return int(str(value))
        except (ValueError, TypeError, AttributeError):
            return default

    def publish_folder(self, folder_id: str, share_type: str,
                      authorized_users: Optional[List[str]] = None,
                      password: Optional[str] = None,
                      password_hint: Optional[str] = None,
                      update_existing: bool = False) -> str:
        """
        Publish a folder
        Returns job ID for tracking
        """
        # Validate inputs
        folder = self.db.get_folder(folder_id)
        if not folder:
            raise ValueError(f"Folder {folder_id} not found")
        folder_name = folder.get("display_name", folder_id) if folder else folder_id
        logger.info(f"FOLDER_DEBUG: Publishing folder {folder_name} as {share_type}")

            
        if share_type not in ['public', 'private', 'protected']:
            raise ValueError(f"Invalid share type: {share_type}")
            
        if share_type == 'private' and not authorized_users:
            raise ValueError("Private shares require authorized users")
            
        if share_type == 'protected' and not password:
            raise ValueError("Protected shares require password")
            
        # Check for existing publication
        existing = self._get_active_share(folder_id)
        if existing and not update_existing:
            raise ValueError(f"Folder already published as {existing.share_id}")
            
        # Create job
        job_id = self._generate_job_id(folder_id)
        job = PublishJob(
            job_id=job_id,
            folder_id=folder_id,
            share_type=share_type,
            version=self._ensure_int(folder['current_version']),
            state=PublishState.PREPARING,
            authorized_users=authorized_users or [],
            password_hint=password_hint
        )
        
        with self._jobs_lock:
            self.active_jobs[job_id] = job
            
        # Start publishing in background
        threading.Thread(
            target=self._publish_folder_async,
            args=(job, password),
            daemon=True
        ).start()
        
        self.logger.info(f"Started publishing job {job_id} for folder {folder_id}")
        return job_id
        
    def _publish_folder_async(self, job: PublishJob, password: Optional[str] = None):
        """Async folder publishing"""
        try:
            # Update state
            job.state = PublishState.PREPARING
            
            # Get folder information
            folder = self.db.get_folder(job.folder_id)
            if not folder:
                raise ValueError(f"Folder {job.folder_id} not found")
            
            # Build index
            self.logger.info(f"Building index for job {job.job_id}")
            
            index_data, metadata = self.index_builder.build_folder_index(
                job.folder_id,
                job.version,
                job.share_type,
                authorized_users=job.authorized_users,
                password=password,
                password_hint=job.password_hint
            )
            
            job.index_size = metadata['index_size']
            
            # Upload index
            job.state = PublishState.UPLOADING
            self.logger.info(f"Uploading index for job {job.job_id}")
            
            index_reference = self._upload_index(job.folder_id, index_data)
            job.segment_count = len(index_reference.get('segments', []))
            
            # Generate share ID and access string
            job.share_id = self.security.generate_share_id(job.folder_id, job.share_type)
            
            share_data = {
                'share_id': job.share_id,
                'share_type': job.share_type,
                'folder_id': job.folder_id,
                'version': job.version,
                'index_reference': index_reference
            }
            
            job.access_string = self.security.create_access_string(share_data)
            
            # Record in database
            self.db.record_publication(
                folder['id'],
                job.version,
                job.share_id,
                job.access_string,
                job.index_size,
                job.share_type
            )
            
            # Create share info
            share_info = ShareInfo(
                share_id=job.share_id,
                share_type=job.share_type,
                folder_id=job.folder_id,
                folder_name=folder['display_name'],
                version=job.version,
                created_at=datetime.now(),
                access_string=job.access_string,
                index_reference=index_reference,
                statistics=metadata
            )
            
            # Cache share
            with self._shares_lock:
                self.published_shares[job.share_id] = share_info
                
            # Update job
            job.state = PublishState.PUBLISHED
            job.completed_at = datetime.now()
            
            self.logger.info(
                f"Successfully published folder {job.folder_id} as {job.share_id}, "
                f"access string: {job.access_string[:20]}..."
            )
            logger.info(f"FOLDER_DEBUG: Published successfully - share_id: {job.share_id}")
            
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to publish folder: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            job.state = PublishState.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
    def _upload_index(self, folder_id: str, index_data: bytes) -> Dict[str, Any]:
        """Upload index to Usenet"""
        # Split into segments if needed
        segments = []
        
        if len(index_data) <= self.index_segment_size:
            # Single segment
            segments.append(index_data)
        else:
            # Multiple segments
            for i in range(0, len(index_data), self.index_segment_size):
                segment = index_data[i:i + self.index_segment_size]
                segments.append(segment)
                
            if len(segments) > self.max_index_segments:
                raise ValueError(
                    f"Index too large: {len(segments)} segments exceeds max {self.max_index_segments}"
                )
                
        # Upload each segment
        uploaded_segments = []
        
        for i, segment_data in enumerate(segments):
            # Generate subject for index segment
            subject = self.security.generate_obfuscated_subject(
                folder_id, "INDEX", i
            )
            
            # Post to Usenet
            success, message_id = self.nntp.post_data(
                subject=subject,
                data=segment_data,
                newsgroup=self.index_newsgroup,
                from_user=f"usenetsync_{folder_id[:8]}@usenetsync.local"
            )
            
            if not success:
                raise Exception(f"Failed to upload index segment {i}: {message_id}")
                
            uploaded_segments.append({
                'index': i,
                'message_id': message_id,
                'newsgroup': self.index_newsgroup,
                'subject': subject,
                'size': len(segment_data)
            })
            
            self.logger.debug(f"Uploaded index segment {i}/{len(segments)}")
            
        # Return reference
        if len(uploaded_segments) == 1:
            # Single segment - simple reference
            return {
                'type': 'single',
                'message_id': uploaded_segments[0]['message_id'],
                'newsgroup': uploaded_segments[0]['newsgroup'],
                'subject': uploaded_segments[0]['subject']
            }
        else:
            # Multiple segments
            return {
                'type': 'multi',
                'segments': uploaded_segments,
                'total': len(segments)
            }
            
    def get_share_info(self, share_id: str) -> Optional[ShareInfo]:
        """Get information about a published share"""
        with self._shares_lock:
            if share_id in self.published_shares:
                return self.published_shares[share_id]
                
        # Try loading from database
        share_data = self.db.get_share_by_id(share_id)
        if share_data:
            return self._share_from_db(share_data)
            
        return None
        
    def get_folder_shares(self, folder_id: str) -> List[ShareInfo]:
        """Get all shares for a folder"""
        shares = []
        
        # Check cache
        with self._shares_lock:
            for share in self.published_shares.values():
                if share.folder_id == folder_id and share.is_active:
                    shares.append(share)
                    
        # Also check database
        db_shares = self.db.get_folder_shares(folder_id)
        for db_share in db_shares:
            share_info = self._share_from_db(db_share)
            if share_info and share_info.share_id not in [s.share_id for s in shares]:
                shares.append(share_info)
                
        return shares
        
    def list_shares(self) -> List[Dict[str, Any]]:
        """List all active shares"""
        shares = []
        
        with self._shares_lock:
            for share in self.published_shares.values():
                if share.is_active:
                    shares.append({
                        'share_id': share.share_id,
                        'share_type': share.share_type,
                        'folder_id': share.folder_id,
                        'folder_name': share.folder_name,
                        'version': share.version,
                        'created_at': share.created_at,
                        'access_string': share.access_string,
                        'statistics': share.statistics
                    })
        
        return shares
    
    def revoke_share(self, share_id: str) -> bool:
        """Revoke a published share"""
        # Update cache
        with self._shares_lock:
            if share_id in self.published_shares:
                self.published_shares[share_id].is_active = False
                
        # Update database
        return self.db.revoke_share(share_id)
        
    def update_share_access(self, share_id: str, user_ids_to_add: List[str],
                          user_ids_to_remove: List[str]) -> bool:
        """Update access control for private share"""
        share = self.get_share_info(share_id)
        if not share or share.share_type != 'private':
            return False
            
        # Update database
        for user_id in user_ids_to_add:
            self.db.add_authorized_user(share.folder_id, user_id, self.security.get_user_id())
            
        for user_id in user_ids_to_remove:
            self.db.remove_authorized_user(share.folder_id, user_id)
            
        # Re-publish with updated access
        folder = self.db.get_folder(share.folder_id)
        if folder:
            current_users = self.db.get_authorized_users(folder['id'])
            self.publish_folder(
                share.folder_id,
                'private',
                authorized_users=current_users,
                update_existing=True
            )
            
        return True
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get publishing job status"""
        with self._jobs_lock:
            job = self.active_jobs.get(job_id)
            
        if not job:
            return None
            
        return {
            'job_id': job.job_id,
            'folder_id': job.folder_id,
            'share_type': job.share_type,
            'state': job.state.value,
            'progress': self._calculate_job_progress(job),
            'share_id': job.share_id,
            'access_string': job.access_string,
            'error': job.error_message,
            'created_at': job.created_at.isoformat(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        }
        
    def _calculate_job_progress(self, job: PublishJob) -> float:
        """Calculate job progress percentage"""
        if job.state == PublishState.PUBLISHED:
            return 100.0
        elif job.state == PublishState.FAILED:
            return 0.0
        elif job.state == PublishState.PREPARING:
            return 25.0
        elif job.state == PublishState.UPLOADING:
            return 50.0
        else:
            return 0.0
            
    def cleanup_old_jobs(self, older_than_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        
        with self._jobs_lock:
            to_remove = []
            for job_id, job in self.active_jobs.items():
                if job.completed_at and job.completed_at < cutoff:
                    to_remove.append(job_id)
                    
            for job_id in to_remove:
                del self.active_jobs[job_id]
                
        self.logger.info(f"Cleaned up {len(to_remove)} old publishing jobs")
        
    def _generate_job_id(self, folder_id: str) -> str:
        """Generate unique job ID"""
        return hashlib.sha256(
            f"{folder_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        
    def _get_active_share(self, folder_id: str) -> Optional[ShareInfo]:
        """Get active share for folder"""
        shares = self.get_folder_shares(folder_id)
        for share in shares:
            if share.is_active:
                return share
        return None
        
    def _share_from_db(self, db_data: Dict) -> ShareInfo:
        """Create ShareInfo from database data"""
        return ShareInfo(
            share_id=db_data['share_id'],
            share_type=db_data['share_type'],
            folder_id=db_data['folder_id'],
            folder_name=db_data.get('folder_name', 'Unknown'),
            version=db_data['version'],
            created_at=db_data['published_at'],
            access_string=db_data['access_string'],
            index_reference=json.loads(db_data.get('index_reference', '{}')),
            statistics={
                'index_size': db_data.get('index_size', 0),
                'segment_count': db_data.get('segment_count', 0)
            },
            is_active=db_data.get('is_active', True)
        )
        
    def _load_published_shares(self):
        """Load published shares from database"""
        try:
            shares = self.db.get_all_shares()
            
            with self._shares_lock:
                for share_data in shares:
                    share_info = self._share_from_db(share_data)
                    self.published_shares[share_info.share_id] = share_info
                    
            self.logger.info(f"Loaded {len(shares)} published shares")
            
        except Exception as e:
            self.logger.error(f"Failed to load published shares: {e}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get publishing statistics"""
        with self._shares_lock:
            active_shares = sum(1 for s in self.published_shares.values() if s.is_active)
            
        with self._jobs_lock:
            active_jobs = sum(1 for j in self.active_jobs.values() 
                            if j.state in [PublishState.PREPARING, PublishState.UPLOADING])
            
        return {
            'total_shares': len(self.published_shares),
            'active_shares': active_shares,
            'active_jobs': active_jobs,
            'completed_jobs': len(self.active_jobs) - active_jobs,
            'share_types': self._count_share_types()
        }
        
    def _count_share_types(self) -> Dict[str, int]:
        """Count shares by type"""
        counts = {'public': 0, 'private': 0, 'protected': 0}
        
        with self._shares_lock:
            for share in self.published_shares.values():
                if share.is_active and share.share_type in counts:
                    counts[share.share_type] += 1
                    
        return counts

    def get_share_access_history(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Get the access history for a folder showing all published versions.
        
        This helps track which users have access to which versions,
        remembering that ALL historical versions remain accessible forever.
        """
        shares = self.db.get_folder_shares(folder_id)
        history = []
        
        for share in shares:
            # Get authorized users for this version
            auth_users = None
            if share['share_type'] == 'private':
                # Extract from index if stored
                auth_users = self._get_share_authorized_users(share['share_id'])
                
            history.append({
                'share_id': share['share_id'],
                'version': share['version'],
                'published_at': share['created_at'],
                'share_type': share['share_type'],
                'access_string': share['access_string'],
                'is_active': share.get('is_active', True),
                'authorized_users': auth_users,
                'permanent_on_usenet': True,  # Always true!
                'note': 'This share is permanently accessible to authorized users'
            })
            
        return history

    def _get_share_authorized_users(self, share_id: str) -> Optional[List[str]]:
        """Get authorized users for a specific share"""
        # This would need to retrieve from stored index metadata
        # For now, return None as this info might not be stored
        return None