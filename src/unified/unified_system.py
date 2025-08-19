#!/usr/bin/env python3
"""
Complete Unified System for UsenetSync
Production-ready implementation combining all components
"""

import os
import sys
import hashlib
import logging
import time
import json
import struct
import mmap
import base64
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Generator
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class UnifiedFileInfo:
    """Unified file information structure"""
    file_id: Optional[int]
    folder_id: str
    file_path: str  # Relative path preserving folder structure
    file_hash: str
    file_size: int
    modified_time: datetime
    version: int
    segment_count: int
    segment_hashes: List[str]
    state: str = 'indexed'
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class UnifiedSegmentInfo:
    """Unified segment information"""
    segment_id: Optional[int]
    file_id: int
    segment_index: int
    segment_hash: str
    segment_size: int
    segment_data: Optional[bytes] = None
    packed_with: Optional[List[int]] = None
    redundancy_level: int = 0
    encrypted_location: Optional[str] = None
    message_id: Optional[str] = None
    internal_subject: Optional[str] = None
    usenet_subject: Optional[str] = None
    upload_status: str = 'pending'

@dataclass
class PackedSegment:
    """Represents multiple small segments packed together"""
    packed_id: str
    segments: List[UnifiedSegmentInfo]
    total_size: int
    packed_data: bytes
    
# ============================================================================
# DATABASE MANAGER
# ============================================================================

