# Unified System Architecture Plan for UsenetSync

## Executive Summary

This document outlines a comprehensive plan to unify the currently fragmented indexing, segmentation, packaging, uploading, publishing, and download systems in UsenetSync. The goal is to create a single, cohesive architecture that maintains all existing functionality while eliminating redundancy and improving maintainability.

## Current State Analysis

**Important Note**: The `folder_manager.py` appears to be incomplete/development code. The actual production systems are:
- `src/core/main.py` - Main integration point
- `src/indexing/versioned_core_index_system.py` and `simplified_binary_index.py` - Core indexing
- `src/upload/enhanced_upload_system.py` and `segment_packing_system.py` - Upload pipeline
- `src/download/enhanced_download_system.py` and `segment_retrieval_system.py` - Download pipeline
- `src/upload/publishing_system.py` (not `src/publishing/`) - Share publishing
- `src/security/enhanced_security_system.py` - Security layer

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

#### PublishingSystem (`src/upload/publishing_system.py`)
- Share creation and management
- Access control (public/private/protected)
- Password protection
- Expiry management
- SQLite database for shares
- Used in production via `src/core/main.py`

#### ShareIDGenerator (`src/indexing/share_id_generator.py`)
- Generates unique share IDs without patterns
- Creates access strings (standard/compact/legacy formats)
- Parses and validates access strings
- No Usenet information leaked in share IDs

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
- SQLite in indexing systems (VersionedCoreIndexSystem)
- SQLite in upload/download systems (EnhancedUploadSystem, EnhancedDownloadSystem)
- PostgreSQL option in main.py and CLI (ShardedPostgreSQLManager)
- ProductionDatabaseManager wraps EnhancedDatabaseManager with retry logic
- Different table structures for same entities (files, segments, shares)
- No unified transaction management

### 7. Actual Production Workflow (from src/core/main.py)

1. **Initialization**: UsenetSync class integrates all components
2. **Index**: `index_system.index_folder()` → creates file/segment metadata
3. **Upload**: `upload_system` with `segment_packing` → posts to Usenet
4. **Publish**: `publishing.create_share()` → generates access string
5. **Download**: `download_system.download_from_access_string()` → retrieves and reconstructs
6. **Security**: `EnhancedSecuritySystem` handles encryption/decryption throughout

## Problems with Current Architecture

1. **Redundant Functionality**
   - Multiple segment creation implementations (FileSegmentProcessor vs SegmentPackingSystem)
   - Duplicate database schemas (SQLite vs PostgreSQL, different table structures)
   - Overlapping upload/publish logic (PublishingSystem vs folder_manager)
   - Two publishing system paths (src/upload/ vs src/publishing/)

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
   - Incomplete/experimental code (folder_manager) mixed with production

5. **Security Inconsistencies**
   - Different access control implementations
   - Multiple encryption points
   - Inconsistent authentication

## Proposed Unified Architecture

### Core Design Principles

1. **Single Source of Truth**: One database schema, one indexing system
2. **Modular Pipeline**: Clear separation of concerns with well-defined interfaces
3. **Scalability First**: Built for 20TB+ datasets from the ground up with streaming
4. **Security by Design**: Unified security model across all operations
5. **Background Processing**: All heavy operations run asynchronously
6. **Progressive Enhancement**: Start simple, add complexity as needed
7. **Preserve Critical Functionality**: All security features from CRITICAL_FUNCTIONALITY_PRESERVATION.md must be maintained
8. **Resource Aware**: Never load large datasets into memory, use streaming
9. **Dual Database Support**: Both SQLite and PostgreSQL with auto-setup

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

**Single segmentation implementation with packing and redundancy:**
```python
class UnifiedSegmentationEngine:
    """
    Single source for all segmentation operations
    """
    
    def __init__(self):
        self.segment_size = 768000  # 750KB standard
        self.packing_system = SegmentPackingSystem()
    
    def segment_file(self, file_path: str, options: SegmentOptions):
        # Standard 768KB segments
        # Pack small files together
        # Create redundant copies (unique articles)
        # Stream large files to avoid memory issues
        # Consistent hash calculation
        
    def create_redundant_segments(self, segment: bytes, redundancy_level: int):
        """Create unique redundant copies, NOT duplicates"""
        segments = []
        for i in range(redundancy_level):
            segments.append({
                'data': segment,
                'redundancy_index': i,
                'subject': generate_random_subject(),  # UNIQUE
                'message_id': generate_message_id()    # UNIQUE
            })
        return segments
```

