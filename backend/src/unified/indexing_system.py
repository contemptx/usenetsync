#!/usr/bin/env python3
"""
Unified Indexing System for UsenetSync
Combines VersionedCoreIndexSystem and SimplifiedBinaryIndex into a single, optimized system
"""

import os
import hashlib
import logging
import time
import json
import struct
import mmap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Generator
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['modified_time'] = self.modified_time.isoformat()
        if self.metadata:
            data['metadata'] = json.dumps(self.metadata)
        return data


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        if data['segment_data'] is not None:
            del data['segment_data']  # Don't store raw data in DB
        if data['packed_with']:
            data['packed_with'] = json.dumps(data['packed_with'])
        return data


class UnifiedIndexingSystem:
    """
    Unified indexing system that combines the best features of both systems:
    - Detailed file tracking from VersionedCore
    - Optimized binary format from SimplifiedBinary
    - Streaming support for large datasets
    - Folder structure preservation
    """
    
    DEFAULT_SEGMENT_SIZE = 768 * 1024  # 768KB default segment size
    BUFFER_SIZE = 10 * 1024 * 1024  # 10MB buffer for large files
    
    def __init__(self, database_connection, segment_size: int = None):
        """
        Initialize unified indexing system
        
        Args:
            database_connection: Database connection (SQLite or PostgreSQL)
            segment_size: Size of segments in bytes
        """
        self.db = database_connection
        self.segment_size = segment_size or self.DEFAULT_SEGMENT_SIZE
        self.stats = {
            'files_indexed': 0,
            'segments_created': 0,
            'total_size': 0,
            'errors': 0
        }
        self._lock = threading.Lock()
        
    def index_folder(self, folder_path: str, folder_id: str = None, 
                    progress_callback=None, use_parallel: bool = True) -> Dict[str, Any]:
        """
        Index a folder and all its contents
        
        Args:
            folder_path: Path to folder to index
            folder_id: Unique folder ID (generated if not provided)
            progress_callback: Callback for progress updates
            use_parallel: Use parallel processing for large folders
            
        Returns:
            Index statistics and folder information
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        if not folder_id:
            folder_id = self._generate_folder_id(str(folder_path))
            
        logger.info(f"Starting index of folder: {folder_path} (ID: {folder_id})")
        
        # Reset stats
        self.stats = {
            'files_indexed': 0,
            'segments_created': 0,
            'total_size': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Create or update folder record
        self._create_folder_record(folder_id, folder_path)
        
        # Scan and index files
        if use_parallel and self._count_files(folder_path) > 100:
            self._index_folder_parallel(folder_path, folder_id, progress_callback)
        else:
            self._index_folder_sequential(folder_path, folder_id, progress_callback)
            
        # Update folder statistics
        self._update_folder_stats(folder_id)
        
        # Calculate final stats
        self.stats['duration'] = time.time() - self.stats['start_time']
        self.stats['folder_id'] = folder_id
        
        logger.info(f"Indexing complete: {self.stats['files_indexed']} files, "
                   f"{self.stats['segments_created']} segments, "
                   f"{self.stats['total_size'] / (1024*1024):.2f} MB")
        
        return self.stats
        
    def _index_folder_sequential(self, folder_path: Path, folder_id: str, 
                                progress_callback=None):
        """Index folder sequentially"""
        for file_path in self._walk_folder(folder_path):
            try:
                # Calculate relative path to preserve folder structure
                relative_path = file_path.relative_to(folder_path)
                relative_str = str(relative_path).replace('\\', '/')
                
                file_info = self._index_file(file_path, folder_id, relative_str)
                
                if file_info:
                    self.stats['files_indexed'] += 1
                    self.stats['total_size'] += file_info.file_size
                    
                    if progress_callback:
                        progress_callback({
                            'current_file': relative_str,
                            'files_indexed': self.stats['files_indexed'],
                            'total_size': self.stats['total_size']
                        })
                        
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                self.stats['errors'] += 1
                
    def _index_folder_parallel(self, folder_path: Path, folder_id: str,
                              progress_callback=None):
        """Index folder using parallel processing"""
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []
            
            for file_path in self._walk_folder(folder_path):
                relative_path = file_path.relative_to(folder_path)
                relative_str = str(relative_path).replace('\\', '/')
                
                future = executor.submit(
                    self._index_file, file_path, folder_id, relative_str
                )
                futures.append((future, relative_str))
                
            for future, relative_str in futures:
                try:
                    file_info = future.result(timeout=60)
                    
                    if file_info:
                        with self._lock:
                            self.stats['files_indexed'] += 1
                            self.stats['total_size'] += file_info.file_size
                            
                        if progress_callback:
                            progress_callback({
                                'current_file': relative_str,
                                'files_indexed': self.stats['files_indexed'],
                                'total_size': self.stats['total_size']
                            })
                            
                except Exception as e:
                    logger.error(f"Failed to index {relative_str}: {e}")
                    with self._lock:
                        self.stats['errors'] += 1
                        
    def _index_file(self, file_path: Path, folder_id: str, 
                   relative_path: str) -> Optional[UnifiedFileInfo]:
        """
        Index a single file
        
        Args:
            file_path: Absolute path to file
            folder_id: Folder ID
            relative_path: Relative path from folder root
            
        Returns:
            UnifiedFileInfo or None if failed
        """
        try:
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Check if file already indexed and unchanged
            existing = self._get_existing_file(folder_id, relative_path)
            if existing and existing['modified_time'] >= modified_time:
                logger.debug(f"File unchanged, skipping: {relative_path}")
                return None
                
            # Calculate file hash and segment hashes
            file_hash, segment_hashes = self._hash_file_and_segments(
                file_path, file_size
            )
            
            # Determine version
            version = 1
            if existing:
                version = existing['version'] + 1
                
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
            
            with self._lock:
                self.stats['segments_created'] += len(segment_hashes)
                
            logger.debug(f"Indexed: {relative_path} ({len(segment_hashes)} segments)")
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return None
            
    def _hash_file_and_segments(self, file_path: Path, 
                               file_size: int) -> Tuple[str, List[str]]:
        """
        Calculate file hash and segment hashes efficiently
        
        Args:
            file_path: Path to file
            file_size: Size of file
            
        Returns:
            Tuple of (file_hash, list_of_segment_hashes)
        """
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
                    
                # Update file hash
                file_hasher.update(segment_data)
                
                # Calculate segment hash
                segment_hash = hashlib.sha256(segment_data).hexdigest()
                segment_hashes.append(segment_hash)
                
        return file_hasher.hexdigest(), segment_hashes
        
    def _hash_large_file(self, file_path: Path, 
                        file_size: int) -> Tuple[str, List[str]]:
        """
        Hash large file using memory mapping to avoid loading into RAM
        
        Args:
            file_path: Path to large file
            file_size: Size of file
            
        Returns:
            Tuple of (file_hash, list_of_segment_hashes)
        """
        file_hasher = hashlib.sha256()
        segment_hashes = []
        
        with open(file_path, 'rb') as f:
            # Use memory mapping
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                offset = 0
                
                while offset < file_size:
                    # Calculate segment size
                    segment_size = min(self.segment_size, file_size - offset)
                    
                    # Read segment using memory map
                    segment_data = mmapped_file[offset:offset + segment_size]
                    
                    # Update file hash
                    file_hasher.update(segment_data)
                    
                    # Calculate segment hash
                    segment_hash = hashlib.sha256(segment_data).hexdigest()
                    segment_hashes.append(segment_hash)
                    
                    offset += segment_size
                    
        return file_hasher.hexdigest(), segment_hashes
        
    def create_binary_index(self, folder_id: str, output_path: str) -> int:
        """
        Create optimized binary index file for a folder
        
        Args:
            folder_id: Folder ID to create index for
            output_path: Path to save binary index
            
        Returns:
            Size of created index file
        """
        logger.info(f"Creating binary index for folder {folder_id}")
        
        # Get all files for folder
        cursor = self.db.cursor()
        
        if hasattr(cursor, 'execute'):  # SQLite
            cursor.execute("""
                SELECT file_path, file_hash, file_size, modified_time, segment_count
                FROM files
                WHERE folder_id = ? AND state = 'indexed'
                ORDER BY file_path
            """, (folder_id,))
        else:  # PostgreSQL
            cursor.execute("""
                SELECT file_path, file_hash, file_size, modified_time, segment_count
                FROM files
                WHERE folder_id = %s AND state = 'indexed'
                ORDER BY file_path
            """, (folder_id,))
            
        files = cursor.fetchall()
        
        # Write binary index
        with open(output_path, 'wb') as f:
            # Write header
            f.write(b'USIX')  # Magic bytes for UsenetSync Index
            f.write(struct.pack('<H', 1))  # Version
            f.write(struct.pack('<I', len(files)))  # File count
            
            # Write file entries
            for file_row in files:
                # Convert row to dict if needed
                if hasattr(file_row, 'keys'):
                    file_data = dict(file_row)
                else:
                    file_data = {
                        'file_path': file_row[0],
                        'file_hash': file_row[1],
                        'file_size': file_row[2],
                        'modified_time': file_row[3],
                        'segment_count': file_row[4]
                    }
                    
                # Write file entry
                path_bytes = file_data['file_path'].encode('utf-8')
                f.write(struct.pack('<H', len(path_bytes)))
                f.write(path_bytes)
                
                f.write(bytes.fromhex(file_data['file_hash']))
                f.write(struct.pack('<Q', file_data['file_size']))
                
                # Convert timestamp
                if isinstance(file_data['modified_time'], str):
                    timestamp = int(datetime.fromisoformat(
                        file_data['modified_time']
                    ).timestamp())
                else:
                    timestamp = int(file_data['modified_time'].timestamp())
                    
                f.write(struct.pack('<I', timestamp))
                f.write(struct.pack('<I', file_data['segment_count']))
                
        index_size = os.path.getsize(output_path)
        logger.info(f"Created binary index: {index_size} bytes")
        
        return index_size
        
    def _walk_folder(self, folder_path: Path) -> Generator[Path, None, None]:
        """Walk folder and yield file paths"""
        for root, dirs, files in os.walk(folder_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                    
                yield Path(root) / filename
                
    def _count_files(self, folder_path: Path) -> int:
        """Count files in folder for parallel processing decision"""
        count = 0
        for _ in self._walk_folder(folder_path):
            count += 1
            if count > 100:  # Early exit if we know we'll use parallel
                break
        return count
        
    def _generate_folder_id(self, folder_path: str) -> str:
        """Generate unique folder ID"""
        return hashlib.sha256(
            f"{folder_path}_{time.time()}".encode()
        ).hexdigest()
        
    def _create_folder_record(self, folder_id: str, folder_path: Path):
        """Create or update folder record in database"""
        cursor = self.db.cursor()
        
        folder_name = folder_path.name
        
        # For now, use placeholder keys (will be replaced by security system)
        public_key = "placeholder_public_key"
        private_key_encrypted = "placeholder_private_key"
        owner_id = "placeholder_owner_id"
        
        if hasattr(cursor, 'execute'):  # SQLite
            cursor.execute("""
                INSERT OR REPLACE INTO folders 
                (folder_id, folder_path, folder_name, owner_id, 
                 public_key, private_key_encrypted, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (folder_id, str(folder_path), folder_name, owner_id,
                  public_key, private_key_encrypted))
        else:  # PostgreSQL
            cursor.execute("""
                INSERT INTO folders 
                (folder_id, folder_path, folder_name, owner_id,
                 public_key, private_key_encrypted, last_indexed)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (folder_id) DO UPDATE
                SET last_indexed = CURRENT_TIMESTAMP
            """, (folder_id, str(folder_path), folder_name, owner_id,
                  public_key, private_key_encrypted))
                  
        self.db.commit()
        
    def _get_existing_file(self, folder_id: str, file_path: str) -> Optional[Dict]:
        """Get existing file record if it exists"""
        cursor = self.db.cursor()
        
        if hasattr(cursor, 'execute'):  # SQLite
            cursor.execute("""
                SELECT * FROM files
                WHERE folder_id = ? AND file_path = ?
                ORDER BY version DESC
                LIMIT 1
            """, (folder_id, file_path))
        else:  # PostgreSQL
            cursor.execute("""
                SELECT * FROM files
                WHERE folder_id = %s AND file_path = %s
                ORDER BY version DESC
                LIMIT 1
            """, (folder_id, file_path))
            
        row = cursor.fetchone()
        
        if row:
            if hasattr(row, 'keys'):
                return dict(row)
            else:
                # Convert tuple to dict for SQLite
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
                
        return None
        
    def _store_file_info(self, file_info: UnifiedFileInfo) -> int:
        """Store file information in database"""
        cursor = self.db.cursor()
        
        data = file_info.to_dict()
        
        if hasattr(cursor, 'execute'):  # SQLite
            cursor.execute("""
                INSERT INTO files 
                (folder_id, file_path, file_hash, file_size, modified_time,
                 version, segment_count, state, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['folder_id'], data['file_path'], data['file_hash'],
                  data['file_size'], data['modified_time'], data['version'],
                  data['segment_count'], data['state'], data.get('metadata')))
                  
            file_id = cursor.lastrowid
            
        else:  # PostgreSQL
            cursor.execute("""
                INSERT INTO files 
                (folder_id, file_path, file_hash, file_size, modified_time,
                 version, segment_count, state, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING file_id
            """, (data['folder_id'], data['file_path'], data['file_hash'],
                  data['file_size'], data['modified_time'], data['version'],
                  data['segment_count'], data['state'], data.get('metadata')))
                  
            file_id = cursor.fetchone()['file_id']
            
        self.db.commit()
        
        return file_id
        
    def _store_segments(self, file_info: UnifiedFileInfo):
        """Store segment information in database"""
        cursor = self.db.cursor()
        
        for i, segment_hash in enumerate(file_info.segment_hashes):
            segment_size = min(
                self.segment_size,
                file_info.file_size - (i * self.segment_size)
            )
            
            if hasattr(cursor, 'execute'):  # SQLite
                cursor.execute("""
                    INSERT INTO segments 
                    (file_id, segment_index, segment_hash, segment_size)
                    VALUES (?, ?, ?, ?)
                """, (file_info.file_id, i, segment_hash, segment_size))
            else:  # PostgreSQL
                cursor.execute("""
                    INSERT INTO segments 
                    (file_id, segment_index, segment_hash, segment_size)
                    VALUES (%s, %s, %s, %s)
                """, (file_info.file_id, i, segment_hash, segment_size))
                
        self.db.commit()
        
    def _update_folder_stats(self, folder_id: str):
        """Update folder statistics"""
        cursor = self.db.cursor()
        
        if hasattr(cursor, 'execute'):  # SQLite
            cursor.execute("""
                UPDATE folders
                SET file_count = (
                    SELECT COUNT(*) FROM files 
                    WHERE folder_id = ? AND state = 'indexed'
                ),
                total_size = (
                    SELECT COALESCE(SUM(file_size), 0) FROM files
                    WHERE folder_id = ? AND state = 'indexed'
                ),
                segment_count = (
                    SELECT COALESCE(SUM(segment_count), 0) FROM files
                    WHERE folder_id = ? AND state = 'indexed'
                ),
                updated_at = datetime('now')
                WHERE folder_id = ?
            """, (folder_id, folder_id, folder_id, folder_id))
        else:  # PostgreSQL
            cursor.execute("""
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
            
        self.db.commit()


def test_unified_indexing():
    """Test unified indexing system with real data"""
    import tempfile
    import shutil
    from unified.database_schema import UnifiedDatabaseSchema
    
    print("\n=== Testing Unified Indexing System ===\n")
    
    # Create test folder with files
    test_dir = tempfile.mkdtemp(prefix="usenet_test_")
    
    try:
        # Create test folder structure
        print("Creating test folder structure...")
        
        # Create subdirectories to test folder preservation
        (Path(test_dir) / "documents").mkdir()
        (Path(test_dir) / "images").mkdir()
        (Path(test_dir) / "data" / "nested").mkdir(parents=True)
        
        # Create test files
        test_files = [
            ("README.md", b"# Test Project\nThis is a test file for indexing." * 100),
            ("documents/report.txt", b"Annual report content here..." * 500),
            ("documents/notes.txt", b"Meeting notes..." * 200),
            ("images/photo.jpg", os.urandom(1024 * 100)),  # 100KB random data
            ("data/dataset.csv", b"col1,col2,col3\n" + b"1,2,3\n" * 1000),
            ("data/nested/config.json", b'{"setting": "value"}' * 50),
        ]
        
        for file_path, content in test_files:
            full_path = Path(test_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(content)
            
        print(f"Created {len(test_files)} test files in {test_dir}")
        
        # Test with SQLite
        print("\n--- Testing with SQLite ---")
        
        # Create database
        schema = UnifiedDatabaseSchema('sqlite', path='test_unified_index.db')
        schema.create_schema()
        
        # Create indexing system
        indexer = UnifiedIndexingSystem(schema.get_connection())
        
        # Index the folder
        def progress_callback(progress):
            print(f"  Indexing: {progress['current_file']} "
                  f"({progress['files_indexed']} files, "
                  f"{progress['total_size'] / 1024:.1f} KB)")
        
        stats = indexer.index_folder(test_dir, progress_callback=progress_callback)
        
        print(f"\nIndexing complete:")
        print(f"  Files indexed: {stats['files_indexed']}")
        print(f"  Segments created: {stats['segments_created']}")
        print(f"  Total size: {stats['total_size'] / 1024:.1f} KB")
        print(f"  Duration: {stats['duration']:.2f} seconds")
        print(f"  Errors: {stats['errors']}")
        
        # Create binary index
        binary_path = "test_folder.idx"
        index_size = indexer.create_binary_index(stats['folder_id'], binary_path)
        print(f"\nBinary index created: {index_size} bytes")
        
        # Verify database contents
        cursor = schema.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) as count FROM files")
        file_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM segments")
        segment_count = cursor.fetchone()[0]
        
        print(f"\nDatabase verification:")
        print(f"  Files in DB: {file_count}")
        print(f"  Segments in DB: {segment_count}")
        
        # Test folder structure preservation
        cursor.execute("SELECT file_path FROM files ORDER BY file_path")
        file_paths = [row[0] for row in cursor.fetchall()]
        
        print(f"\nPreserved folder structure:")
        for path in file_paths:
            print(f"  {path}")
            
        schema.close()
        
        # Test with PostgreSQL
        print("\n--- Testing with PostgreSQL ---")
        
        pg_schema = UnifiedDatabaseSchema(
            'postgresql',
            host='localhost',
            database='usenetsync',
            user='usenetsync',
            password='usenetsync123'
        )
        pg_schema.create_schema()
        
        # Create indexing system for PostgreSQL
        pg_indexer = UnifiedIndexingSystem(pg_schema.get_connection())
        
        # Index the same folder
        pg_stats = pg_indexer.index_folder(test_dir)
        
        print(f"\nPostgreSQL indexing complete:")
        print(f"  Files indexed: {pg_stats['files_indexed']}")
        print(f"  Segments created: {pg_stats['segments_created']}")
        
        pg_schema.close()
        
        print("\n✓ Unified indexing test completed successfully")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        if os.path.exists("test_folder.idx"):
            os.remove("test_folder.idx")
        print(f"\nCleaned up test directory: {test_dir}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_unified_indexing()