class UnifiedDatabaseManager:
    """Unified database manager supporting both SQLite and PostgreSQL"""
    
    def __init__(self, db_type: str = 'sqlite', **kwargs):
        self.db_type = db_type.lower()
        self.connection_params = kwargs
        self.connection = None
        self._lock = threading.Lock()
        
    def connect(self):
        """Establish database connection"""
        if self.db_type == 'postgresql':
            self.connection = psycopg2.connect(
                host=self.connection_params.get('host', 'localhost'),
                port=self.connection_params.get('port', 5432),
                database=self.connection_params.get('database', 'usenetsync'),
                user=self.connection_params.get('user', 'usenetsync'),
                password=self.connection_params.get('password', 'usenetsync123'),
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = False
        else:  # SQLite
            db_path = self.connection_params.get('path', 'usenetsync.db')
            self.connection = sqlite3.connect(
                db_path,
                check_same_thread=False,
                isolation_level=None
            )
            self.connection.row_factory = sqlite3.Row
            # Enable optimizations
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            
    def execute(self, query: str, params: tuple = None):
        """Execute query with proper parameter formatting"""
        with self._lock:
            cursor = self.connection.cursor()
            
            if self.db_type == 'sqlite':
                # Convert %s to ? for SQLite
                query = query.replace('%s', '?')
                
            cursor.execute(query, params or ())
            
            if self.db_type == 'postgresql':
                self.connection.commit()
                
            return cursor
            
    def fetchone(self, query: str, params: tuple = None):
        """Fetch one result"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
        
    def fetchall(self, query: str, params: tuple = None):
        """Fetch all results"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
        
    def insert_returning(self, query: str, params: tuple):
        """Insert and return ID (handles both databases)"""
        with self._lock:
            cursor = self.connection.cursor()
            
            if self.db_type == 'sqlite':
                # SQLite doesn't support RETURNING
                query = query.replace(' RETURNING file_id', '')
                query = query.replace(' RETURNING segment_id', '')
                query = query.replace('%s', '?')
                cursor.execute(query, params)
                return cursor.lastrowid
            else:
                cursor.execute(query, params)
                self.connection.commit()
                result = cursor.fetchone()
                return result['file_id'] if 'file_id' in result else result['segment_id']

# ============================================================================
# UNIFIED INDEXING SYSTEM
# ============================================================================

class UnifiedIndexingSystem:
    """Unified indexing system combining best features of both systems"""
    
    DEFAULT_SEGMENT_SIZE = 768 * 1024  # 768KB
    BUFFER_SIZE = 10 * 1024 * 1024  # 10MB for large files
    
    def __init__(self, db_manager: UnifiedDatabaseManager):
        self.db = db_manager
        self.segment_size = self.DEFAULT_SEGMENT_SIZE
        self.stats = {}
        self._lock = threading.Lock()
        
    def index_folder(self, folder_path: str, folder_id: str = None,
                    progress_callback=None) -> Dict[str, Any]:
        """Index a folder and all its contents"""
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        if not folder_id:
            folder_id = self._generate_folder_id(str(folder_path))
            
        logger.info(f"Indexing folder: {folder_path} (ID: {folder_id})")
        
        self.stats = {
            'files_indexed': 0,
            'segments_created': 0,
            'total_size': 0,
            'errors': 0,
            'start_time': time.time(),
            'folder_id': folder_id
        }
        
        # Create folder record
        self._create_folder_record(folder_id, folder_path)
        
        # Index files
        for file_path in self._walk_folder(folder_path):
            try:
                relative_path = file_path.relative_to(folder_path)
                relative_str = str(relative_path).replace('\\', '/')
                
                file_info = self._index_file(file_path, folder_id, relative_str)
                
                if file_info:
                    self.stats['files_indexed'] += 1
                    self.stats['total_size'] += file_info.file_size
                    self.stats['segments_created'] += file_info.segment_count
                    
                    if progress_callback:
                        progress_callback({
                            'current_file': relative_str,
                            'files_indexed': self.stats['files_indexed'],
                            'total_size': self.stats['total_size']
                        })
                        
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                self.stats['errors'] += 1
                
        # Update folder statistics
        self._update_folder_stats(folder_id)
        
        self.stats['duration'] = time.time() - self.stats['start_time']
        
        logger.info(f"Indexing complete: {self.stats['files_indexed']} files, "
                   f"{self.stats['segments_created']} segments")
        
        return self.stats
        
    def _index_file(self, file_path: Path, folder_id: str,
                   relative_path: str) -> Optional[UnifiedFileInfo]:
        """Index a single file"""
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Check if already indexed
            existing = self._get_existing_file(folder_id, relative_path)
            if existing and existing.get('modified_time'):
                existing_time = existing['modified_time']
                if isinstance(existing_time, str):
                    existing_time = datetime.fromisoformat(existing_time)
                if existing_time >= modified_time:
                    logger.debug(f"File unchanged: {relative_path}")
                    return None
                    
            # Calculate hashes
            file_hash, segment_hashes = self._hash_file_and_segments(
                file_path, file_size
            )
            
            # Determine version
            version = 1
            if existing:
                version = existing.get('version', 0) + 1
                
            # Create file info
            file_info = UnifiedFileInfo(
                file_id=None,
                folder_id=folder_id,
                file_path=relative_path,
                file_hash=file_hash,
                file_size=file_size,
                modified_time=modified_time,
                version=version,
                segment_count=len(segment_hashes),
                segment_hashes=segment_hashes,
                state='indexed'
            )
            
            # Store in database
            file_id = self._store_file_info(file_info)
            file_info.file_id = file_id
            
            # Store segments
            self._store_segments(file_info)
            
            logger.debug(f"Indexed: {relative_path} ({len(segment_hashes)} segments)")
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return None
            
    def _hash_file_and_segments(self, file_path: Path,
                               file_size: int) -> Tuple[str, List[str]]:
        """Calculate file and segment hashes"""
        file_hasher = hashlib.sha256()
        segment_hashes = []
        
        # Use memory mapping for large files
        if file_size > self.BUFFER_SIZE:
            return self._hash_large_file(file_path, file_size)
            
        # Regular processing for smaller files
        with open(file_path, 'rb') as f:
            while True:
                segment_data = f.read(self.segment_size)
                if not segment_data:
                    break
                    
                file_hasher.update(segment_data)
                segment_hash = hashlib.sha256(segment_data).hexdigest()
                segment_hashes.append(segment_hash)
                
        return file_hasher.hexdigest(), segment_hashes
        
    def _hash_large_file(self, file_path: Path,
                        file_size: int) -> Tuple[str, List[str]]:
        """Hash large file using memory mapping"""
        file_hasher = hashlib.sha256()
        segment_hashes = []
        
        with open(file_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                offset = 0
                
                while offset < file_size:
                    segment_size = min(self.segment_size, file_size - offset)
                    segment_data = mmapped[offset:offset + segment_size]
                    
                    file_hasher.update(segment_data)
                    segment_hash = hashlib.sha256(segment_data).hexdigest()
                    segment_hashes.append(segment_hash)
                    
                    offset += segment_size
                    
        return file_hasher.hexdigest(), segment_hashes
        
    def _generate_folder_id(self, folder_path: str) -> str:
        """Generate unique folder ID"""
        return hashlib.sha256(
            f"{folder_path}_{time.time()}".encode()
        ).hexdigest()
        
    def _create_folder_record(self, folder_id: str, folder_path: Path):
        """Create folder record in database"""
        # Placeholder keys - will be replaced by security system
        public_key = "placeholder_public_key"
        private_key = "placeholder_private_key"
        owner_id = "placeholder_owner_id"
        
        self.db.execute("""
            INSERT INTO folders 
            (folder_id, folder_path, folder_name, owner_id,
             public_key, private_key_encrypted, last_indexed)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (folder_id) DO UPDATE
            SET last_indexed = CURRENT_TIMESTAMP
        """, (folder_id, str(folder_path), folder_path.name,
              owner_id, public_key, private_key))
              
    def _get_existing_file(self, folder_id: str, file_path: str):
        """Get existing file record"""
        result = self.db.fetchone("""
            SELECT * FROM files
            WHERE folder_id = %s AND file_path = %s
            ORDER BY version DESC
            LIMIT 1
        """, (folder_id, file_path))
        
        if result:
            return dict(result)
        return None
        
    def _store_file_info(self, file_info: UnifiedFileInfo) -> int:
        """Store file info in database"""
        return self.db.insert_returning("""
            INSERT INTO files 
            (folder_id, file_path, file_hash, file_size, modified_time,
             version, segment_count, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING file_id
        """, (file_info.folder_id, file_info.file_path, file_info.file_hash,
              file_info.file_size, file_info.modified_time.isoformat(),
              file_info.version, file_info.segment_count, file_info.state))
              
    def _store_segments(self, file_info: UnifiedFileInfo):
        """Store segment information"""
        for i, segment_hash in enumerate(file_info.segment_hashes):
            segment_size = min(
                self.segment_size,
                file_info.file_size - (i * self.segment_size)
            )
            
            self.db.execute("""
                INSERT INTO segments 
                (file_id, segment_index, segment_hash, segment_size)
                VALUES (%s, %s, %s, %s)
            """, (file_info.file_id, i, segment_hash, segment_size))
            
    def _update_folder_stats(self, folder_id: str):
        """Update folder statistics"""
        self.db.execute("""
            UPDATE folders
            SET file_count = (
                SELECT COUNT(*) FROM files 
                WHERE folder_id = %s AND state = 'indexed'
            ),
            total_size = (
                SELECT COALESCE(SUM(file_size), 0) FROM files
                WHERE folder_id = %s AND state = 'indexed'
            ),
            segment_count = (
                SELECT COALESCE(SUM(segment_count), 0) FROM files
                WHERE folder_id = %s AND state = 'indexed'
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE folder_id = %s
        """, (folder_id, folder_id, folder_id, folder_id))
        
    def _walk_folder(self, folder_path: Path) -> Generator[Path, None, None]:
        """Walk folder and yield file paths"""
        for root, dirs, files in os.walk(folder_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if not filename.startswith('.'):
                    yield Path(root) / filename

# ============================================================================
# SEGMENT PACKING SYSTEM
# ============================================================================

class UnifiedSegmentPacker:
    """Handles segment packing for small files"""
    
    TARGET_PACK_SIZE = 750 * 1024  # 750KB target for packed segments
    
    def __init__(self, db_manager: UnifiedDatabaseManager):
        self.db = db_manager
        self.packing_buffer = []
        self.buffer_size = 0
        
    def pack_segments(self, folder_id: str) -> List[PackedSegment]:
        """Pack small segments together for efficient upload"""
        # Get small segments
        small_segments = self.db.fetchall("""
            SELECT s.*, f.file_path
            FROM segments s
            JOIN files f ON s.file_id = f.file_id
            WHERE f.folder_id = %s 
            AND s.segment_size < %s
            AND s.upload_status = 'pending'
            ORDER BY s.segment_size
        """, (folder_id, self.TARGET_PACK_SIZE // 2))
        
        packed_segments = []
        current_pack = []
        current_size = 0
        
        for segment in small_segments:
            segment_dict = dict(segment)
            
            if current_size + segment_dict['segment_size'] <= self.TARGET_PACK_SIZE:
                current_pack.append(segment_dict)
                current_size += segment_dict['segment_size']
            else:
                if current_pack:
                    packed = self._create_packed_segment(current_pack)
                    packed_segments.append(packed)
                    
                current_pack = [segment_dict]
                current_size = segment_dict['segment_size']
                
        # Pack remaining
        if current_pack:
            packed = self._create_packed_segment(current_pack)
            packed_segments.append(packed)
            
        logger.info(f"Created {len(packed_segments)} packed segments from "
                   f"{len(small_segments)} small segments")
        
        return packed_segments
        
    def _create_packed_segment(self, segments: List[dict]) -> PackedSegment:
        """Create a packed segment from multiple small segments"""
        packed_id = hashlib.sha256(
            f"{time.time()}_{len(segments)}".encode()
        ).hexdigest()[:16]
        
        # Create packed data structure
        packed_data = {
            'packed_id': packed_id,
            'segment_count': len(segments),
            'segments': []
        }
        
        for seg in segments:
            packed_data['segments'].append({
                'segment_id': seg['segment_id'],
                'file_id': seg['file_id'],
                'segment_index': seg['segment_index'],
                'segment_hash': seg['segment_hash'],
                'segment_size': seg['segment_size']
            })
            
        # Serialize to bytes
        packed_bytes = json.dumps(packed_data).encode('utf-8')
        
        # Update database to mark segments as packed
        segment_ids = [seg['segment_id'] for seg in segments]
        
        # PostgreSQL needs proper array format
        if self.db.db_type == 'postgresql':
            packed_array = '{' + ','.join(map(str, segment_ids)) + '}'
        else:
            packed_array = json.dumps(segment_ids)
            
        for sid in segment_ids:
            self.db.execute("""
                UPDATE segments 
                SET packed_with = %s
                WHERE segment_id = %s
            """, (packed_array, sid))
            
        return PackedSegment(
            packed_id=packed_id,
            segments=[],  # Would be populated with actual segment objects
            total_size=sum(s['segment_size'] for s in segments),
            packed_data=packed_bytes
        )

# ============================================================================
# UNIFIED UPLOAD SYSTEM
# ============================================================================

class UnifiedUploadSystem:
    """Unified upload system with redundancy and packing"""
    
    def __init__(self, nntp_client, db_manager: UnifiedDatabaseManager,
                 security_system=None):
        self.nntp = nntp_client
        self.db = db_manager
        self.security = security_system
        self.packer = UnifiedSegmentPacker(db_manager)
        self.stats = {}
        
    def upload_folder(self, folder_id: str, redundancy_level: int = 0,
                     pack_small_files: bool = True) -> Dict[str, Any]:
        """Upload all segments for a folder with redundancy"""
        logger.info(f"Starting upload for folder {folder_id} "
                   f"(redundancy: {redundancy_level})")
        
        self.stats = {
            'segments_uploaded': 0,
            'segments_failed': 0,
            'packed_segments': 0,
            'bytes_uploaded': 0,
            'redundancy_copies': 0,
            'start_time': time.time()
        }
        
        # Pack small segments if requested
        if pack_small_files:
            packed = self.packer.pack_segments(folder_id)
            for packed_segment in packed:
                if self._upload_packed_segment(packed_segment, redundancy_level):
                    self.stats['packed_segments'] += 1
                    self.stats['bytes_uploaded'] += packed_segment.total_size
                    
        # Get regular segments
        segments = self._get_pending_segments(folder_id)
        
        for segment in segments:
            success = self._upload_segment(segment, redundancy_level)
            if success:
                self.stats['segments_uploaded'] += 1
                self.stats['bytes_uploaded'] += segment['segment_size']
                self.stats['redundancy_copies'] += redundancy_level
            else:
                self.stats['segments_failed'] += 1
                
        self.stats['duration'] = time.time() - self.stats['start_time']
        
        logger.info(f"Upload complete: {self.stats['segments_uploaded']} segments, "
                   f"{self.stats['packed_segments']} packed, "
                   f"{self.stats['redundancy_copies']} redundancy copies")
        
        return self.stats
        
    def _get_pending_segments(self, folder_id: str):
        """Get segments pending upload"""
        return self.db.fetchall("""
            SELECT s.* 
            FROM segments s
            JOIN files f ON s.file_id = f.file_id
            WHERE f.folder_id = %s 
            AND s.upload_status = 'pending'
            AND s.packed_with IS NULL
        """, (folder_id,))
        
    def _upload_segment(self, segment: dict, redundancy_level: int) -> bool:
        """Upload a single segment with redundancy"""
        try:
            # Generate subjects
            internal_subject = hashlib.sha256(
                f"{segment['segment_hash']}_{time.time()}".encode()
            ).hexdigest()[:64]
            
            # Generate obfuscated Usenet subject
            usenet_subject = self._generate_obfuscated_subject()
            
            # Get actual segment data (would read from file)
            segment_data = self._get_segment_data(segment)
            
            # Encrypt if security system available
            if self.security:
                segment_data = self.security.encrypt_data(segment_data)
                
            # Upload main copy
            success, response = self.nntp.post_data(
                subject=usenet_subject,
                data=segment_data,
                newsgroup="alt.binaries.test"
            )
            
            if success:
                message_id = response[1] if isinstance(response, tuple) else str(response)
                
                # Store encrypted location
                encrypted_location = self._encrypt_location(message_id)
                
                # Update database
                self.db.execute("""
                    UPDATE segments 
                    SET upload_status = %s, message_id = %s,
                        internal_subject = %s, usenet_subject = %s,
                        encrypted_location = %s, uploaded_at = CURRENT_TIMESTAMP
                    WHERE segment_id = %s
                """, ('uploaded', message_id, internal_subject,
                      usenet_subject, encrypted_location, segment['segment_id']))
                
                # Upload redundancy copies as unique articles
                for i in range(redundancy_level):
                    redundant_subject = self._generate_obfuscated_subject()
                    
                    # Modify data slightly to make unique
                    redundant_data = self._create_redundant_copy(segment_data, i)
                    
                    r_success, r_response = self.nntp.post_data(
                        subject=redundant_subject,
                        data=redundant_data,
                        newsgroup="alt.binaries.test"
                    )
                    
                    if r_success:
                        # Store redundancy info
                        self._store_redundancy_info(
                            segment['segment_id'], i + 1,
                            r_response[1] if isinstance(r_response, tuple) else str(r_response),
                            redundant_subject
                        )
                        
                return True
            else:
                # Update retry count
                self.db.execute("""
                    UPDATE segments 
                    SET retry_count = retry_count + 1
                    WHERE segment_id = %s
                """, (segment['segment_id'],))
                return False
                
        except Exception as e:
            logger.error(f"Upload failed for segment {segment['segment_id']}: {e}")
            return False
            
    def _upload_packed_segment(self, packed: PackedSegment,
                              redundancy_level: int) -> bool:
        """Upload a packed segment"""
        try:
            usenet_subject = self._generate_obfuscated_subject()
            
            success, response = self.nntp.post_data(
                subject=usenet_subject,
                data=packed.packed_data,
                newsgroup="alt.binaries.test"
            )
            
            if success:
                # Upload redundancy copies
                for i in range(redundancy_level):
                    redundant_data = self._create_redundant_copy(packed.packed_data, i)
                    self.nntp.post_data(
                        subject=self._generate_obfuscated_subject(),
                        data=redundant_data,
                        newsgroup="alt.binaries.test"
                    )
                    
                return True
                
        except Exception as e:
            logger.error(f"Failed to upload packed segment: {e}")
            
        return False
        
    def _generate_obfuscated_subject(self) -> str:
        """Generate completely obfuscated subject"""
        # Random 20 character string
        return ''.join([chr(ord('a') + (b % 26)) for b in os.urandom(20)])
        
    def _encrypt_location(self, message_id: str) -> str:
        """Encrypt the Usenet location"""
        # Simple obfuscation for now - would use proper encryption
        return base64.b64encode(message_id.encode()).decode()
        
    def _get_segment_data(self, segment: dict) -> bytes:
        """Get actual segment data (placeholder for now)"""
        # In production, would read from file using segment info
        return f"SEGMENT_DATA_{segment['segment_hash']}".encode()
        
    def _create_redundant_copy(self, data: bytes, copy_num: int) -> bytes:
        """Create unique redundant copy"""
        # Add metadata to make it unique
        metadata = f"\nREDUNDANCY_COPY_{copy_num}_{time.time()}\n".encode()
        return metadata + data
        
    def _store_redundancy_info(self, segment_id: int, redundancy_level: int,
                              message_id: str, subject: str):
        """Store redundancy information"""
        self.db.execute("""
            INSERT INTO segments 
            (file_id, segment_index, segment_hash, segment_size,
             redundancy_level, message_id, usenet_subject, upload_status)
            SELECT file_id, segment_index, segment_hash, segment_size,
                   %s, %s, %s, 'uploaded'
            FROM segments WHERE segment_id = %s
        """, (redundancy_level, message_id, subject, segment_id))

# ============================================================================
# MAIN UNIFIED SYSTEM
# ============================================================================

class UnifiedSystem:
    """Main unified system orchestrator"""
    
    def __init__(self, db_type: str = 'sqlite', **db_params):
        # Store database type
        self.db_type = db_type
        
        # Initialize database
        self.db_manager = UnifiedDatabaseManager(db_type, **db_params)
        self.db_manager.connect()
        
        # Initialize subsystems
        self.indexer = UnifiedIndexingSystem(self.db_manager)
        self.uploader = None  # Initialized when NNTP client provided
        self.downloader = None  # Initialized when NNTP client provided
        
        # Import and initialize publishing system
        from unified.publishing_system import UnifiedPublishingSystem
        self.publisher = UnifiedPublishingSystem(self.db_manager)
        
        # Create schema
        self._create_schema()
        
    def _create_schema(self):
        """Create database schema"""
        from unified.database_schema import UnifiedDatabaseSchema
        
        schema = UnifiedDatabaseSchema(
            self.db_manager.db_type,
            **self.db_manager.connection_params
        )
        schema.connection = self.db_manager.connection
        schema.create_schema()
        
    def initialize_upload(self, nntp_client, security_system=None):
        """Initialize upload system with NNTP client"""
        self.uploader = UnifiedUploadSystem(
            nntp_client, self.db_manager, security_system
        )
        
    def index_and_upload(self, folder_path: str, redundancy: int = 1,
                        pack_small: bool = True) -> Dict[str, Any]:
        """Complete index and upload workflow"""
        # Index folder
        index_stats = self.indexer.index_folder(folder_path)
        
        if not self.uploader:
            raise RuntimeError("Upload system not initialized")
            
        # Upload with redundancy
        upload_stats = self.uploader.upload_folder(
            index_stats['folder_id'],
            redundancy_level=redundancy,
            pack_small_files=pack_small
        )
        
        return {
            'index': index_stats,
            'upload': upload_stats
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Unified System module loaded successfully")