#!/usr/bin/env python3
"""
Unified Scanner Module - File system scanning with performance optimization
Production-ready with parallel processing and streaming
"""

import os
import hashlib
import mimetypes
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Generator, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """File information"""
    path: str
    name: str
    size: int
    modified: datetime
    hash: Optional[str] = None
    mime_type: Optional[str] = None
    is_directory: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['modified'] = self.modified.isoformat()
        return data

class UnifiedScanner:
    """
    Unified file system scanner
    Handles recursive scanning with performance optimization
    """
    
    def __init__(self, db, config=None):
        """Initialize scanner"""
        self.db = db
        self.config = config or {}
        self.worker_threads = self.config.get('worker_threads', 8)
        self.batch_size = self.config.get('batch_size', 100)
        self.buffer_size = self.config.get('buffer_size', 65536)
        self.skip_patterns = self.config.get('skip_patterns', [
            '.*', '__pycache__', 'node_modules', '.git', '.svn'
        ])
        self._scan_cache = {}
        self._hash_cache = {}
    
    def scan_folder(self, folder_path: str, recursive: bool = True,
                   calculate_hashes: bool = True,
                   progress_callback: Optional[callable] = None) -> Generator[FileInfo, None, None]:
        """
        Scan folder and yield file information
        
        Args:
            folder_path: Path to folder to scan
            recursive: Whether to scan recursively
            calculate_hashes: Whether to calculate file hashes
            progress_callback: Optional progress callback
        
        Yields:
            FileInfo objects
        """
        folder_path = Path(folder_path).resolve()
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Not a directory: {folder_path}")
        
        logger.info(f"Scanning folder: {folder_path}")
        
        # Count total files for progress
        total_files = self._count_files(folder_path, recursive) if progress_callback else 0
        files_processed = 0
        
        # Scan with parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.worker_threads) as executor:
            # Submit file processing tasks
            futures = []
            
            for file_path in self._walk_folder(folder_path, recursive):
                if self._should_skip(file_path):
                    continue
                
                future = executor.submit(
                    self._process_file,
                    file_path,
                    folder_path,
                    calculate_hashes
                )
                futures.append(future)
                
                # Process in batches
                if len(futures) >= self.batch_size:
                    for future in concurrent.futures.as_completed(futures[:self.batch_size]):
                        try:
                            file_info = future.result()
                            if file_info:
                                yield file_info
                                
                                files_processed += 1
                                if progress_callback:
                                    progress_callback(files_processed, total_files)
                        except Exception as e:
                            logger.error(f"Error processing file: {e}")
                    
                    futures = futures[self.batch_size:]
            
            # Process remaining futures
            for future in concurrent.futures.as_completed(futures):
                try:
                    file_info = future.result()
                    if file_info:
                        yield file_info
                        
                        files_processed += 1
                        if progress_callback:
                            progress_callback(files_processed, total_files)
                except Exception as e:
                    logger.error(f"Error processing file: {e}")
        
        logger.info(f"Scanned {files_processed} files")
    
    def _walk_folder(self, folder_path: Path, recursive: bool) -> Generator[Path, None, None]:
        """Walk folder and yield file paths"""
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                # Filter directories
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                
                root_path = Path(root)
                
                # Yield directories
                for dir_name in dirs:
                    yield root_path / dir_name
                
                # Yield files
                for file_name in files:
                    yield root_path / file_name
        else:
            # Non-recursive scan
            for item in folder_path.iterdir():
                if not self._should_skip(item):
                    yield item
    
    def _process_file(self, file_path: Path, base_path: Path,
                     calculate_hash: bool) -> Optional[FileInfo]:
        """Process single file"""
        try:
            # Get file stats
            stat = file_path.stat()
            
            # Create file info
            file_info = FileInfo(
                path=str(file_path.relative_to(base_path)),
                name=file_path.name,
                size=stat.st_size if file_path.is_file() else 0,
                modified=datetime.fromtimestamp(stat.st_mtime),
                is_directory=file_path.is_dir()
            )
            
            if file_path.is_file():
                # Get MIME type
                file_info.mime_type = mimetypes.guess_type(str(file_path))[0]
                
                # Calculate hash if requested
                if calculate_hash and stat.st_size > 0:
                    file_info.hash = self._calculate_hash(file_path)
            
            return file_info
            
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
            return None
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        # Check cache
        cache_key = f"{file_path}:{file_path.stat().st_mtime}"
        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]
        
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.buffer_size):
                    sha256.update(chunk)
            
            hash_value = sha256.hexdigest()
            
            # Cache result
            self._hash_cache[cache_key] = hash_value
            
            return hash_value
            
        except Exception as e:
            logger.warning(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _count_files(self, folder_path: Path, recursive: bool) -> int:
        """Count total files in folder"""
        count = 0
        
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # Filter directories
                    dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                    count += len(files) + len(dirs)
            else:
                count = len(list(folder_path.iterdir()))
        except:
            pass
        
        return count
    
    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped"""
        name = path.name
        
        # Check skip patterns
        for pattern in self.skip_patterns:
            if pattern.startswith('.') and name == pattern:
                return True
            elif pattern in name:
                return True
        
        return False
    
    def _should_skip_dir(self, dir_name: str) -> bool:
        """Check if directory should be skipped"""
        for pattern in self.skip_patterns:
            if pattern == dir_name or pattern in dir_name:
                return True
        return False
    
    def scan_changes(self, folder_path: str, last_scan: Optional[datetime] = None) -> Dict[str, List[FileInfo]]:
        """
        Scan for changes since last scan
        
        Args:
            folder_path: Folder to scan
            last_scan: Last scan timestamp
        
        Returns:
            Dictionary with 'added', 'modified', 'deleted' lists
        """
        changes = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        current_files = {}
        
        # Scan current state
        for file_info in self.scan_folder(folder_path):
            current_files[file_info.path] = file_info
            
            if last_scan:
                # Check if file is new or modified
                if file_info.modified > last_scan:
                    # Check if exists in database
                    existing = self.db.fetch_one(
                        "SELECT hash FROM files WHERE path = ?",
                        (file_info.path,)
                    )
                    
                    if existing:
                        if existing['hash'] != file_info.hash:
                            changes['modified'].append(file_info)
                    else:
                        changes['added'].append(file_info)
            else:
                # All files are new
                changes['added'].append(file_info)
        
        # Check for deleted files
        if last_scan:
            db_files = self.db.fetch_all(
                "SELECT path FROM files WHERE folder_id IN (SELECT folder_id FROM folders WHERE path = ?)",
                (folder_path,)
            )
            
            for db_file in db_files:
                if db_file['path'] not in current_files:
                    changes['deleted'].append(FileInfo(
                        path=db_file['path'],
                        name=Path(db_file['path']).name,
                        size=0,
                        modified=datetime.now(),
                        is_directory=False
                    ))
        
        return changes
    
    def calculate_folder_hash(self, folder_path: str) -> str:
        """
        Calculate hash of entire folder contents
        
        Args:
            folder_path: Folder to hash
        
        Returns:
            Combined hash of all files
        """
        hasher = hashlib.sha256()
        
        # Get all files sorted by path
        files = []
        for file_info in self.scan_folder(folder_path):
            if not file_info.is_directory:
                files.append(file_info)
        
        files.sort(key=lambda f: f.path)
        
        # Hash file paths and contents
        for file_info in files:
            hasher.update(file_info.path.encode('utf-8'))
            hasher.update(str(file_info.size).encode('utf-8'))
            if file_info.hash:
                hasher.update(file_info.hash.encode('utf-8'))
        
        return hasher.hexdigest()
    
    def get_folder_size(self, folder_path: str) -> Tuple[int, int]:
        """
        Get total size and file count of folder
        
        Args:
            folder_path: Folder to analyze
        
        Returns:
            Tuple of (total_size, file_count)
        """
        total_size = 0
        file_count = 0
        
        for file_info in self.scan_folder(folder_path, calculate_hashes=False):
            if not file_info.is_directory:
                total_size += file_info.size
                file_count += 1
        
        return total_size, file_count
    
    def find_duplicates(self, folder_path: str) -> Dict[str, List[str]]:
        """
        Find duplicate files by hash
        
        Args:
            folder_path: Folder to scan
        
        Returns:
            Dictionary of hash -> list of file paths
        """
        hash_map = {}
        
        for file_info in self.scan_folder(folder_path):
            if file_info.hash and not file_info.is_directory:
                if file_info.hash not in hash_map:
                    hash_map[file_info.hash] = []
                hash_map[file_info.hash].append(file_info.path)
        
        # Return only duplicates
        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    
    def export_index(self, folder_path: str, output_file: str):
        """
        Export folder index to file
        
        Args:
            folder_path: Folder to index
            output_file: Output file path
        """
        import json
        
        index_data = {
            'folder': folder_path,
            'indexed_at': datetime.now().isoformat(),
            'files': []
        }
        
        for file_info in self.scan_folder(folder_path):
            index_data['files'].append(file_info.to_dict())
        
        with open(output_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Exported index to {output_file}")