**Features:**
- Consistent segment size (768KB)
- Optional Reed-Solomon redundancy
- Streaming operation for large files
- Parallel processing support
- Direct database integration

#### 3. Unified Data Layer (UDL)

**Single database schema supporting both SQLite and PostgreSQL:**

```python
class UnifiedDataLayer:
    def __init__(self, config):
        if config.database_type == 'postgresql':
            self.db = PostgreSQLManager(config)
            # Auto-setup if needed
            if config.auto_install:
                self.auto_install_postgresql()
        else:
            self.db = SQLiteManager(config)  # Default
    
    def auto_install_postgresql(self):
        """GUI-triggered auto installation"""
        # Platform-specific installation
        # Configuration for large datasets
        # Sharding setup for 20TB+
```

```sql
-- Core entities (works on both SQLite and PostgreSQL)
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

-- Segments with redundancy support
CREATE TABLE segments (
    segment_id UUID,
    entity_id UUID REFERENCES entities(entity_id),
    segment_index INTEGER NOT NULL,
    redundancy_index INTEGER DEFAULT 0,  -- 0=original, 1+=redundant copies
    size INTEGER NOT NULL,
    hash VARCHAR(64) NOT NULL,
    offset BIGINT,
    message_id TEXT ENCRYPTED,  -- Encrypted for security
    subject TEXT ENCRYPTED,      -- Encrypted for security
    internal_subject TEXT,       -- For verification only
    packed_segment_id UUID,      -- For packed small files
    PRIMARY KEY (segment_id, redundancy_index)
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
    Single security implementation preserving critical features
    """
    
    def __init__(self):
        self.encryption = AES256_GCM
        self.key_derivation = Scrypt
        self.access_control = RoleBasedAccessControl()
        
    def generate_subject_pair(self, folder_id: str, file_version: int, 
                            segment_index: int) -> SubjectPair:
        """CRITICAL: Maintain two-layer subject system"""
        internal_subject = self._generate_internal_subject(...)  # 64 hex chars
        usenet_subject = self._generate_usenet_subject()  # 20 random chars
        return SubjectPair(internal_subject, usenet_subject)
        
    def encrypt_segment(self, segment: bytes, access_level: AccessLevel):
        # Consistent encryption for all segments
        
    def verify_access(self, user_id: str, entity_id: str, operation: str):
        # Unified access control with zero-knowledge proofs
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

- **Indexing**: 100,000 files/minute (streaming for large datasets)
- **Segmentation**: 1GB/second with packing for small files
- **Upload**: 100MB/second (network permitting)
- **Download**: 100MB/second (network permitting)
- **Memory Usage**: < 2GB for 1 million files (streaming for 20TB+)
- **Database Size**: ~1KB per file + segments
- **Max Dataset Size**: 20TB+ with PostgreSQL sharding
- **Redundancy**: Configurable 1-5 unique copies
- **Segment Packing**: Pack files < 750KB together

### Security Requirements

1. **Encryption**: AES-256-GCM for all sensitive data
2. **Access Control**: Role-based with zero-knowledge proofs
3. **Audit Logging**: All operations logged
4. **Key Management**: Secure key derivation and storage
5. **Network Security**: TLS for all connections
6. **Usenet Obfuscation**: Maintain two-layer subject system
7. **Message ID Security**: Random generation with no patterns
8. **Share ID Protection**: No Usenet data in share identifiers
9. **Client-Side Decryption**: All sensitive operations local only

**CRITICAL**: See CRITICAL_FUNCTIONALITY_PRESERVATION.md for detailed security requirements that MUST be preserved.

### Benefits of Unification

1. **Reduced Complexity**: Single codebase to maintain
2. **Improved Performance**: Optimized data flow with streaming
3. **Better Scalability**: Handles 20TB+ datasets with resource management
4. **Consistent Security**: Single security model with encrypted storage
5. **Easier Testing**: Unified test suite
6. **Better Documentation**: Single system to document
7. **Reduced Bugs**: Fewer integration points
8. **Faster Development**: Clear architecture
9. **Preserved Functionality**: All critical features maintained:
   - Redundancy with unique articles
   - Segment packing for small files
   - Dual database support
   - Encrypted location storage
   - Resource-aware processing

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