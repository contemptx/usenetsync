# Unified System Architecture Plan for UsenetSync

## Executive Summary

This document outlines a comprehensive plan to unify the currently fragmented indexing, segmentation, packaging, uploading, publishing, and download systems in UsenetSync. The goal is to create a single, cohesive architecture that maintains all existing functionality while eliminating redundancy and improving maintainability.

## Current State Analysis

### 1. Multiple Indexing Systems

#### VersionedCoreIndexSystem (`src/indexing/versioned_core_index_system.py`)
- **Purpose**: Full versioning with change tracking
- **Features**:
  - File change detection (added/modified/deleted)
  - Segment-level hashing with SHA256
  - Version history tracking
  - SQLite database for metadata
  - 768KB default segment size
  - Thread-safe operations
- **Database Tables**: files, segments, file_versions, folder_stats

#### SimplifiedBinaryIndex (`src/indexing/simplified_binary_index.py`)
- **Purpose**: Optimized for large datasets (up to 20TB)
- **Features**:
  - Single binary index file
  - Zlib compression (level 9)
  - Memory-efficient scanning
  - Minimal metadata storage
  - Fast serialization/deserialization
- **Database**: None (pure binary format)

### 2. Segmentation Systems

#### FileSegmentProcessor (part of VersionedCoreIndexSystem)
- Creates actual segment data with hashes
- 768KB segments
- Per-segment SHA256 hashing
- Offset tracking

#### SegmentPackingSystem (`src/upload/segment_packing_system.py`)
- Multiple packing strategies (SIMPLE, OPTIMIZED, REDUNDANT, COMPRESSED)
- Segment buffering and batching
- Redundancy management
- Header creation with metadata
- Reed-Solomon error correction support

### 3. Upload Systems

