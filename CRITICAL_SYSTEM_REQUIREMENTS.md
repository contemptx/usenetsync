# Critical System Requirements for Unification

## 1. Redundancy System

### Current Implementation
- **Redundancy Level**: Configurable number of copies (e.g., redundancy_level=3 means 3 copies)
- **Unique Articles**: Each redundant copy is a UNIQUE article with different:
  - Message ID
  - Subject (different random string)
  - Potentially different newsgroups for distribution
- **NOT duplicates**: This is NOT simple duplication but intelligent redundancy

### Example Implementation
```python
def create_redundant_segments(segment_data: bytes, redundancy_level: int):
    """Create unique redundant copies of segment"""
    segments = []
    for redundancy_index in range(redundancy_level):
        # Each copy gets unique identifiers
        segment = {
            'data': segment_data,
            'redundancy_index': redundancy_index,
            'subject': generate_random_subject(),  # UNIQUE for each copy
            'message_id': generate_message_id(),   # UNIQUE for each copy
            'newsgroup': select_newsgroup(redundancy_index)  # Can vary
        }
        segments.append(segment)
    return segments
```

### Database Schema
```sql
CREATE TABLE segments (
    segment_id TEXT,
    redundancy_index INTEGER,  -- 0 = original, 1+ = redundant copies
    message_id TEXT UNIQUE,    -- Each redundant copy has unique message_id
    subject TEXT UNIQUE,       -- Each redundant copy has unique subject
    -- All redundant copies share same segment_id but different redundancy_index
);
```

## 2. Segment Packaging System

### Purpose
Pack multiple small files into single 750KB articles for efficiency

### Current Implementation
```python
class SegmentPackingSystem:
    def __init__(self, target_size: int = 768000):  # 750KB
        self.target_size = target_size
        self.buffer = SegmentBuffer(max_size=target_size)
    
    def pack_files(self, small_files: List[FileData]):
        """Pack small files together into target_size segments"""
        packed_segments = []
        current_pack = []
        current_size = 0
        
        for file in small_files:
            if current_size + file.size > self.target_size:
                # Create packed segment
                packed_segments.append(self.create_packed_segment(current_pack))
                current_pack = [file]
                current_size = file.size
            else:
                current_pack.append(file)
                current_size += file.size
        
        # Handle remaining files
        if current_pack:
            packed_segments.append(self.create_packed_segment(current_pack))
```

### Benefits
- Reduces number of articles for small files
- Optimizes Usenet server resources
- Improves download efficiency
- Maintains 750KB standard article size

## 3. Dual Database Support

### SQLite
- Default for small to medium datasets
- No installation required
- Good for up to ~100GB datasets
- Single file database

### PostgreSQL
- Required for large datasets (100GB+)
- Auto-installation via GUI
- Sharding support for 20TB+ datasets
- Better concurrent access

### Implementation
```python
class DatabaseSelector:
    @staticmethod
    def get_database_manager(config):
        if config.get('database_type') == 'postgresql':
            return PostgreSQLManager(config)
        else:
            return SQLiteManager(config)  # Default

class UnifiedDatabaseInterface:
    """Common interface for both databases"""
    def execute(self, query: str, params: tuple):
        # Handles SQL dialect differences
        if self.is_postgresql:
            query = self.convert_to_postgresql(query)
        return self.connection.execute(query, params)
```

### Auto-Installation (GUI)
```python
async def auto_install_postgresql():
    """GUI function to auto-install PostgreSQL"""
    if platform.system() == 'Windows':
        # Download PostgreSQL installer
        # Run silent installation
        # Configure for UsenetSync
    elif platform.system() == 'Linux':
        # Use package manager (apt/yum)
        # Configure postgresql.conf
        # Setup user and database
```

## 4. Large Dataset Support

### Memory Management
**CRITICAL**: Never load entire datasets into memory

### Streaming Architecture
```python
class LargeDatasetHandler:
    def index_folder(self, path: str, size_estimate: int):
        """Stream-based indexing for large datasets"""
        if size_estimate > 1_000_000_000_000:  # 1TB+
            return self.index_with_streaming(path)
        else:
            return self.index_standard(path)
    
    def index_with_streaming(self, path: str):
        """Process files in chunks, never loading all into memory"""
        chunk_size = 1000  # Process 1000 files at a time
        
        for file_chunk in self.iterate_files_chunked(path, chunk_size):
            # Process chunk
            self.process_chunk(file_chunk)
            # Write to database
            self.db.bulk_insert(file_chunk)
            # Clear memory
            del file_chunk
            gc.collect()
```

