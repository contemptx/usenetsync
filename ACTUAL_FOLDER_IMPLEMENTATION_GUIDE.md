# UsenetSync Folder Management - Detailed Implementation Guide

## Core System Architecture (Based on Actual Code)

### Key Components We Actually Have:
1. **VersionedCoreIndexSystem** - Core indexing with versioning
2. **SimplifiedBinaryIndex** - Binary index for millions of files
3. **RedundancyLevel** (NOT PAR2) - Configurable redundancy (default: 2)
4. **PublishingSystem** - Publishes core index files (NOT NZB/torrent)
5. **EnhancedUploadSystem** - Queue-based upload with workers
6. **SegmentPackingSystem** - Segment creation and packing
7. **ProductionNNTPClient** - Connection pooling for Usenet

## 1. Folder Management Architecture

### 1.1 Folder States (Actual System)
```python
class FolderState(Enum):
    ADDED = 'added'              # Folder added to system
    INDEXING = 'indexing'        # Creating core index
    INDEXED = 'indexed'          # Core index created
    SEGMENTING = 'segmenting'    # Creating segments with redundancy
    SEGMENTED = 'segmented'      # Segments ready
    UPLOADING = 'uploading'      # Posting to Usenet
    UPLOADED = 'uploaded'        # All segments posted
    PUBLISHING = 'publishing'    # Publishing core index
    PUBLISHED = 'published'      # Core index published
    SYNCING = 'syncing'         # Re-syncing changes
    ERROR = 'error'             # Error state
```

### 1.2 Database Schema (From actual system)
```sql
-- Folders table (based on actual schema)
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    folder_id TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    state TEXT DEFAULT 'added',
    version INTEGER DEFAULT 1,
    
    -- Statistics
    total_files INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    indexed_files INTEGER DEFAULT 0,
    total_segments INTEGER DEFAULT 0,
    
    -- Redundancy (NOT PAR2)
    redundancy_level INTEGER DEFAULT 2,
    redundancy_segments INTEGER DEFAULT 0,
    
    -- Core index
    index_hash TEXT,
    index_size INTEGER,
    index_published BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP,
    uploaded_at TIMESTAMP,
    published_at TIMESTAMP,
    last_sync TIMESTAMP
);

-- Segments table with redundancy_index
CREATE TABLE segments (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    segment_index INTEGER NOT NULL,
    redundancy_index INTEGER DEFAULT 0,  -- For redundancy copies
    size INTEGER,
    hash TEXT,
    compressed_size INTEGER,
    message_id TEXT,
    upload_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, segment_index, redundancy_index)
);
```

## 2. Indexing System (VersionedCoreIndexSystem)

### 2.1 Core Index Structure
```python
class CoreIndex:
    """Actual core index structure from the system"""
    def __init__(self):
        self.version = 1
        self.folder_id = None
        self.created_at = None
        self.files = []  # List of IndexedFile objects
        self.segments = []  # List of segment metadata
        self.folder_stats = None  # FolderStats object
        self.index_hash = None  # SHA256 of index
        
class IndexedFile:
    """File entry in core index"""
    file_id: int
    file_path: str
    file_size: int
    file_hash: str
    segment_count: int
    version: int
    created_at: datetime
    modified_at: datetime
```

### 2.2 Indexing Process
```python
def index_folder(folder_path: str) -> CoreIndex:
    """
    Creates versioned core index for folder
    Uses SimplifiedBinaryIndex for efficiency
    """
    # Phase 1: File Discovery
    - Walk directory tree
    - Filter by configured rules (hidden files, symlinks)
    - Chunk processing (1000 files at a time)
    
    # Phase 2: File Processing
    - Calculate file hashes (SHA256)
    - Extract metadata
    - Create IndexedFile entries
    
    # Phase 3: Core Index Creation
    - Build binary index using SimplifiedBinaryIndex
    - Calculate index hash
    - Store in database
    
    # Phase 4: Version Management
    - Increment version for changes
    - Maintain version history
    - Support rollback
```

## 3. Segmentation with Redundancy (NOT PAR2)

### 3.1 Redundancy System
```python
class RedundancySystem:
    """
    Our actual redundancy system
    Creates duplicate segments, NOT PAR2 recovery files
    """
    def __init__(self, redundancy_level: int = 2):
        self.redundancy_level = redundancy_level  # Number of copies
        
    def create_redundant_segments(self, segment_data: bytes, segment_index: int):
        """
        Creates redundant copies of segments
        Each copy has a different redundancy_index
        """
        segments = []
        
        for redundancy_index in range(self.redundancy_level):
            # Each redundancy copy is the same data
            # Posted to different servers or with different headers
            segment = {
                'data': segment_data,
                'segment_index': segment_index,
                'redundancy_index': redundancy_index,
                'hash': hashlib.sha256(segment_data).hexdigest()
            }
            segments.append(segment)
            
        return segments
```

