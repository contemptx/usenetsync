-- UsenetSync Database Schema
-- Fixed version that matches code expectations

-- User configuration
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT, -- JSON
    download_path TEXT DEFAULT '.downloads',
    temp_path TEXT DEFAULT '.temp',
    last_active TIMESTAMP
);

-- Folders being managed
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_unique_id TEXT NOT NULL UNIQUE,
    folder_path TEXT NOT NULL,
    display_name TEXT NOT NULL,
    share_type TEXT DEFAULT 'private' CHECK(share_type IN ('public', 'private', 'protected')),
    private_key BLOB,
    public_key BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP,
    last_published TIMESTAMP,
    current_version INTEGER DEFAULT 1,
    total_files INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    state TEXT DEFAULT 'active' CHECK(state IN ('active', 'deleted', 'archived'))
);

-- Files within folders
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    segment_count INTEGER DEFAULT 0,
    state TEXT DEFAULT 'indexed' CHECK(state IN ('indexed', 'modified', 'deleted', 'uploading', 'uploaded')),
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, file_path, version)
);

-- Segments for files
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,
    segment_hash TEXT NOT NULL,
    segment_size INTEGER NOT NULL,
    subject_hash TEXT NOT NULL,
    message_id TEXT,
    newsgroup TEXT NOT NULL,
    uploaded_at TIMESTAMP,
    redundancy_index INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending' CHECK(state IN ('pending', 'uploading', 'uploaded', 'failed')),
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, segment_index, redundancy_index)
);

-- Folder versions for tracking
CREATE TABLE IF NOT EXISTS folder_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT, -- JSON
    segments_added INTEGER DEFAULT 0,
    segments_modified INTEGER DEFAULT 0,
    segments_deleted INTEGER DEFAULT 0,
    index_size INTEGER,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, version)
);

-- Change journal for incremental updates
CREATE TABLE IF NOT EXISTS change_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('added', 'modified', 'deleted')),
    old_version INTEGER,
    new_version INTEGER,
    old_hash TEXT,
    new_hash TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    segments_affected TEXT, -- JSON array
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Access control (local tracking only)
CREATE TABLE IF NOT EXISTS access_control_local (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE,
    UNIQUE(folder_id, user_id)
);

-- Published indexes
CREATE TABLE IF NOT EXISTS published_indexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    share_id TEXT NOT NULL UNIQUE,
    access_string TEXT NOT NULL,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_size INTEGER,
    segment_count INTEGER DEFAULT 1,
    share_type TEXT NOT NULL,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Download sessions
CREATE TABLE IF NOT EXISTS download_sessions (
    session_id TEXT PRIMARY KEY,
    access_string TEXT NOT NULL,
    folder_name TEXT,
    total_files INTEGER,
    total_size INTEGER,
    downloaded_files INTEGER DEFAULT 0,
    downloaded_size INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Download progress tracking
CREATE TABLE IF NOT EXISTS download_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    downloaded_size INTEGER DEFAULT 0,
    segment_count INTEGER,
    completed_segments INTEGER DEFAULT 0,
    state TEXT DEFAULT 'pending',
    error_count INTEGER DEFAULT 0,
    FOREIGN KEY(session_id) REFERENCES download_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, file_path)
);

-- Server configurations
CREATE TABLE IF NOT EXISTS server_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT,
    password TEXT,
    use_ssl BOOLEAN DEFAULT TRUE,
    max_connections INTEGER DEFAULT 10,
    priority INTEGER DEFAULT 1,
    enabled BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0
);

-- Upload queue (fixed structure for file-based uploads)
CREATE TABLE IF NOT EXISTS upload_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Publications table for shared folders
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id TEXT UNIQUE NOT NULL,
    folder_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    access_string TEXT NOT NULL,
    share_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_size INTEGER DEFAULT 0,
    FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id);
CREATE INDEX IF NOT EXISTS idx_files_state ON files(state);
CREATE INDEX IF NOT EXISTS idx_segments_file ON segments(file_id);
CREATE INDEX IF NOT EXISTS idx_segments_state ON segments(state);
CREATE INDEX IF NOT EXISTS idx_upload_queue_status ON upload_queue(status);
CREATE INDEX IF NOT EXISTS idx_upload_queue_folder ON upload_queue(folder_id);
CREATE INDEX IF NOT EXISTS idx_publications_folder ON publications(folder_id);
CREATE INDEX IF NOT EXISTS idx_publications_share ON publications(share_id);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS pending_uploads AS
SELECT 
    uq.task_id,
    uq.folder_id,
    uq.file_path,
    uq.status,
    uq.priority,
    uq.created_at,
    uq.retry_count,
    f.folder_unique_id,
    f.display_name as folder_name
FROM upload_queue uq
JOIN folders f ON uq.folder_id = f.id
WHERE uq.status = 'pending'
ORDER BY uq.priority DESC, uq.created_at ASC;

CREATE VIEW IF NOT EXISTS folder_summary AS
SELECT 
    f.id,
    f.folder_unique_id,
    f.display_name,
    f.share_type,
    f.current_version,
    COUNT(DISTINCT fi.id) as file_count,
    SUM(fi.file_size) as total_size,
    MAX(fi.modified_at) as last_modified
FROM folders f
LEFT JOIN files fi ON f.id = fi.folder_id
GROUP BY f.id;