### Database Optimizations for Large Datasets
```python
# PostgreSQL sharding for 20TB+
class ShardedPostgreSQLManager:
    def __init__(self, shard_count: int = 16):
        self.shard_count = shard_count
        
    def get_shard(self, file_id: str):
        """Distribute data across shards"""
        hash_val = hashlib.md5(file_id.encode()).hexdigest()
        shard_id = int(hash_val[:2], 16) % self.shard_count
        return f"shard_{shard_id}"
```

### Progress Tracking for Large Operations
```python
class ProgressTracker:
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.processed = 0
        self.checkpoint_interval = 100_000_000  # 100MB
        
    def update(self, bytes_processed: int):
        self.processed += bytes_processed
        if self.processed % self.checkpoint_interval == 0:
            self.save_checkpoint()  # Allow resume
```

## 5. Usenet One-Way Communication

### Key Principles
- **Upload Only**: Data goes TO Usenet, never modified after posting
- **Immutable Storage**: Once posted, articles cannot be changed
- **Local Authentication**: All auth/encryption happens client-side
- **No Server Interaction**: Beyond basic NNTP commands

### Security Model
```python
class UsenetSecurityModel:
    """All security is client-side"""
    
    def publish_share(self, data, access_type):
        if access_type == 'private':
            # Generate access commitments locally
            commitments = self.generate_access_commitments(authorized_users)
            # Encrypt data with keys only authorized users can derive
            encrypted = self.encrypt_for_users(data, authorized_users)
        elif access_type == 'protected':
            # Password-based encryption, all client-side
            encrypted = self.encrypt_with_password(data, password)
        else:  # public
            # Still encrypted but key is in access string
            key = generate_random_key()
            encrypted = self.encrypt_with_key(data, key)
            # Key included in access string
        
        # Post encrypted data to Usenet
        self.post_to_usenet(encrypted)
        # No further server interaction needed
```

## 6. Encrypted Storage of Usenet Locations

### Current Implementation
Message IDs and subjects are encrypted in local database:

```python
class SecureStorageManager:
    def store_segment_location(self, segment_id: str, message_id: str, subject: str):
        """Store Usenet location encrypted"""
        # Encrypt sensitive data
        encrypted_message_id = self.encrypt(message_id, self.storage_key)
        encrypted_subject = self.encrypt(subject, self.storage_key)
        
        # Store encrypted
        self.db.execute("""
            INSERT INTO segments (segment_id, message_id, subject)
            VALUES (?, ?, ?)
        """, (segment_id, encrypted_message_id, encrypted_subject))
    
    def retrieve_segment_location(self, segment_id: str):
        """Retrieve and decrypt location"""
        row = self.db.fetchone("""
            SELECT message_id, subject FROM segments WHERE segment_id = ?
        """, (segment_id,))
        
        # Decrypt for use
        message_id = self.decrypt(row['message_id'], self.storage_key)
        subject = self.decrypt(row['subject'], self.storage_key)
        return message_id, subject
```

### Benefits
- Prevents casual inspection of Usenet locations
- Protects against database dumps
- Additional security layer

## 7. Resource Management

### Memory Constraints
```python
class ResourceManager:
    def __init__(self):
        self.max_memory = psutil.virtual_memory().total * 0.5  # Use max 50% RAM
        self.current_usage = 0
        
    def can_load(self, size_bytes: int) -> bool:
        """Check if we can load data without exceeding limits"""
        return (self.current_usage + size_bytes) < self.max_memory
    
    def process_large_file(self, file_path: str, file_size: int):
        """Process file in chunks if too large"""
        if file_size > self.max_memory:
            # Stream processing
            chunk_size = min(100_000_000, self.max_memory // 10)  # 100MB or 10% of max
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.process_chunk(chunk)
                    del chunk  # Explicit cleanup
        else:
            # Can load entire file
            with open(file_path, 'rb') as f:
                data = f.read()
                self.process_data(data)
```