#### EnhancedUploadSystem (`src/upload/enhanced_upload_system.py`)
- Priority-based queuing (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
- Upload sessions with progress tracking
- Retry mechanism with exponential backoff
- Thread pool execution
- State management (QUEUED, UPLOADING, COMPLETED, FAILED, CANCELLED, RETRYING)
- SQLite database for queue persistence

#### UploadQueueManager (`src/upload/upload_queue_manager.py`)
- Smart queue with newsgroup batching
- Rate limiting support
- Priority scheduling
- Queue persistence
- Statistics tracking

### 4. Publishing Systems

#### PublishingSystem (`src/publishing/publishing_system.py`)
- Share creation and management
- Access control (public/private/protected)
- Password protection
- Expiry management
- SQLite database for shares

#### FolderManager Publishing (`src/folder_management/folder_manager.py`)
- Folder-level operations
- PostgreSQL support
- State machine (INDEXED, SEGMENTED, UPLOADING, PUBLISHED)

### 5. Download Systems

#### EnhancedDownloadSystem (`src/download/enhanced_download_system.py`)
- Resume capability
- Parallel downloading
- yEnc decoding
- Integrity verification
- Progress tracking
- State management

#### SegmentRetrievalSystem (`src/download/segment_retrieval_system.py`)
- Multiple retrieval methods (MESSAGE_ID, REDUNDANCY, SUBJECT_HASH)
- Server health tracking
- Intelligent fallback mechanisms
- Priority-based retrieval

### 6. Database Fragmentation

Currently using **multiple database schemas** across systems:
- SQLite in indexing systems
- SQLite in upload/download systems
- PostgreSQL in folder management
- Different table structures for same entities
- No unified transaction management

## Problems with Current Architecture

1. **Redundant Functionality**
   - Multiple segment creation implementations
   - Duplicate database schemas
   - Overlapping upload/publish logic

2. **Integration Issues**
   - Systems not properly connected (per UPLOAD_FLOW_ANALYSIS.md)
   - No unified workflow from indexing to publishing
   - Missing background job processing

3. **Scalability Concerns**
   - Different systems optimized differently
   - No unified resource management
   - Inconsistent batching strategies

4. **Maintenance Burden**
   - Multiple codebases to maintain
   - Inconsistent error handling
   - Difficult to add new features

5. **Security Inconsistencies**
   - Different access control implementations
   - Multiple encryption points
   - Inconsistent authentication

## Proposed Unified Architecture

### Core Design Principles

1. **Single Source of Truth**: One database schema, one indexing system
2. **Modular Pipeline**: Clear separation of concerns with well-defined interfaces
3. **Scalability First**: Built for 20TB+ datasets from the ground up
4. **Security by Design**: Unified security model across all operations
5. **Background Processing**: All heavy operations run asynchronously
6. **Progressive Enhancement**: Start simple, add complexity as needed

### Unified System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Core System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Indexing   │→ │ Segmentation │→ │   Packing    │     │
│  │   Engine     │  │   Engine     │  │   Engine     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                 ↓              │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Unified Data Layer (UDL)               │      │
│  │  - Single database schema                        │      │
│  │  - Consistent entity models                      │      │
│  │  - Transaction management                        │      │
│  └──────────────────────────────────────────────────┘      │
│         ↓                  ↓                 ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Upload    │  │   Publish    │  │   Download   │     │
│  │   Manager    │  │   Manager    │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Security & Access Control Layer          │      │
│  │  - Unified authentication                        │      │
│  │  - Consistent encryption                         │      │
│  │  - Access level management                       │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Background Job Processing System         │      │
│  │  - Task queue                                    │      │
│  │  - Worker pools                                  │      │
│  │  - Progress tracking                             │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Component Specifications

#### 1. Unified Indexing Engine

**Combines best of both systems:**
```python
class UnifiedIndexingEngine:
    """
    Hybrid approach combining VersionedCoreIndex and SimplifiedBinaryIndex
    """
    
    def __init__(self):
        self.versioning_enabled = True  # Can be disabled for speed
        self.compression_level = 9      # Configurable
        self.segment_size = 768000       # Standard across system
        
    def index_folder(self, path: str, options: IndexOptions):
        # Use SimplifiedBinaryIndex approach for initial scan
        # Add versioning metadata if enabled
        # Stream results to database
        # Return unified index format
```

**Features:**
- Streaming indexing for large datasets
- Optional versioning (can be disabled for speed)
- Binary format with compression
- Progressive indexing with checkpoints
- Memory-mapped file support

#### 2. Unified Segmentation Engine

**Single segmentation implementation:**
```python
class UnifiedSegmentationEngine:
    """
    Single source for all segmentation operations
    """
    
    def segment_file(self, file_path: str, options: SegmentOptions):
        # Standard 768KB segments
        # Optional compression
        # Optional redundancy
        # Consistent hash calculation
        # Stream to database
```

**Features:**
- Consistent segment size (768KB)
- Optional Reed-Solomon redundancy
- Streaming operation for large files
- Parallel processing support
- Direct database integration

#### 3. Unified Data Layer (UDL)

**Single database schema for all operations:**

```sql
-- Core entities
CREATE TABLE entities (
    entity_id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- 'folder', 'file', 'segment', 'share'
    parent_id UUID REFERENCES entities(entity_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Indexing data
CREATE TABLE index_data (
    entity_id UUID PRIMARY KEY REFERENCES entities(entity_id),
    path TEXT NOT NULL,
    size BIGINT NOT NULL,
    hash VARCHAR(64),
    version INTEGER DEFAULT 1,
    indexed_at TIMESTAMP,
    binary_index BYTEA  -- Compressed binary index
);

-- Segments
CREATE TABLE segments (
    segment_id UUID PRIMARY KEY,
    entity_id UUID REFERENCES entities(entity_id),
    segment_index INTEGER NOT NULL,
    size INTEGER NOT NULL,
    hash VARCHAR(64) NOT NULL,
    offset BIGINT,
    data BYTEA,  -- Optional, for caching
    redundancy_level INTEGER DEFAULT 0
);

-- Upload/Download operations
CREATE TABLE operations (
    operation_id UUID PRIMARY KEY,
    entity_id UUID REFERENCES entities(entity_id),
    operation_type VARCHAR(50), -- 'upload', 'download', 'publish'
    state VARCHAR(50),
    priority INTEGER DEFAULT 5,
    progress FLOAT DEFAULT 0.0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- Publishing/Sharing
CREATE TABLE shares (
    share_id VARCHAR(255) PRIMARY KEY,
    entity_id UUID REFERENCES entities(entity_id),
    share_type VARCHAR(50), -- 'public', 'private', 'protected'
    access_control JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Message tracking
CREATE TABLE messages (
    message_id VARCHAR(255) PRIMARY KEY,
    segment_id UUID REFERENCES segments(segment_id),
    newsgroup VARCHAR(255),
    subject VARCHAR(500),
    posted_at TIMESTAMP,
    server VARCHAR(255)
);
```

#### 4. Unified Upload Manager

**Single upload system with all features:**
```python
class UnifiedUploadManager:
    """
    Combines EnhancedUploadSystem and UploadQueueManager
    """
    
    def __init__(self):
        self.queue = PriorityQueue()
        self.workers = WorkerPool()
        self.batch_processor = BatchProcessor()
        
    async def upload_entity(self, entity_id: str, options: UploadOptions):
        # Queue segments for upload
        # Batch by newsgroup
        # Apply rate limiting
        # Track progress
        # Handle retries
```

#### 5. Unified Security Layer

**Consistent security across all operations:**
```python
class UnifiedSecurityLayer:
    """
    Single security implementation
    """
    
    def __init__(self):
        self.encryption = AES256_GCM
        self.key_derivation = Scrypt
        self.access_control = RoleBasedAccessControl()
        
    def encrypt_segment(self, segment: bytes, access_level: AccessLevel):
        # Consistent encryption for all segments
        
    def verify_access(self, user_id: str, entity_id: str, operation: str):
        # Unified access control
```

### Migration Strategy

#### Phase 1: Foundation (Week 1-2)
1. Create unified database schema
2. Implement data migration scripts
3. Set up background job system
4. Create unified configuration

#### Phase 2: Core Unification (Week 3-4)
1. Implement UnifiedIndexingEngine
2. Implement UnifiedSegmentationEngine
3. Create UnifiedDataLayer
4. Add progress tracking infrastructure

#### Phase 3: Upload/Download Unification (Week 5-6)
1. Merge upload systems into UnifiedUploadManager
2. Merge download systems into UnifiedDownloadManager
3. Unify publishing mechanisms
4. Implement unified queue management

#### Phase 4: Security & Testing (Week 7-8)
1. Implement UnifiedSecurityLayer
2. Migrate access control systems
3. Comprehensive testing
4. Performance optimization

#### Phase 5: Integration & Cleanup (Week 9-10)
1. Connect all systems through unified pipeline
2. Remove deprecated code
3. Update documentation
4. Final testing and validation

### Backward Compatibility

To ensure smooth transition:

1. **Adapter Pattern**: Create adapters for existing interfaces
2. **Feature Flags**: Enable gradual rollout
3. **Data Migration**: Automated migration of existing data
4. **Fallback Mechanisms**: Ability to use old systems if needed

### Performance Targets

- **Indexing**: 100,000 files/minute
- **Segmentation**: 1GB/second
- **Upload**: 100MB/second (network permitting)
- **Download**: 100MB/second (network permitting)
- **Memory Usage**: < 2GB for 1 million files
- **Database Size**: ~1KB per file + segments

### Security Requirements

1. **Encryption**: AES-256-GCM for all sensitive data
2. **Access Control**: Role-based with zero-knowledge proofs
3. **Audit Logging**: All operations logged
4. **Key Management**: Secure key derivation and storage
5. **Network Security**: TLS for all connections

### Benefits of Unification

1. **Reduced Complexity**: Single codebase to maintain
2. **Improved Performance**: Optimized data flow
3. **Better Scalability**: Designed for large datasets
4. **Consistent Security**: Single security model
5. **Easier Testing**: Unified test suite
6. **Better Documentation**: Single system to document
7. **Reduced Bugs**: Fewer integration points
8. **Faster Development**: Clear architecture

### Risk Mitigation

1. **Gradual Migration**: Phase-by-phase approach
2. **Comprehensive Testing**: Unit, integration, and E2E tests
3. **Rollback Plan**: Ability to revert to old system
4. **Performance Monitoring**: Track all metrics
5. **User Communication**: Clear migration timeline

### Implementation Priority

1. **Critical Path First**: Focus on indexing → segmentation → upload flow
2. **Database Unification**: Essential for all other work
3. **Background Processing**: Enable scalability
4. **Security Layer**: Ensure data protection
5. **UI Integration**: Connect to user interface

### Success Metrics

- All existing functionality preserved
- 50% reduction in code complexity
- 2x improvement in indexing speed
- 3x improvement in upload throughput
- Single database schema
- Unified API surface
- Complete test coverage

## Conclusion

This unification plan addresses the current fragmentation while maintaining all functionality. The phased approach ensures minimal disruption while delivering a more maintainable, scalable, and secure system. The unified architecture will support UsenetSync's growth from handling gigabytes to petabytes of data efficiently.