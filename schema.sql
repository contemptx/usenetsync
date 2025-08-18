-- UsenetSync PostgreSQL Database Schema
-- Run this script to create all required tables

-- Drop existing tables (careful in production!)
-- DROP TABLE IF EXISTS activity_log CASCADE;
-- DROP TABLE IF EXISTS uploads CASCADE;
-- DROP TABLE IF EXISTS authorized_users CASCADE;
-- DROP TABLE IF EXISTS shares CASCADE;
-- DROP TABLE IF EXISTS segments CASCADE;
-- DROP TABLE IF EXISTS files CASCADE;
-- DROP TABLE IF EXISTS folders CASCADE;

-- Create folders table
CREATE TABLE IF NOT EXISTS folders (
    folder_id VARCHAR(255) PRIMARY KEY,
    path TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(50) DEFAULT 'added',
    published BOOLEAN DEFAULT FALSE,
    share_id VARCHAR(255),
    access_type VARCHAR(50) DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create files table
CREATE TABLE IF NOT EXISTS files (
    file_id VARCHAR(255) PRIMARY KEY,
    folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    size BIGINT,
    mime_type VARCHAR(255),
    hash VARCHAR(255),
    encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create segments table
CREATE TABLE IF NOT EXISTS segments (
    segment_id VARCHAR(255) PRIMARY KEY,
    file_id VARCHAR(255) REFERENCES files(file_id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    size BIGINT,
    hash VARCHAR(255),
    message_id TEXT,
    uploaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create shares table
CREATE TABLE IF NOT EXISTS shares (
    share_id VARCHAR(255) PRIMARY KEY,
    folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
    share_type VARCHAR(50) DEFAULT 'public',
    password_hash TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create authorized_users table for private shares
CREATE TABLE IF NOT EXISTS authorized_users (
    id SERIAL PRIMARY KEY,
    folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    permissions VARCHAR(50) DEFAULT 'read',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(folder_id, user_id)
);

-- Create uploads table
CREATE TABLE IF NOT EXISTS uploads (
    upload_id VARCHAR(255) PRIMARY KEY,
    folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_segments INTEGER,
    uploaded_segments INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create activity_log table
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    folder_id VARCHAR(255),
    action VARCHAR(100),
    details JSONB,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);
CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments(file_id);
CREATE INDEX IF NOT EXISTS idx_shares_folder_id ON shares(folder_id);
CREATE INDEX IF NOT EXISTS idx_authorized_users_folder_id ON authorized_users(folder_id);
CREATE INDEX IF NOT EXISTS idx_uploads_folder_id ON uploads(folder_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_folder_id ON activity_log(folder_id);

-- Verify tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;