### Batch Processing
```python
def process_20tb_dataset(dataset_path: str):
    """Example of processing 20TB dataset"""
    total_files = count_files(dataset_path)
    batch_size = 10000  # Process 10k files at a time
    
    for batch_num in range(0, total_files, batch_size):
        # Process batch
        files = get_files_batch(dataset_path, batch_num, batch_size)
        
        # Index files
        index_results = index_files(files)
        
        # Create segments (streaming)
        for file in files:
            create_segments_streaming(file)
        
        # Upload segments (queued)
        queue_segments_for_upload(index_results)
        
        # Clear memory
        del files, index_results
        gc.collect()
        
        # Save checkpoint for resume capability
        save_checkpoint(batch_num)
```

## 8. Existing Functionality Preservation

### Critical Components That Work
1. **VersionedCoreIndexSystem**: Handles file versioning and change detection
2. **SimplifiedBinaryIndex**: Optimized for large datasets with compression
3. **EnhancedUploadSystem**: Queue management, retry logic, worker pools
4. **EnhancedDownloadSystem**: Resume capability, parallel downloads
5. **SegmentPackingSystem**: Small file optimization
6. **ProductionNNTPClient**: Connection pooling, retry logic
7. **EnhancedSecuritySystem**: Two-layer subjects, zero-knowledge proofs

### What Must Be Preserved
- Redundancy with unique articles
- Segment packing for small files
- Dual database support (SQLite + PostgreSQL)
- Streaming for large datasets
- Resource management
- Encrypted storage of locations
- All security features

## Implementation Priorities

### Phase 1: Core Unification
- Merge indexing systems while preserving both approaches
- Unify database interface for SQLite/PostgreSQL
- Preserve redundancy system

### Phase 2: Optimization
- Ensure segment packing works with unified system
- Verify streaming for large datasets
- Test resource management

### Phase 3: Security
- Maintain encrypted storage
- Preserve two-layer subjects
- Keep client-side authentication

### Phase 4: Testing
- Test with 20TB dataset
- Verify redundancy creates unique articles
- Confirm resource usage stays within limits

## Testing Requirements

### Large Dataset Test
```python
def test_20tb_dataset():
    """Test system can handle 20TB dataset"""
    # Create test dataset
    test_path = create_test_dataset(size_tb=20)
    
    # Monitor resources
    monitor = ResourceMonitor()
    monitor.start()
    
    # Index dataset
    indexer = UnifiedIndexer(streaming=True)
    result = indexer.index_folder(test_path)
    
    # Verify
    assert result['files_indexed'] > 1_000_000
    assert monitor.max_memory_used < (psutil.virtual_memory().total * 0.6)
    assert monitor.no_crashes
```

### Redundancy Test
```python
def test_redundancy_unique_articles():
    """Verify redundant copies are unique articles"""
    segment_data = b"test data"
    redundancy_level = 3
    
    segments = create_redundant_segments(segment_data, redundancy_level)
    
    # Verify all unique
    message_ids = [s['message_id'] for s in segments]
    subjects = [s['subject'] for s in segments]
    
    assert len(set(message_ids)) == redundancy_level
    assert len(set(subjects)) == redundancy_level
    
    # Verify all can be retrieved independently
    for segment in segments:
        retrieved = nntp.retrieve_article(segment['message_id'])
        assert retrieved == segment_data
```

## 9. Folder/File Structure Preservation

### Critical Requirement
Usenet has NO concept of directories or folder structure - it only stores individual articles. The system MUST preserve and reconstruct the complete folder hierarchy.

### Current Implementation

#### During Indexing
```python
# Both indexing systems preserve relative paths
for root, dirs, files in os.walk(folder_path):
    rel_path = os.path.relpath(root, folder_path)
    for filename in files:
        file_path = os.path.join(root, filename)
        rel_file_path = os.path.join(rel_path, filename).replace('\\', '/')
        
        # Store with relative path preserved
        files[rel_file_path] = {
            'size': stat.st_size,
            'hash': file_hash,
            'path': rel_file_path  # CRITICAL: Preserve full relative path
        }
```