### 3.2 Segment Creation Process
```python
def segment_file(file_path: str, segment_size: int = 768000):
    """
    Segments file with redundancy
    Default: 768KB segments
    """
    # Read file in chunks
    # Create segments
    # Apply compression (zlib)
    # Encrypt segments
    # Generate redundancy copies (NOT PAR2)
    # Store segment metadata
```

## 4. Upload System (EnhancedUploadSystem)

### 4.1 Upload Queue Management
```python
class UploadTask:
    """Actual upload task from the system"""
    task_id: str
    segment_id: int
    file_path: str
    folder_id: str
    session_id: str
    priority: UploadPriority
    data: bytes
    subject: str
    newsgroup: str
    headers: Dict[str, str]
    retry_count: int = 0
    max_retries: int = 3
    state: UploadState
    message_id: Optional[str] = None
```

### 4.2 Upload Process
```python
def upload_folder(folder_id: str):
    """
    Upload all segments with redundancy
    """
    # Phase 1: Queue Creation
    - Load all segments from database
    - Create upload tasks for each segment
    - Include redundancy copies (redundancy_index 0, 1, etc.)
    
    # Phase 2: Worker Pool
    - Start configured number of workers (default: 10)
    - Each worker processes queue
    - Connection pooling via ProductionNNTPClient
    
    # Phase 3: Posting
    - Post articles to Usenet
    - Store Message-IDs
    - Handle retries
    - Track progress
    
    # Phase 4: Verification
    - Verify all segments uploaded
    - Check redundancy copies
    - Update database status
```

## 5. Publishing System (Core Index Publishing)

### 5.1 What Gets Published
```python
class PublishedIndex:
    """
    The core index that gets published
    NOT NZB, NOT torrent - our custom index format
    """
    def __init__(self):
        self.share_id = None
        self.folder_id = None
        self.version = None
        self.index_data = None  # Binary index data
        self.access_type = None  # public/private/protected
        self.encryption_key = None
        self.segment_references = []  # Message-IDs for segments
```

### 5.2 Publishing Process
```python
def publish_folder(folder_id: str):
    """
    Publishes the core index file
    This is how users discover and access the folder
    """
    # Phase 1: Generate Core Index
    - Load folder metadata
    - Load segment information
    - Create binary index
    
    # Phase 2: Create Share
    - Generate share ID
    - Set access control
    - Encrypt if needed
    
    # Phase 3: Upload Core Index
    - Segment the index file itself
    - Upload index segments
    - Store index Message-IDs
    
    # Phase 4: Generate Access String
    - Create shareable link
    - Include decryption info if protected
    - Return share information
```

## 6. Folder Management UI Components

### 6.1 Folder List Component
```typescript
interface FolderListItem {
  id: string;
  path: string;
  name: string;
  state: FolderState;
  stats: {
    files: number;
    size: number;
    segments: number;
  };
  progress?: {
    operation: string;
    percent: number;
  };
}
```

### 6.2 Folder Tabs

#### Overview Tab
```
- Folder path and name
- Current state with visual indicator
- Statistics:
  * Total files
  * Total size
  * Indexed files
  * Total segments
  * Redundancy segments
- Version information
- Last sync time
```

#### Access Control Tab
```
- Access type (public/private/protected)
- Password management (if protected)
- User access list
- Share ID and link
- NOT: torrent/NZB generation (we don't use these)
```

#### Files & Segments Tab
```
- File tree view
- Segment information per file
- Redundancy status (copies, not PAR2)
- Upload status per segment
- Message-IDs for verification
```

#### Actions Tab
```
- Re-index (check for changes)
- Re-sync (upload new/changed files)
- Verify integrity
- Re-publish core index
- NOT: PAR2 repair (we use redundancy copies)
- NOT: Generate NZB/torrent (we use core index)
```

## 7. Handling Large Folders (20TB/3M Files)

