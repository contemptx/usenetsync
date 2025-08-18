# Final Implementation Plan - UsenetSync Folder Management System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FOLDER LIFECYCLE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ADD FOLDER → INDEX → SEGMENT → UPLOAD → PUBLISH → SHARE        │
│      ↓          ↓        ↓         ↓        ↓        ↓          │
│   [Added]   [Indexed][Segmented][Uploaded][Published][Active]   │
│                                                                  │
│  Each stage has:                                                │
│  • Progress tracking (0-100%)                                   │
│  • Worker management                                            │
│  • Error handling & retry                                       │
│  • Resume capability                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Backend Infrastructure

### 1.1 Folder Manager Core
```python
# src/folder_management/folder_manager.py

class FolderManager:
    """
    Central management system leveraging existing components
    """
    def __init__(self):
        # Use existing PostgreSQL system
        self.db = ShardedPostgreSQLManager(config)
        
        # Use existing indexing system
        self.indexer = VersionedCoreIndexSystem(db, security, config)
        self.parallel_indexer = ParallelIndexer(db)
        
        # Use existing upload system
        self.upload_system = EnhancedUploadSystem()
        self.upload_processor = ParallelUploadProcessor(pool_manager, db_ops)
        
        # Use existing publishing system
        self.publisher = PublishingSystem(db, security, binary_index)
        
        # Connection pool for NNTP
        self.nntp_pool = ProductionNNTPClient(
            host=config.host,
            port=config.port,
            max_connections=20
        )
```