#### In the Index
```python
# Index stores complete folder structure
index_data = {
    'base_path': '/original/folder/path',
    'folder_name': 'MyFolder',
    'folders': {
        '': {'name': 'MyFolder', 'file_count': 10},
        'subfolder1': {'name': 'subfolder1', 'file_count': 5},
        'subfolder1/nested': {'name': 'nested', 'file_count': 3}
    },
    'files': [
        {
            'path': 'document.pdf',  # Root level file
            'size': 1024000,
            'hash': 'abc123...',
            'segments': [...]
        },
        {
            'path': 'subfolder1/image.jpg',  # Nested file
            'size': 2048000,
            'hash': 'def456...',
            'segments': [...]
        },
        {
            'path': 'subfolder1/nested/data.txt',  # Deeply nested
            'size': 512000,
            'hash': 'ghi789...',
            'segments': [...]
        }
    ]
}
```

#### During Download/Reconstruction
```python
def _complete_file_download(self, session, file_download):
    # Reconstruct complete path including folder structure
    file_download.final_path = os.path.join(
        session.destination_path,  # User's chosen destination
        session.folder_name,        # Original folder name
        file_download.file_path     # FULL relative path with subfolders
    )
    
    # Example: /downloads/MyFolder/subfolder1/nested/data.txt
    
    # Create all necessary directories
    os.makedirs(os.path.dirname(file_download.final_path), exist_ok=True)
    
    # Assemble file in correct location
    self.assembler.assemble_file(
        file_download.file_path,
        file_download.segment_count,
        file_download.temp_path,
        file_download.final_path  # Preserves full structure
    )
```

### Database Schema
```sql
CREATE TABLE files (
    file_id INTEGER PRIMARY KEY,
    folder_id INTEGER,
    file_path TEXT,  -- FULL relative path: 'subfolder/nested/file.txt'
    file_hash TEXT,
    file_size INTEGER,
    -- NOT just filename, but complete path within folder
);
```

### Testing Structure Preservation
```python
def test_folder_structure_preservation():
    # Create test structure
    test_folder = Path('/test/source')
    (test_folder / 'docs').mkdir(parents=True)
    (test_folder / 'docs' / 'nested').mkdir()
    (test_folder / 'images' / 'photos').mkdir(parents=True)
    
    # Create files at various levels
    (test_folder / 'readme.txt').write_text('root file')
    (test_folder / 'docs' / 'document.pdf').write_bytes(b'doc')
    (test_folder / 'docs' / 'nested' / 'data.csv').write_text('data')
    (test_folder / 'images' / 'photos' / 'pic.jpg').write_bytes(b'img')
    
    # Index and upload
    index_result = indexer.index_folder(test_folder)
    upload_result = uploader.upload_folder(folder_id)
    access_string = publisher.create_share(folder_id)
    
    # Download to new location
    download_path = Path('/test/destination')
    downloader.download_share(access_string, download_path)
    
    # Verify structure preserved
    assert (download_path / 'source' / 'readme.txt').exists()
    assert (download_path / 'source' / 'docs' / 'document.pdf').exists()
    assert (download_path / 'source' / 'docs' / 'nested' / 'data.csv').exists()
    assert (download_path / 'source' / 'images' / 'photos' / 'pic.jpg').exists()
    
    # Verify content
    assert (download_path / 'source' / 'readme.txt').read_text() == 'root file'
```

### Critical Points

1. **Relative Paths**: Always store relative paths, not absolute
2. **Path Separators**: Normalize to forward slashes for cross-platform
3. **Directory Creation**: Create all parent directories during download
4. **Empty Folders**: System tracks folder structure even if empty
5. **Deep Nesting**: Support arbitrary depth of folder nesting
6. **Special Characters**: Handle spaces and special chars in paths

### Implementation Requirements

- Index MUST capture complete folder hierarchy
- Database MUST store full relative paths
- Download MUST recreate exact structure
- Path separators MUST be normalized
- Empty directories SHOULD be preserved

## Conclusion

The unified system MUST preserve:
1. Redundancy as unique articles
2. Segment packing for efficiency
3. Dual database support
4. Large dataset streaming
5. Resource management
6. Encrypted location storage
7. One-way Usenet communication
8. Client-side authentication
9. **Complete folder/file structure preservation**

These are not optional features but core requirements for the system to function correctly with production Usenet servers and large datasets.