### 7.1 Chunked Processing Strategy
```python
class LargeFolderProcessor:
    """
    Handles massive folders efficiently
    """
    def __init__(self):
        self.chunk_size = 1000  # Files per chunk
        self.max_memory = 4 * 1024**3  # 4GB limit
        self.worker_count = 10
        
    async def process_folder(self, folder_path: str):
        """
        Process 20TB folder with 3M files
        """
        # Phase 1: Streaming Discovery
        - Use generator for file iteration
        - Don't load all files into memory
        - Process in chunks of 1000
        
        # Phase 2: Parallel Processing
        - Use ThreadPoolExecutor
        - Process multiple chunks simultaneously
        - Memory-mapped file reading
        
        # Phase 3: Progressive Updates
        - Update UI every 1% progress
        - Save state every 10,000 files
        - Allow pause/resume
        
        # Phase 4: Database Batching
        - Batch inserts (1000 records)
        - Use transactions
        - Periodic commits
```

### 7.2 Progress Tracking
```python
class ProgressTracker:
    """
    Real-time progress updates via WebSocket
    """
    def __init__(self, websocket):
        self.ws = websocket
        self.operations = {}
        
    async def update_progress(self, folder_id: str, operation: str, data: dict):
        """
        Stream progress to frontend
        """
        message = {
            'type': 'folder_progress',
            'folder_id': folder_id,
            'operation': operation,  # indexing|segmenting|uploading|publishing
            'progress': data['progress'],
            'current_file': data.get('current_file'),
            'speed': data.get('speed'),
            'eta': data.get('eta'),
            'timestamp': datetime.now().isoformat()
        }
        await self.ws.send(json.dumps(message))
```

## 8. Implementation Order

### Phase 1: Core Infrastructure
1. **FolderManager class** - Central management
2. **Database schema** - Tables and indexes
3. **State management** - Folder lifecycle
4. **Basic CRUD operations** - Add/remove folders

### Phase 2: Indexing
1. **Integration with VersionedCoreIndexSystem**
2. **Chunked file processing**
3. **Progress tracking**
4. **Version management**

### Phase 3: Segmentation
1. **Integration with existing segmentation**
2. **Redundancy system** (NOT PAR2)
3. **Segment metadata storage**
4. **Progress updates**

### Phase 4: Upload
1. **Integration with EnhancedUploadSystem**
2. **Queue management**
3. **Worker pool**
4. **Retry logic**

### Phase 5: Publishing
1. **Core index generation**
2. **Share creation**
3. **Access control**
4. **NOT NZB/torrent** (we use core index)

### Phase 6: UI
1. **Folder list component**
2. **Folder details tabs**
3. **Progress indicators**
4. **WebSocket integration**

### Phase 7: Large Folder Support
1. **Chunked processing**
2. **Memory management**
3. **Parallel operations**
4. **Resume capability**

## 9. Key Differences from Generic Usenet

### What We DO Have:
- ✅ **Core Index System** - Custom binary index format
- ✅ **Redundancy Level** - Duplicate segments (configurable)
- ✅ **Versioned Indexing** - Track folder changes
- ✅ **Binary Index** - Efficient for millions of files
- ✅ **Custom Publishing** - Share via core index

### What We DON'T Have:
- ❌ **PAR2** - We use redundancy copies instead
- ❌ **NZB Generation** - We use core index
- ❌ **Torrent Creation** - Not relevant to our system
- ❌ **Indexer Publishing** - We have our own share system

## 10. Critical Implementation Notes

### 10.1 Memory Management for 20TB
```python
# NEVER do this:
all_files = list(os.walk(folder_path))  # Will OOM on 3M files

# ALWAYS do this:
for root, dirs, files in os.walk(folder_path):
    process_batch(files[:1000])  # Process in chunks
```

### 10.2 Database Performance
```python
# NEVER do this:
for file in millions_of_files:
    db.insert_file(file)  # 3M individual inserts

# ALWAYS do this:
db.bulk_insert_files(file_batch)  # Batch of 1000
```

### 10.3 Progress Updates
```python
# NEVER do this:
for i, file in enumerate(files):
    send_progress(i/total*100)  # 3M WebSocket messages

# ALWAYS do this:
if i % 1000 == 0:  # Update every 1000 files
    send_progress(i/total*100)
```

## Summary

This implementation guide focuses on:
1. **Our actual components** - Not generic Usenet features
2. **Core index system** - Not NZB/torrent
3. **Redundancy levels** - Not PAR2
4. **Scalability** - Handle 20TB/3M files
5. **Real functionality** - What actually exists in the codebase

The system is designed for:
- Publishing folders via core index files
- Managing versions and changes
- Handling massive datasets efficiently
- Providing redundancy through duplication
- Custom share system (not traditional Usenet indexers)