### 1.2 Database Schema (PostgreSQL)
```sql
-- Main folder management table
CREATE TABLE managed_folders (
    id SERIAL PRIMARY KEY,
    folder_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    state VARCHAR(50) DEFAULT 'added',
    
    -- Statistics (updated during indexing)
    total_files INTEGER DEFAULT 0,
    total_folders INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    indexed_files INTEGER DEFAULT 0,
    indexed_size BIGINT DEFAULT 0,
    
    -- Segmentation stats
    total_segments INTEGER DEFAULT 0,
    segment_size INTEGER DEFAULT 768000,
    redundancy_level INTEGER DEFAULT 2,
    redundancy_segments INTEGER DEFAULT 0,
    
    -- Upload stats
    uploaded_segments INTEGER DEFAULT 0,
    failed_segments INTEGER DEFAULT 0,
    upload_speed BIGINT DEFAULT 0,
    
    -- Publishing
    share_id TEXT UNIQUE,
    core_index_hash TEXT,
    core_index_size INTEGER,
    published BOOLEAN DEFAULT FALSE,
    
    -- Access control
    access_type VARCHAR(20) DEFAULT 'public',
    password_hash TEXT,
    max_downloads INTEGER,
    expires_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP,
    segmented_at TIMESTAMP,
    uploaded_at TIMESTAMP,
    published_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    
    -- Versioning
    current_version INTEGER DEFAULT 1,
    
    -- Progress tracking
    current_operation VARCHAR(50),
    operation_progress DECIMAL(5,2) DEFAULT 0.00,
    operation_started_at TIMESTAMP,
    operation_eta INTEGER, -- seconds
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for performance
CREATE INDEX idx_folders_state ON managed_folders(state);
CREATE INDEX idx_folders_share_id ON managed_folders(share_id);
CREATE INDEX idx_folders_path ON managed_folders(path);

-- Progress tracking table
CREATE TABLE folder_operations (
    id SERIAL PRIMARY KEY,
    folder_id UUID REFERENCES managed_folders(folder_id),
    operation VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    progress DECIMAL(5,2) DEFAULT 0.00,
    current_item TEXT,
    items_processed INTEGER DEFAULT 0,
    items_total INTEGER,
    bytes_processed BIGINT DEFAULT 0,
    bytes_total BIGINT,
    speed_mbps DECIMAL(10,2),
    eta_seconds INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

## Phase 2: Folder Operations Implementation

### 2.1 Add Folder Operation
```python
async def add_folder(self, path: str, name: Optional[str] = None) -> Dict:
    """
    Add folder to management system
    """
    # Validate path
    folder_path = Path(path).resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        raise ValueError(f"Invalid folder path: {path}")
    
    # Check for duplicates using PostgreSQL
    with self.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_id FROM managed_folders WHERE path = %s",
            (str(folder_path),)
        )
        if cursor.fetchone():
            raise ValueError(f"Folder already managed: {path}")
    
    # Create folder record
    folder_id = str(uuid.uuid4())
    folder_name = name or folder_path.name
    
    # Insert into PostgreSQL
    with self.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO managed_folders (folder_id, path, name, state)
            VALUES (%s, %s, %s, 'added')
            RETURNING *
        """, (folder_id, str(folder_path), folder_name))
        
        folder = cursor.fetchone()
        conn.commit()
    
    return folder
```

### 2.2 Index Folder Operation
```python
async def index_folder(self, folder_id: str, force: bool = False) -> Dict:
    """
    Index folder using existing VersionedCoreIndexSystem
    Handles 3M+ files through chunking
    """
    # Update state
    await self._update_folder_state(folder_id, 'indexing')
    
    # Create progress callback
    def progress_callback(data: Dict):
        # Stream to WebSocket
        self.websocket.send({
            'type': 'indexing_progress',
            'folder_id': folder_id,
            'current': data.get('current', 0),
            'total': data.get('total', 0),
            'file': data.get('file', ''),
            'throughput': data.get('throughput_mbps', 0),
            'eta': data.get('eta', 0)
        })
        
        # Update database
        self._update_operation_progress(
            folder_id, 'indexing',
            progress=data.get('current', 0) / data.get('total', 1) * 100,
            current_item=data.get('file'),
            items_processed=data.get('current'),
            items_total=data.get('total')
        )
    
    # Use ParallelIndexer for performance (10,000+ files/sec)
    folder = await self._get_folder(folder_id)
    
    if force:
        # Re-index with version increment
        result = await self.indexer.reindex_folder(
            folder['path'],
            folder_id,
            progress_callback=progress_callback
        )
    else:
        # Initial indexing
        result = await self.parallel_indexer.index_directory(
            folder['path'],
            session_id=folder_id
        )
    
    # Update folder statistics
    await self._update_folder_stats(folder_id, {
        'total_files': result['files_indexed'],
        'total_folders': result.get('folders', 0),
        'total_size': result['total_size'],
        'indexed_files': result['files_indexed'],
        'indexed_at': datetime.now(),
        'state': 'indexed',
        'current_version': result.get('version', 1)
    })
    
    return result
```

### 2.3 Segment Folder Operation
```python
async def segment_folder(self, folder_id: str) -> Dict:
    """
    Create segments with redundancy (NOT PAR2)
    Uses memory-mapped files for efficiency
    """
    # Update state
    await self._update_folder_state(folder_id, 'segmenting')
    
    folder = await self._get_folder(folder_id)
    
    # Get files from database (PostgreSQL)
    files = await self.db.get_folder_files(folder_id)
    
    # Use OptimizedSegmentPacker for efficiency
    packer = OptimizedSegmentPacker(
        segment_size=folder['segment_size'],  # 768KB default
        pack_threshold=50000  # 50KB
    )
    
    total_segments = 0
    redundancy_segments = 0
    
    # Process files in chunks for memory efficiency
    for file_batch in self._batch_files(files, batch_size=100):
        
        # Pack small files together, segment large files
        for pack_data in packer.pack_files_optimized(file_batch):
            
            # Create redundancy copies (not PAR2)
            for redundancy_index in range(folder['redundancy_level']):
                segment = {
                    'file_id': pack_data['file_id'],
                    'segment_index': pack_data['index'],
                    'redundancy_index': redundancy_index,
                    'size': pack_data['size'],
                    'hash': pack_data['hash'],
                    'compressed_size': pack_data['compressed_size'],
                    'data': pack_data['data']  # Encrypted & compressed
                }
                
                # Store in PostgreSQL using bulk operations
                await self.db.bulk_insert_segments([segment])
                
                total_segments += 1
                if redundancy_index > 0:
                    redundancy_segments += 1
                
                # Progress update
                await self._send_progress(folder_id, 'segmenting', {
                    'segments_created': total_segments,
                    'redundancy_segments': redundancy_segments
                })
    
    # Update folder stats
    await self._update_folder_stats(folder_id, {
        'total_segments': total_segments,
        'redundancy_segments': redundancy_segments,
        'segmented_at': datetime.now(),
        'state': 'segmented'
    })
    
    return {
        'total_segments': total_segments,
        'redundancy_segments': redundancy_segments
    }
```

### 2.4 Upload Folder Operation
```python
async def upload_folder(self, folder_id: str) -> Dict:
    """
    Upload segments to Usenet using existing infrastructure
    Achieves 100+ MB/s throughput
    """
    # Update state
    await self._update_folder_state(folder_id, 'uploading')
    
    folder = await self._get_folder(folder_id)
    
    # Get segments from PostgreSQL
    segments = await self.db.get_folder_segments(folder_id)
    
    # Create upload session
    session = self.upload_system.create_session(
        folder_id=folder_id,
        total_segments=len(segments)
    )
    
    # Queue segments for upload
    for segment in segments:
        task = UploadTask(
            task_id=str(uuid.uuid4()),
            segment_id=segment['id'],
            file_path=segment['file_path'],
            folder_id=folder_id,
            session_id=session.session_id,
            priority=UploadPriority.NORMAL,
            data=segment['data'],
            subject=self._build_subject(folder, segment),
            newsgroup=folder.get('newsgroup', 'alt.binaries.test'),
            headers=self._build_headers(folder, segment)
        )
        
        await self.upload_system.queue_task(task)
    
    # Start parallel upload (uses workers)
    upload_result = await self.upload_processor.process_upload_session(
        session_id=session.session_id,
        progress_callback=lambda p: self._send_progress(
            folder_id, 'uploading', p
        )
    )
    
    # Update folder stats
    await self._update_folder_stats(folder_id, {
        'uploaded_segments': upload_result['uploaded'],
        'failed_segments': upload_result['failed'],
        'uploaded_at': datetime.now(),
        'state': 'uploaded' if upload_result['failed'] == 0 else 'partial'
    })
    
    return upload_result
```

### 2.5 Publish Folder Operation
```python
async def publish_folder(self, folder_id: str) -> Dict:
    """
    Publish core index file (NOT NZB/torrent)
    Creates shareable access string
    """
    # Update state
    await self._update_folder_state(folder_id, 'publishing')
    
    folder = await self._get_folder(folder_id)
    
    # Create core index using SimplifiedBinaryIndex
    index_builder = IndexBuilder(self.db, self.security, self.binary_index)
    
    # Build core index with all metadata
    core_index = await index_builder.build_folder_index(
        folder_id=folder_id,
        include_segments=True,
        include_message_ids=True
    )
    
    # Compress and encrypt core index
    compressed_index = zlib.compress(core_index, level=9)
    encrypted_index, encryption_key = self.security.encrypt_data(compressed_index)
    
    # Upload core index itself
    index_segments = await self._segment_data(
        encrypted_index,
        segment_size=768000
    )
    
    # Post index segments to Usenet
    index_message_ids = []
    for segment in index_segments:
        message_id = await self.nntp_pool.post_article(
            newsgroup=folder['newsgroup'],
            subject=f"[INDEX] {folder['name']} - Part {segment['index']}",
            data=segment['data']
        )
        index_message_ids.append(message_id)
    
    # Generate share ID and access string
    share_id = self._generate_share_id(folder)
    access_string = self._create_access_string(
        share_id=share_id,
        index_message_ids=index_message_ids,
        encryption_key=encryption_key,
        access_type=folder['access_type']
    )
    
    # Update folder with share info
    await self._update_folder_stats(folder_id, {
        'share_id': share_id,
        'core_index_hash': hashlib.sha256(core_index).hexdigest(),
        'core_index_size': len(core_index),
        'published': True,
        'published_at': datetime.now(),
        'state': 'published'
    })
    
    return {
        'share_id': share_id,
        'access_string': access_string,
        'index_size': len(core_index),
        'index_segments': len(index_segments)
    }
```

## Phase 3: Frontend Implementation

### 3.1 Folder Management Page Structure
```typescript
// src/pages/FolderManagement.tsx

interface ManagedFolder {
  id: string;
  path: string;
  name: string;
  state: FolderState;
  
  // Statistics
  stats: {
    totalFiles: number;
    totalFolders: number;
    totalSize: number;
    indexedFiles: number;
    totalSegments: number;
    uploadedSegments: number;
    redundancySegments: number;
  };
  
  // Progress
  progress: {
    operation: string;
    percent: number;
    currentFile?: string;
    speed?: number;
    eta?: number;
    itemsProcessed?: number;
    itemsTotal?: number;
  };
  
  // Sharing
  share?: {
    shareId: string;
    accessString: string;
    accessType: 'public' | 'private' | 'protected';
    published: boolean;
  };
  
  // Versioning
  version: number;
  lastSync?: Date;
}
```

### 3.2 WebSocket Progress Streaming
```typescript
// src/services/progress-stream.ts

class ProgressStream {
  private ws: WebSocket;
  private callbacks: Map<string, (progress: any) => void>;
  
  connect() {
    this.ws = new WebSocket('ws://localhost:8080/progress');
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'indexing_progress':
          this.updateIndexingProgress(data);
          break;
        case 'segmenting_progress':
          this.updateSegmentingProgress(data);
          break;
        case 'uploading_progress':
          this.updateUploadingProgress(data);
          break;
        case 'publishing_progress':
          this.updatePublishingProgress(data);
          break;
      }
    };
  }
  
  private updateIndexingProgress(data: any) {
    // Update UI with:
    // - Files processed: data.current / data.total
    // - Current file: data.file
    // - Speed: data.throughput (files/sec)
    // - ETA: data.eta
  }
}
```

### 3.3 Folder List Component
```typescript
// src/components/FolderList.tsx

export const FolderList: React.FC = () => {
  const [folders, setFolders] = useState<ManagedFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  
  // Load folders with pagination (NEVER load all at once)
  const loadFolders = async (page: number = 0) => {
    const result = await invoke('get_folders_page', {
      offset: page * 100,
      limit: 100
    });
    setFolders(result.folders);
  };
  
  // State indicator component
  const StateIndicator = ({ state, progress }) => {
    const colors = {
      'added': 'gray',
      'indexing': 'blue',
      'indexed': 'green',
      'segmenting': 'yellow',
      'segmented': 'orange',
      'uploading': 'purple',
      'uploaded': 'indigo',
      'publishing': 'pink',
      'published': 'green'
    };
    
    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full bg-${colors[state]}-500`} />
        <span className="text-sm">{state}</span>
        {progress > 0 && (
          <span className="text-xs text-gray-500">{progress.toFixed(1)}%</span>
        )}
      </div>
    );
  };
  
  return (
    <div className="folder-list">
      {folders.map(folder => (
        <div key={folder.id} className="folder-item">
          <div className="folder-name">{folder.name}</div>
          <StateIndicator 
            state={folder.state} 
            progress={folder.progress?.percent} 
          />
          <div className="folder-stats">
            {folder.stats.totalFiles} files | 
            {formatBytes(folder.stats.totalSize)}
          </div>
        </div>
      ))}
    </div>
  );
};
```

### 3.4 Folder Details Tabs
```typescript
// src/components/FolderDetails.tsx

export const FolderDetails: React.FC<{ folder: ManagedFolder }> = ({ folder }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  return (
    <div className="folder-details">
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tab value="overview" label="Overview" />
        <Tab value="access" label="Access Control" />
        <Tab value="files" label="Files & Segments" />
        <Tab value="actions" label="Actions" />
      </Tabs>
      
      {activeTab === 'overview' && <OverviewTab folder={folder} />}
      {activeTab === 'access' && <AccessControlTab folder={folder} />}
      {activeTab === 'files' && <FilesSegmentsTab folder={folder} />}
      {activeTab === 'actions' && <ActionsTab folder={folder} />}
    </div>
  );
};
```

## Phase 4: Operations Flow

### 4.1 Complete Upload Flow
```
1. User adds folder
   → Create database record
   → Show in folder list as "added"

2. User clicks "Index"
   → Start ParallelIndexer (10,000+ files/sec)
   → Stream progress via WebSocket
   → Update UI in real-time
   → Save to PostgreSQL

3. User clicks "Segment"
   → Use OptimizedSegmentPacker
   → Create redundancy copies (not PAR2)
   → Store in PostgreSQL with bulk ops
   → Show segment count

4. User clicks "Upload"
   → Queue all segments
   → Start parallel workers
   → Post to Usenet
   → Track Message-IDs
   → Show speed & ETA

5. User clicks "Publish"
   → Generate core index
   → Upload index segments
   → Create share link
   → Show access string
```

### 4.2 Large Folder Handling (20TB/3M files)
```python
# Automatic optimizations kick in:

if folder_stats['total_files'] > 100000:
    # Use chunked processing
    chunk_size = 1000
    
if folder_stats['total_size'] > 1_000_000_000_000:  # 1TB
    # Use memory-mapped files
    use_mmap = True
    
if folder_stats['total_files'] > 1000000:
    # Increase worker count
    worker_count = 16
    
# Progress updates throttled
if items_processed % 1000 == 0:
    send_progress_update()
```

## Phase 5: Access Control & Sharing

### 5.1 Access Types
```typescript
interface AccessControl {
  type: 'public' | 'private' | 'protected';
  
  // Public: Anyone with share link can access
  // Private: Only specified users can access
  // Protected: Password required
  
  password?: string;  // For protected shares
  allowedUsers?: string[];  // For private shares
  maxDownloads?: number;  // Limit downloads
  expiresAt?: Date;  // Expiration date
}
```

### 5.2 Share Generation
```typescript
interface Share {
  shareId: string;  // Unique identifier
  accessString: string;  // Full access string with encryption
  
  // Format: usenetsync://share/SHARE_ID?key=ENCRYPTION_KEY&index=MESSAGE_IDS
  
  qrCode: string;  // QR code for mobile
  shortUrl?: string;  // Optional short URL
}
```

## Phase 6: Re-sync & Maintenance

### 6.1 Re-sync Operation
```python
async def resync_folder(self, folder_id: str) -> Dict:
    """
    Check for changes and upload only new/modified files
    """
    # Use VersionedCoreIndexSystem for change detection
    changes = await self.indexer.detect_changes(folder_id)
    
    if changes['new_files'] or changes['modified_files']:
        # Process only changed files
        await self._process_changes(folder_id, changes)
        
        # Increment version
        await self._increment_folder_version(folder_id)
        
        # Re-publish core index
        await self.publish_folder(folder_id)
```

### 6.2 Integrity Verification
```python
async def verify_folder(self, folder_id: str) -> Dict:
    """
    Verify all segments are uploaded correctly
    """
    # Check all segments have Message-IDs
    missing = await self.db.get_segments_without_message_ids(folder_id)
    
    if missing:
        # Re-upload missing segments
        await self._reupload_segments(missing)
    
    return {
        'total_segments': total,
        'verified': total - len(missing),
        'reupload': len(missing)
    }
```

## Implementation Timeline

### Week 1: Backend Infrastructure
- [ ] Create FolderManager class
- [ ] Set up PostgreSQL tables
- [ ] Integrate with existing systems
- [ ] Add progress tracking

### Week 2: Core Operations
- [ ] Implement add_folder
- [ ] Implement index_folder with ParallelIndexer
- [ ] Implement segment_folder with redundancy
- [ ] Implement upload_folder with workers

### Week 3: Publishing & Sharing
- [ ] Implement publish_folder
- [ ] Create core index generation
- [ ] Add access control
- [ ] Generate share links

### Week 4: Frontend
- [ ] Create FolderManagement page
- [ ] Implement folder list with pagination
- [ ] Add progress streaming via WebSocket
- [ ] Create all tabs (Overview, Access, Files, Actions)

### Week 5: Testing & Optimization
- [ ] Test with 20TB dataset
- [ ] Optimize for 3M files
- [ ] Add error recovery
- [ ] Performance tuning

## Success Metrics

1. **Performance**
   - Index: 10,000+ files/second
   - Upload: 100+ MB/s throughput
   - Handle: 20TB+ folders

2. **Scalability**
   - Support: 3,000,000+ files
   - PostgreSQL: 30M+ segments
   - Workers: 16+ parallel

3. **Reliability**
   - Resume: From any stage
   - Retry: Failed operations
   - Verify: Integrity checks

4. **User Experience**
   - Real-time: Progress updates
   - Responsive: Never freeze UI
   - Clear: State indicators

This implementation plan leverages ALL existing functionality and provides a complete, production-ready folder management system.