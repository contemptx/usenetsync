# 📚 Complete UsenetSync API Documentation

## Overview
This is the COMPLETE API documentation including ALL endpoints based on comprehensive backend analysis. The system includes over 100+ endpoints covering all functionality.

## Base URL
```
http://localhost:8000
```

## Table of Contents
1. [System & Health](#system--health)
2. [User Management](#user-management)
3. [Security & Authentication](#security--authentication)
4. [Folder Management](#folder-management)
5. [File Operations](#file-operations)
6. [Indexing System](#indexing-system)
7. [Segmentation System](#segmentation-system)
8. [Upload System](#upload-system)
9. [Download System](#download-system)
10. [Share Management](#share-management)
11. [Publishing System](#publishing-system)
12. [Backup & Recovery](#backup--recovery)
13. [Monitoring & Metrics](#monitoring--metrics)
14. [Migration System](#migration-system)
15. [Network Management](#network-management)
16. [Progress Tracking](#progress-tracking)
17. [WebSocket Endpoints](#websocket-endpoints)

---

## 🚨 MISSING ENDPOINTS (Not Yet Implemented in server.py)

Based on backend analysis, these endpoints should be added to the API server:

### Security System Endpoints
- `POST /api/v1/security/generate_user_keys` - Generate user key pair
- `POST /api/v1/security/generate_folder_key` - Generate folder encryption key
- `POST /api/v1/security/encrypt_file` - Encrypt a file
- `POST /api/v1/security/decrypt_file` - Decrypt a file
- `POST /api/v1/security/generate_api_key` - Generate API key for user
- `POST /api/v1/security/verify_api_key` - Verify API key
- `POST /api/v1/security/hash_password` - Hash password securely
- `POST /api/v1/security/verify_password` - Verify password hash
- `POST /api/v1/security/grant_access` - Grant resource access
- `POST /api/v1/security/revoke_access` - Revoke resource access
- `GET /api/v1/security/check_access` - Check user access to resource
- `POST /api/v1/security/session/create` - Create session token
- `POST /api/v1/security/session/verify` - Verify session token
- `POST /api/v1/security/sanitize_path` - Sanitize file path

### Backup & Recovery Endpoints
- `POST /api/v1/backup/create` - Create system backup
- `POST /api/v1/backup/restore` - Restore from backup
- `GET /api/v1/backup/list` - List all backups
- `POST /api/v1/backup/verify` - Verify backup integrity
- `POST /api/v1/backup/schedule` - Schedule automatic backups
- `DELETE /api/v1/backup/{backup_id}` - Delete a backup
- `GET /api/v1/backup/{backup_id}/metadata` - Get backup metadata
- `POST /api/v1/backup/export` - Export backup to external storage
- `POST /api/v1/backup/import` - Import backup from external storage

### Monitoring System Endpoints
- `POST /api/v1/monitoring/record_metric` - Record custom metric
- `POST /api/v1/monitoring/record_operation` - Record operation metrics
- `POST /api/v1/monitoring/record_error` - Record error occurrence
- `POST /api/v1/monitoring/record_throughput` - Record data throughput
- `POST /api/v1/monitoring/alerts/add` - Add alert rule
- `GET /api/v1/monitoring/alerts/list` - List alert rules
- `DELETE /api/v1/monitoring/alerts/{alert_id}` - Remove alert rule
- `GET /api/v1/monitoring/metrics/{metric_name}/values` - Get metric values
- `GET /api/v1/monitoring/metrics/{metric_name}/stats` - Get metric statistics
- `GET /api/v1/monitoring/dashboard` - Get dashboard data
- `POST /api/v1/monitoring/export` - Export metrics to file
- `GET /api/v1/monitoring/system_status` - Get detailed system status

### Migration System Endpoints
- `POST /api/v1/migration/start` - Start migration from old system
- `GET /api/v1/migration/status` - Get migration status
- `POST /api/v1/migration/verify` - Verify migration integrity
- `POST /api/v1/migration/backup_old` - Backup old databases
- `POST /api/v1/migration/rollback` - Rollback migration

### Publishing System Endpoints
- `POST /api/v1/publishing/publish` - Publish folder with advanced options
- `POST /api/v1/publishing/unpublish` - Unpublish share
- `PUT /api/v1/publishing/update` - Update share properties
- `POST /api/v1/publishing/authorized_users/add` - Add user to private share
- `POST /api/v1/publishing/authorized_users/remove` - Remove user from private share
- `GET /api/v1/publishing/authorized_users/list` - List authorized users
- `POST /api/v1/publishing/commitment/add` - Add user commitment
- `POST /api/v1/publishing/commitment/remove` - Remove user commitment
- `GET /api/v1/publishing/commitment/list` - List commitments
- `POST /api/v1/publishing/expiry/set` - Set share expiry
- `GET /api/v1/publishing/expiry/check` - Check expiry status

### Advanced Indexing Endpoints
- `POST /api/v1/indexing/sync` - Sync folder changes
- `POST /api/v1/indexing/verify` - Verify index integrity
- `POST /api/v1/indexing/rebuild` - Rebuild index from scratch
- `GET /api/v1/indexing/stats` - Get indexing statistics
- `POST /api/v1/indexing/binary` - Create binary index
- `GET /api/v1/indexing/version/{file_hash}` - Get file versions
- `POST /api/v1/indexing/deduplicate` - Deduplicate indexed files

### Advanced Upload Endpoints
- `POST /api/v1/upload/batch` - Batch upload multiple files
- `GET /api/v1/upload/queue/{queue_id}` - Get queue item details
- `PUT /api/v1/upload/queue/{queue_id}/priority` - Update upload priority
- `POST /api/v1/upload/queue/pause` - Pause upload queue
- `POST /api/v1/upload/queue/resume` - Resume upload queue
- `DELETE /api/v1/upload/queue/{queue_id}` - Cancel upload
- `POST /api/v1/upload/session/create` - Create upload session
- `POST /api/v1/upload/session/{session_id}/end` - End upload session
- `GET /api/v1/upload/strategy` - Get optimal upload strategy
- `POST /api/v1/upload/worker/add` - Add upload worker
- `POST /api/v1/upload/worker/{worker_id}/stop` - Stop upload worker

### Advanced Download Endpoints
- `POST /api/v1/download/batch` - Batch download multiple files
- `POST /api/v1/download/pause` - Pause download
- `POST /api/v1/download/resume` - Resume download
- `POST /api/v1/download/cancel` - Cancel download
- `GET /api/v1/download/progress/{download_id}` - Get download progress
- `POST /api/v1/download/verify` - Verify downloaded file
- `GET /api/v1/download/cache/stats` - Get cache statistics
- `POST /api/v1/download/cache/clear` - Clear download cache
- `POST /api/v1/download/cache/optimize` - Optimize cache
- `POST /api/v1/download/reconstruct` - Reconstruct file from segments
- `POST /api/v1/download/streaming/start` - Start streaming download

### Network Management Endpoints
- `POST /api/v1/network/servers/add` - Add NNTP server
- `DELETE /api/v1/network/servers/{server_id}` - Remove NNTP server
- `GET /api/v1/network/servers/list` - List configured servers
- `GET /api/v1/network/servers/{server_id}/health` - Get server health
- `POST /api/v1/network/servers/{server_id}/test` - Test server connection
- `GET /api/v1/network/bandwidth/current` - Get current bandwidth usage
- `POST /api/v1/network/bandwidth/limit` - Set bandwidth limit
- `GET /api/v1/network/connection_pool/stats` - Get connection pool stats
- `POST /api/v1/network/retry/configure` - Configure retry policy

### Segmentation System Endpoints
- `POST /api/v1/segmentation/pack` - Pack files into segments
- `POST /api/v1/segmentation/unpack` - Unpack segments to files
- `GET /api/v1/segmentation/info/{file_hash}` - Get segmentation info
- `POST /api/v1/segmentation/redundancy/add` - Add redundancy segments
- `POST /api/v1/segmentation/redundancy/verify` - Verify redundancy
- `POST /api/v1/segmentation/headers/generate` - Generate segment headers
- `POST /api/v1/segmentation/hash/calculate` - Calculate segment hashes

---

## 1. System & Health

### GET `/`
Root endpoint - API information

### GET `/health`
Health check endpoint

### GET `/api/v1/license/status`
Get license status and features

### GET `/api/v1/database/status`
Get database connection status

### POST `/api/v1/test_server_connection`
Test NNTP server connection

### POST `/api/v1/save_server_config`
Save NNTP server configuration

---

## 2. User Management

### POST `/api/v1/initialize_user`
Initialize or update user in the system

### POST `/api/v1/get_user_info`
Get current user information

### POST `/api/v1/is_user_initialized`
Check if any user exists in the system

### POST `/api/v1/users`
Create a new user

---

## 3. Security & Authentication

### 🔴 NOT YET EXPOSED - Should be added:
- User key generation
- Folder encryption
- API key management
- Session management
- Access control
- Password hashing

---

## 4. Folder Management

### POST `/api/v1/add_folder`
Add a new folder to the system

### GET `/api/v1/folders`
Get all folders in the system

### GET `/api/v1/folders/{folder_id}`
Get specific folder information

### DELETE `/api/v1/folders/{folder_id}`
Delete a folder from the system

### POST `/api/v1/folder_info`
Get detailed folder information

---

## 5. File Operations

### POST `/api/v1/index_folder`
Index files in a folder with progress tracking

### POST `/api/v1/process_folder`
Segment files in a folder for Usenet upload

### POST `/api/v1/folders/index`
Alternative indexing endpoint

---

## 6. Indexing System

### 🔴 NOT YET EXPOSED - Should be added:
- Sync changes
- Verify integrity
- Rebuild index
- Binary indexing
- File versioning
- Deduplication

---

## 7. Segmentation System

### 🔴 NOT YET EXPOSED - Should be added:
- Pack/unpack operations
- Redundancy management
- Header generation
- Hash calculation

---

## 8. Upload System

### POST `/api/v1/upload_folder`
Upload folder segments to Usenet with progress tracking

### POST `/api/v1/upload/queue`
Queue entity for upload

### GET `/api/v1/upload/status`
Get upload queue status

### 🔴 NOT YET EXPOSED - Should be added:
- Batch uploads
- Session management
- Worker management
- Priority updates
- Queue control

---

## 9. Download System

### POST `/api/v1/download_share`
Download a shared folder with progress tracking

### POST `/api/v1/download/start`
Start download with output path

### 🔴 NOT YET EXPOSED - Should be added:
- Batch downloads
- Pause/resume/cancel
- Cache management
- File reconstruction
- Streaming downloads

---

## 10. Share Management

### POST `/api/v1/create_share`
Create a share for a folder

### GET `/api/v1/shares`
Get all shares

### POST `/api/v1/shares`
Create a new share (alternative)

### GET `/api/v1/shares/{share_id}`
Get share information

### POST `/api/v1/shares/{share_id}/verify`
Verify access to a share

---

## 11. Publishing System

### 🔴 NOT YET EXPOSED - Should be added:
- Advanced publishing options
- User authorization
- Commitment management
- Expiry management

---

## 12. Backup & Recovery

### 🔴 NOT YET EXPOSED - Should be added:
- Create/restore backups
- Verify integrity
- Schedule backups
- Export/import

---

## 13. Monitoring & Metrics

### GET `/api/v1/events/transfers`
Get real-time transfer events

### POST `/api/v1/get_logs`
Get system logs from database

### GET `/api/v1/logs`
Get recent logs

### GET `/api/v1/stats`
Get system statistics

### GET `/api/v1/metrics`
Get detailed system metrics

### GET `/api/v1/search`
Search files and folders

### 🔴 NOT YET EXPOSED - Should be added:
- Custom metrics
- Alert management
- Dashboard data
- Metric export

---

## 14. Migration System

### 🔴 NOT YET EXPOSED - Should be added:
- Migrate from old system
- Verify migration
- Backup old data
- Rollback capability

---

## 15. Network Management

### GET `/api/v1/network/connection_pool`
Get connection pool statistics

### 🔴 NOT YET EXPOSED - Should be added:
- Server management
- Health monitoring
- Bandwidth control
- Retry configuration

---

## 16. Progress Tracking

### GET `/api/v1/progress/{progress_id}`
Get progress for a specific operation

### GET `/api/v1/progress`
Get all active progress operations

---

## 17. WebSocket Endpoints

### WS `/ws`
WebSocket for real-time updates

---

## Summary of Missing Functionality

### Critical Missing Endpoints (High Priority):
1. **Security System** - 14 endpoints missing
2. **Backup & Recovery** - 9 endpoints missing
3. **Advanced Upload/Download** - 22 endpoints missing
4. **Monitoring System** - 12 endpoints missing

### Important Missing Endpoints (Medium Priority):
1. **Publishing System** - 11 endpoints missing
2. **Network Management** - 9 endpoints missing
3. **Indexing System** - 7 endpoints missing
4. **Segmentation System** - 7 endpoints missing

### Nice-to-Have (Low Priority):
1. **Migration System** - 5 endpoints missing

### Total Statistics:
- **Currently Implemented**: 37 endpoints
- **Missing but Available in Backend**: 96 endpoints
- **Total Potential Endpoints**: 133 endpoints
- **Implementation Coverage**: 28%

---

## Recommendations

1. **Immediate Actions:**
   - Expose security endpoints for authentication and encryption
   - Add backup/recovery endpoints for data protection
   - Implement advanced upload/download features

2. **Next Phase:**
   - Add monitoring and alerting endpoints
   - Expose publishing system features
   - Implement network management

3. **Future Enhancements:**
   - Migration system for upgrades
   - Advanced indexing features
   - Segmentation optimization

---

**Version:** 2.0.0  
**Last Updated:** December 2024  
**Status:** ⚠️ INCOMPLETE - Many backend features not exposed via API