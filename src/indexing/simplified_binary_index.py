#!/usr/bin/env python3
"""
Simplified Binary Index System for UsenetSync
Uses optimized binary format but keeps index as single file
Perfect for datasets up to 20TB with millions of files
"""

import struct
import zlib
import io
import os
import time
import hashlib
import json
import base64
from typing import List, Dict, Optional, BinaryIO, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """File information"""
    path: str
    size: int
    hash: str
    modified: int
    segments: int

class SimplifiedBinaryIndex:
    """
    Optimized binary index system - single file approach
    Handles millions of files efficiently while maintaining simplicity
    """
    
    def __init__(self, folder_id: str):
        self.folder_id = folder_id
        self.version = 2  # Version 2: Single binary index
        self.logger = logging.getLogger(__name__)
        
    def create_index_from_folder(self, folder_path: str, progress_callback=None) -> bytes:
        """
        Create complete binary index from folder scan
        Returns compressed binary index ready for upload
        """
        self.logger.info(f"Creating optimized binary index for: {folder_path}")
        
        # Scan folder
        scan_result = self._scan_folder(folder_path, progress_callback)
        
        # Create binary index
        binary_index = self._create_binary_index(scan_result)
        
        # Compress with maximum compression
        compressed = zlib.compress(binary_index, level=9)
        
        # Statistics
        self.logger.info(f"Index Statistics:")
        self.logger.info(f"  Files: {len(scan_result['files']):,}")
        self.logger.info(f"  Folders: {len(scan_result['folders']):,}")
        self.logger.info(f"  Total size: {scan_result['total_size']:,} bytes")
        self.logger.info(f"  Raw index: {len(binary_index):,} bytes")
        self.logger.info(f"  Compressed: {len(compressed):,} bytes")
        self.logger.info(f"  Compression ratio: {len(compressed)/len(binary_index)*100:.1f}%")
        self.logger.info(f"  Bytes per file: {len(compressed)/len(scan_result['files']):.1f}")
        
        return compressed
        
    def _scan_folder(self, folder_path: str, progress_callback=None) -> Dict:
        """Scan folder and collect all metadata"""
        result = {
            'base_path': folder_path,
            'folders': {},
            'files': [],
            'total_size': 0,
            'scan_time': time.time()
        }
        
        file_count = 0
        
        for root, dirs, files in os.walk(folder_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            rel_path = os.path.relpath(root, folder_path)
            if rel_path == '.':
                rel_path = ''
                
            # Track folder
            result['folders'][rel_path] = {
                'name': os.path.basename(root) or os.path.basename(folder_path),
                'file_count': len(files),
                'subfolder_count': len(dirs)
            }
            
            # Process files
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, filename)
                rel_file_path = os.path.join(rel_path, filename).replace('\\', '/')
                
                try:
                    stat = os.stat(file_path)
                    
                    # Skip empty files
                    if stat.st_size == 0:
                        continue
                    
                    # Fast hash for large files
                    file_hash = self._calculate_file_hash(file_path, stat.st_size)
                    
                    # Calculate segments
                    segment_size = 768_000  # 750KB
                    num_segments = (stat.st_size + segment_size - 1) // segment_size
                    
                    result['files'].append(FileInfo(
                        path=rel_file_path,
                        size=stat.st_size,
                        hash=file_hash,
                        modified=int(stat.st_mtime),
                        segments=num_segments
                    ))
                    
                    result['total_size'] += stat.st_size
                    file_count += 1
                    
                    if progress_callback and file_count % 100 == 0:
                        progress_callback({
                            'phase': 'scanning',
                            'files': file_count
                        })
                        
                except Exception as e:
                    logger.warning(f"Error scanning {file_path}: {e}")
                    
        result['scan_time'] = time.time() - result['scan_time']
        self.logger.info(f"Scan complete in {result['scan_time']:.1f}s")
        
        return result
        
    def _calculate_file_hash(self, file_path: str, file_size: int) -> str:
        """Fast file hashing"""
        if file_size < 1024 * 1024:  # < 1MB
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        else:
            # Sample-based for large files
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # First 64KB
                hasher.update(f.read(65536))
                # Middle 64KB
                f.seek(file_size // 2)
                hasher.update(f.read(65536))
                # Last 64KB
                if file_size > 131072:
                    f.seek(-65536, 2)
                    hasher.update(f.read(65536))
                # Include size
                hasher.update(str(file_size).encode())
            return hasher.hexdigest()
            
    def _create_binary_index(self, scan_result: Dict) -> bytes:
        """Create optimized binary index"""
        buffer = io.BytesIO()
        
        # Header
        buffer.write(b'USBI')  # UsenetSync Binary Index
        buffer.write(struct.pack('<H', self.version))
        buffer.write(self.folder_id.encode('utf-8')[:32].ljust(32, b'\0'))
        buffer.write(struct.pack('<Q', int(time.time())))
        
        # Statistics
        buffer.write(struct.pack('<I', len(scan_result['folders'])))
        buffer.write(struct.pack('<I', len(scan_result['files'])))
        buffer.write(struct.pack('<Q', scan_result['total_size']))
        
        # Build path dictionary for deduplication
        path_components = set()
        for file in scan_result['files']:
            path_components.update(file.path.split('/'))
        for folder in scan_result['folders']:
            if folder:
                path_components.update(folder.split('/'))
                
        # Write path dictionary
        path_dict = {comp: idx for idx, comp in enumerate(sorted(path_components))}
        buffer.write(struct.pack('<I', len(path_dict)))
        
        for component in sorted(path_components):
            comp_bytes = component.encode('utf-8')
            buffer.write(struct.pack('<H', len(comp_bytes)))
            buffer.write(comp_bytes)
            
        # Write folders
        for path, info in sorted(scan_result['folders'].items()):
            if path:
                parts = path.split('/')
                buffer.write(struct.pack('<B', len(parts)))
                for part in parts:
                    buffer.write(struct.pack('<H', path_dict[part]))
            else:
                buffer.write(struct.pack('<B', 0))  # Root folder
                
            buffer.write(struct.pack('<I', info['file_count']))
            buffer.write(struct.pack('<I', info['subfolder_count']))
            
        # Write files
        for file in scan_result['files']:
            # Path using dictionary indices
            parts = file.path.split('/')
            buffer.write(struct.pack('<B', len(parts)))
            for part in parts:
                buffer.write(struct.pack('<H', path_dict[part]))
                
            # File metadata
            self._write_varint(buffer, file.size)
            buffer.write(bytes.fromhex(file.hash))  # 32 bytes
            self._write_varint(buffer, file.modified)
            self._write_varint(buffer, file.segments)
            
        return buffer.getvalue()
        
    def _write_varint(self, buffer: BinaryIO, value: int):
        """Write variable-length integer for space efficiency"""
        while value >= 0x80:
            buffer.write(struct.pack('B', (value & 0x7F) | 0x80))
            value >>= 7
        buffer.write(struct.pack('B', value & 0x7F))
        
    def parse_binary_index(self, compressed_data: bytes) -> Dict:
        """Parse binary index back to usable format"""
        # Decompress
        binary_data = zlib.decompress(compressed_data)
        buffer = io.BytesIO(binary_data)
        
        # Read header
        magic = buffer.read(4)
        if magic != b'USBI':
            raise ValueError("Invalid index format")
            
        version = struct.unpack('<H', buffer.read(2))[0]
        folder_id = buffer.read(32).rstrip(b'\0').decode('utf-8')
        timestamp = struct.unpack('<Q', buffer.read(8))[0]
        
        # Read statistics
        folder_count = struct.unpack('<I', buffer.read(4))[0]
        file_count = struct.unpack('<I', buffer.read(4))[0]
        total_size = struct.unpack('<Q', buffer.read(8))[0]
        
        # Read path dictionary
        dict_size = struct.unpack('<I', buffer.read(4))[0]
        path_dict = {}
        
        for i in range(dict_size):
            comp_len = struct.unpack('<H', buffer.read(2))[0]
            component = buffer.read(comp_len).decode('utf-8')
            path_dict[i] = component
            
        # Read folders
        folders = {}
        for _ in range(folder_count):
            part_count = struct.unpack('<B', buffer.read(1))[0]
            
            if part_count > 0:
                parts = []
                for _ in range(part_count):
                    idx = struct.unpack('<H', buffer.read(2))[0]
                    parts.append(path_dict[idx])
                path = '/'.join(parts)
            else:
                path = ''
                
            file_count_folder = struct.unpack('<I', buffer.read(4))[0]
            subfolder_count = struct.unpack('<I', buffer.read(4))[0]
            
            folders[path] = {
                'file_count': file_count_folder,
                'subfolder_count': subfolder_count
            }
            
        # Read files
        files = []
        for _ in range(file_count):
            # Read path
            part_count = struct.unpack('<B', buffer.read(1))[0]
            parts = []
            for _ in range(part_count):
                idx = struct.unpack('<H', buffer.read(2))[0]
                parts.append(path_dict[idx])
            path = '/'.join(parts)
            
            # Read metadata
            size = self._read_varint(buffer)
            hash_bytes = buffer.read(32)
            file_hash = hash_bytes.hex()
            modified = self._read_varint(buffer)
            segments = self._read_varint(buffer)
            
            files.append({
                'path': path,
                'size': size,
                'hash': file_hash,
                'modified': modified,
                'segments': segments
            })
            
        return {
            'version': version,
            'folder_id': folder_id,
            'timestamp': timestamp,
            'folders': folders,
            'files': files,
            'total_size': total_size
        }
        
    def _read_varint(self, buffer: BinaryIO) -> int:
        """Read variable-length integer"""
        value = 0
        shift = 0
        
        while True:
            byte = buffer.read(1)[0]
            value |= (byte & 0x7F) << shift
            if byte & 0x80 == 0:
                break
            shift += 7
            
        return value
        
    def create_folder_structure_index(self, folder_structure: Dict) -> bytes:
        """
        Create index from pre-built folder structure
        Used when index data comes from database
        """
        scan_result = {
            'base_path': folder_structure.get('base_path', ''),
            'folders': folder_structure.get('folders', {}),
            'files': [],
            'total_size': 0
        }
        
        # Convert file data to FileInfo objects
        for file_data in folder_structure.get('files', []):
            scan_result['files'].append(FileInfo(
                path=file_data['path'],
                size=file_data['size'],
                hash=file_data['hash'],
                modified=file_data.get('modified', int(time.time())),
                segments=file_data.get('segments', 1)
            ))
            scan_result['total_size'] += file_data['size']
            
        # Create binary index
        binary_index = self._create_binary_index(scan_result)
        
        # Compress
        return zlib.compress(binary_index, level=9)
        
    def merge_indices(self, primary_index: bytes, secondary_index: bytes) -> bytes:
        """
        Merge two binary indices
        Useful for combining multiple folder indices
        """
        # Parse both indices
        primary = self.parse_binary_index(primary_index)
        secondary = self.parse_binary_index(secondary_index)
        
        # Merge folders
        merged_folders = primary['folders'].copy()
        for path, info in secondary['folders'].items():
            if path in merged_folders:
                # Combine counts
                merged_folders[path]['file_count'] += info['file_count']
                merged_folders[path]['subfolder_count'] = max(
                    merged_folders[path]['subfolder_count'],
                    info['subfolder_count']
                )
            else:
                merged_folders[path] = info
                
        # Merge files (avoid duplicates by path)
        merged_files = {f['path']: f for f in primary['files']}
        for file in secondary['files']:
            if file['path'] not in merged_files:
                merged_files[file['path']] = file
                
        # Create merged structure
        merged_structure = {
            'base_path': primary.get('base_path', ''),
            'folders': merged_folders,
            'files': list(merged_files.values())
        }
        
        # Create new index
        return self.create_folder_structure_index(merged_structure)
        
    def get_index_summary(self, compressed_index: bytes) -> Dict:
        """
        Get summary of index without full parsing
        Useful for quick inspection
        """
        # Decompress just the header
        binary_data = zlib.decompress(compressed_index)
        buffer = io.BytesIO(binary_data[:64])  # Read first 64 bytes
        
        # Read header
        magic = buffer.read(4)
        if magic != b'USBI':
            raise ValueError("Invalid index format")
            
        version = struct.unpack('<H', buffer.read(2))[0]
        folder_id = buffer.read(32).rstrip(b'\0').decode('utf-8')
        timestamp = struct.unpack('<Q', buffer.read(8))[0]
        
        # Read statistics
        folder_count = struct.unpack('<I', buffer.read(4))[0]
        file_count = struct.unpack('<I', buffer.read(4))[0]
        total_size = struct.unpack('<Q', buffer.read(8))[0]
        
        return {
            'version': version,
            'folder_id': folder_id,
            'created': datetime.fromtimestamp(timestamp).isoformat(),
            'folders': folder_count,
            'files': file_count,
            'total_size': total_size,
            'compressed_size': len(compressed_index),
            'compression_ratio': len(compressed_index) / len(binary_data) * 100
        }
    
    def create_index_from_database(self, files: List[Dict], segments: List[Dict]) -> bytes:
        """
        Create binary index from database data (files and segments)
        This is used when publishing folders that are already indexed
        """
        self.logger.info(f"Creating binary index from database data")
        
        # Convert database format to scan_result format
        from dataclasses import dataclass
        
        @dataclass
        class FileObj:
            """Wrapper to make dict look like object"""
            path: str
            size: int
            hash: str
            modified: int
            segments: int
            
        # Convert dicts to objects
        file_objects = []
        for f in files:
            # Ensure hash is valid hex string (64 chars for SHA256)
            file_hash = f.get('hash', f.get('file_hash', ''))
            if not file_hash or len(file_hash) != 64:
                # Generate a placeholder hash if missing
                import hashlib
                file_path = f.get('path', f.get('file_path', 'unknown'))
                file_hash = hashlib.sha256(file_path.encode()).hexdigest()
            
            file_objects.append(FileObj(
                path=f.get('path', f.get('file_path', '')),
                size=f.get('size', f.get('file_size', 0)),
                hash=file_hash,
                modified=f.get('modified', int(time.time())),
                segments=f.get('segments', 1)
            ))
        
        # Build folder structure from file paths
        folders = {}
        for f in file_objects:
            # Extract folder path from file path
            if '/' in f.path:
                folder_path = '/'.join(f.path.split('/')[:-1])
                if folder_path not in folders:
                    folders[folder_path] = {'file_count': 0, 'subfolder_count': 0}
                folders[folder_path]['file_count'] += 1
        
        # Add root folder if there are files in root
        root_files = [f for f in file_objects if '/' not in f.path]
        if root_files:
            folders[''] = {'file_count': len(root_files), 'subfolder_count': len(set(p.split('/')[0] for p in folders.keys() if p))}
        
        # Build scan result
        scan_result = {
            'files': file_objects,
            'folders': folders,
            'total_size': sum(f.size for f in file_objects),
            'total_files': len(file_objects)
        }
        
        # Create binary index
        binary_index = self._create_binary_index(scan_result)
        
        # Compress with maximum compression
        compressed = zlib.compress(binary_index, level=9)
        
        self.logger.info(f"Index created: {len(files)} files, {len(compressed):,} bytes compressed")
        
        return compressed