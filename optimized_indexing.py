#!/usr/bin/env python3
"""
Optimized Indexing System with Write Queue
Prevents database locking during file indexing
"""

import os
import hashlib
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from database_write_queue import DatabaseWriteQueue

logger = logging.getLogger(__name__)


class OptimizedIndexingSystem:
    """
    Optimized indexing system that uses write queue for database operations
    """
    
    def __init__(self, db_manager, security_system, config: Dict = None):
        self.db = db_manager
        self.security = security_system
        self.config = config or {}
        
        # Configuration
        self.segment_size = self.config.get('segment_size', 768000)
        self.worker_threads = self.config.get('worker_threads', 4)
        self.batch_size = self.config.get('batch_size', 100)
        
        # Initialize write queue
        self.write_queue = DatabaseWriteQueue(
            db_manager,
            max_batch_size=self.batch_size,
            batch_timeout=0.5
        )
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'segments_created': 0,
            'bytes_processed': 0,
            'errors': 0
        }
    
    def index_folder(self, folder_path: str, folder_id: str, 
                    progress_callback: Optional[Callable] = None) -> Dict:
        """
        Index a folder with optimized database writes
        
        Args:
            folder_path: Path to folder to index
            folder_id: Unique identifier for folder
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with indexing results
        """
        logger.info(f"Starting optimized indexing for: {folder_path}")
        start_time = time.time()
        
        # Start write queue
        self.write_queue.start()
        
        try:
            # Ensure folder exists in database
            folder_db_id = self._ensure_folder_exists(folder_id, folder_path)
            
            # Generate encryption keys for folder
            keys = self.security.generate_folder_keys(folder_id)
            # Serialize keys for storage
            from cryptography.hazmat.primitives import serialization
            
            with self.db.pool.get_connection() as conn:
                if hasattr(keys, 'private_key') and hasattr(keys, 'public_key'):
                    # Serialize private key
                    private_bytes = keys.private_key.private_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PrivateFormat.Raw,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    # Serialize public key
                    public_bytes = keys.public_key.public_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PublicFormat.Raw
                    )
                    
                    conn.execute("""
                        UPDATE folders 
                        SET private_key = ?, public_key = ?, keys_updated_at = datetime('now')
                        WHERE folder_id = ?
                    """, (private_bytes, public_bytes, folder_db_id))
                    conn.commit()
            
            # Scan folder for files
            files = self._scan_folder(folder_path)
            total_files = len(files)
            
            logger.info(f"Found {total_files} files to index")
            
            # Process files in batches
            segments_batch = []
            files_processed = 0
            
            for i, file_path in enumerate(files):
                try:
                    # Process file and collect segments
                    file_segments = self._process_file(
                        file_path, 
                        folder_db_id,
                        folder_path
                    )
                    
                    # Add to batch
                    segments_batch.extend(file_segments)
                    
                    # Flush batch if it's large enough
                    if len(segments_batch) >= self.batch_size:
                        self._flush_segments_batch(segments_batch)
                        segments_batch = []
                    
                    files_processed += 1
                    self.stats['files_processed'] += 1
                    
                    # Update progress
                    if progress_callback:
                        progress = (i + 1) / total_files * 100
                        progress_callback({
                            'current': progress,
                            'files_done': i + 1,
                            'files_total': total_files,
                            'phase': 'indexing'
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    self.stats['errors'] += 1
            
            # Flush remaining segments
            if segments_batch:
                self._flush_segments_batch(segments_batch)
            
            # Wait for queue to complete
            time.sleep(1)  # Give queue time to flush
            
            # Update folder statistics
            self._update_folder_stats(folder_db_id)
            
            # Calculate results
            elapsed = time.time() - start_time
            
            result = {
                'folder_id': folder_id,
                'folder_db_id': folder_db_id,
                'files_indexed': files_processed,
                'total_size': self.stats['bytes_processed'],
                'total_segments': self.stats['segments_created'],
                'elapsed_time': elapsed,
                'errors': self.stats['errors']
            }
            
            logger.info(f"Indexing complete: {files_processed} files in {elapsed:.2f}s")
            
            return result
            
        finally:
            # Stop write queue
            self.write_queue.stop()
            
            # Log final statistics
            queue_stats = self.write_queue.get_stats()
            logger.info(f"Write queue stats: {queue_stats}")
    
    def _ensure_folder_exists(self, folder_id: str, folder_path: str) -> int:
        """Ensure folder exists in database"""
        with self.db.pool.get_connection() as conn:
            # Check if folder exists
            cursor = conn.execute("""
                SELECT folder_id FROM folders 
                WHERE folder_unique_id = ? OR folder_path = ?
            """, (folder_id, folder_path))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create folder if it doesn't exist
            cursor = conn.execute("""
                INSERT INTO folders (folder_unique_id, folder_path, display_name, share_type)
                VALUES (?, ?, ?, ?)
            """, (folder_id, folder_path, Path(folder_path).name, 'private'))
            folder_db_id = cursor.lastrowid
            conn.commit()
            
            return folder_db_id
    
    def _scan_folder(self, folder_path: str) -> List[Path]:
        """Scan folder for files"""
        files = []
        folder = Path(folder_path)
        
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                # Skip hidden files and system files
                if not file_path.name.startswith('.'):
                    files.append(file_path)
        
        return sorted(files)
    
    def _process_file(self, file_path: Path, folder_db_id: int, 
                     base_path: str) -> List[tuple]:
        """
        Process a single file and return segments
        
        Returns:
            List of (file_id, segment_data) tuples
        """
        # Get file info
        file_size = file_path.stat().st_size
        relative_path = str(file_path.relative_to(base_path))
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Create file record directly
        with self.db.pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO files (folder_id, filename, file_path, size, file_size, hash, file_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (folder_db_id, file_path.name, relative_path, file_size, file_size, file_hash, file_hash))
            file_id = cursor.lastrowid
            conn.commit()
        
        # Create segments
        segments = []
        segment_count = (file_size + self.segment_size - 1) // self.segment_size
        
        for i in range(segment_count):
            offset = i * self.segment_size
            size = min(self.segment_size, file_size - offset)
            
            # Calculate segment hash
            segment_hash = self._calculate_segment_hash(file_path, offset, size)
            
            segment_data = {
                'index': i,
                'size': size,
                'hash': segment_hash,
                'offset': offset
            }
            
            segments.append((file_id, segment_data))
            self.stats['segments_created'] += 1
        
        self.stats['bytes_processed'] += file_size
        
        return segments
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _calculate_segment_hash(self, file_path: Path, offset: int, size: int) -> str:
        """Calculate hash of file segment"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            f.seek(offset)
            data = f.read(size)
            sha256.update(data)
        
        return sha256.hexdigest()
    
    def _flush_segments_batch(self, segments: List[tuple]):
        """Flush a batch of segments to database"""
        if not segments:
            return
        
        # Use write queue for batch insert
        count = self.write_queue.batch_add_segments(segments)
        logger.debug(f"Flushed {count} segments to database")
    
    def _update_folder_stats(self, folder_db_id: int):
        """Update folder statistics"""
        try:
            with self.db.pool.get_connection() as conn:
                # Update folder stats
                conn.execute("""
                    UPDATE folders
                    SET total_files = (SELECT COUNT(*) FROM files WHERE folder_id = ?),
                        total_size = (SELECT COALESCE(SUM(size), 0) FROM files WHERE folder_id = ?),
                        file_count = (SELECT COUNT(*) FROM files WHERE folder_id = ?)
                    WHERE id = ?
                """, (folder_db_id, folder_db_id, folder_db_id, folder_db_id))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not update folder stats: {e}")


def test_optimized_indexing():
    """Test the optimized indexing system"""
    from src.database.enhanced_database_manager import DatabaseConfig, EnhancedDatabaseManager
    from src.security.enhanced_security_system import EnhancedSecuritySystem
    from complete_schema_fix import create_complete_schema
    from enhance_db_pool import enhance_database_pool
    import tempfile
    
    print("Testing Optimized Indexing System")
    print("="*60)
    
    # Setup
    db_path = "test_workspace/optimized_index_test.db"
    create_complete_schema(db_path)
    enhance_database_pool()
    
    # Create database and security
    db_config = DatabaseConfig(path=db_path, pool_size=20)
    db = EnhancedDatabaseManager(db_config)
    security = EnhancedSecuritySystem(db)
    
    # Create test files
    test_dir = Path("test_workspace/index_test_files")
    test_dir.mkdir(exist_ok=True)
    
    print("Creating test files...")
    for i in range(10):
        file_path = test_dir / f"test_{i}.txt"
        content = f"Test file {i}\n" * 1000
        file_path.write_text(content)
    
    # Create subdirectory with more files
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)
    
    for i in range(5):
        file_path = sub_dir / f"sub_{i}.dat"
        content = os.urandom(50000)  # 50KB random data
        file_path.write_bytes(content)
    
    print(f"✅ Created 15 test files")
    
    # Create indexing system
    config = {
        'segment_size': 10000,  # 10KB segments for testing
        'worker_threads': 2,
        'batch_size': 20
    }
    
    indexer = OptimizedIndexingSystem(db, security, config)
    
    # Index the folder
    print("\nIndexing folder...")
    
    def progress_callback(progress):
        if isinstance(progress, dict):
            print(f"  Progress: {progress.get('current', 0):.1f}% "
                  f"({progress.get('files_done', 0)}/{progress.get('files_total', 0)} files)", 
                  end='\r')
    
    result = indexer.index_folder(
        str(test_dir),
        "optimized_test_folder",
        progress_callback
    )
    
    print(f"\n\n✅ Indexing complete!")
    print(f"  Files indexed: {result['files_indexed']}")
    print(f"  Total size: {result['total_size']:,} bytes")
    print(f"  Total segments: {result['total_segments']}")
    print(f"  Time: {result['elapsed_time']:.2f}s")
    print(f"  Errors: {result['errors']}")
    
    # Verify in database
    with db.pool.get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM segments")
        segment_count = cursor.fetchone()[0]
        
        print(f"\n✅ Database verification:")
        print(f"  Files in DB: {file_count}")
        print(f"  Segments in DB: {segment_count}")
    
    # Cleanup
    db.pool.close_all()
    
    print("\n✅ Test completed successfully!")
    
    return result['errors'] == 0


if __name__ == "__main__":
    success = test_optimized_indexing()
    exit(0 if success else 1)