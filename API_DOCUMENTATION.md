# 📚 UsenetSync API Documentation

## Base URL
```
http://localhost:8000
```

## Table of Contents
- [System Endpoints](#system-endpoints)
- [User Management](#user-management)
- [Folder Management](#folder-management)
- [File Operations](#file-operations)
- [Share Management](#share-management)
- [Upload/Download](#uploaddownload)
- [Progress Tracking](#progress-tracking)
- [Monitoring & Logs](#monitoring--logs)

---

## System Endpoints

### GET `/`
**Description:** Root endpoint - API information  
**Response:**
```json
{
  "name": "Unified UsenetSync API",
  "version": "1.0.0",
  "status": "operational"
}
```

### GET `/health`
**Description:** Health check endpoint  
**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600,
  "database": "connected"
}
```

### GET `/api/v1/license/status`
**Description:** Get license status and features  
**Response:**
```json
{
  "status": "active",
  "type": "trial",
  "expires_at": "2025-12-31T23:59:59Z",
  "features": ["all"]
}
```

### GET `/api/v1/database/status`
**Description:** Get database connection status  
**Response:**
```json
{
  "connected": true,
  "type": "sqlite",
  "path": "/workspace/backend/data/usenetsync.db"
}
```

---

## User Management

### POST `/api/v1/initialize_user`
**Description:** Initialize or update user in the system  
**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com"
}
```
**Response:**
```json
{
  "success": true,
  "user_id": "uuid-here",
  "message": "User initialized successfully"
}
```

### POST `/api/v1/get_user_info`
**Description:** Get current user information  
**Response:**
```json
{
  "user_id": "uuid-here",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### POST `/api/v1/is_user_initialized`
**Description:** Check if any user exists in the system  
**Response:**
```json
{
  "initialized": true,
  "user_count": 1
}
```

### POST `/api/v1/users`
**Description:** Create a new user  
**Query Parameters:**
- `username` (string, required): Username
- `email` (string, optional): Email address

**Response:**
```json
{
  "id": "uuid-here",
  "username": "john_doe",
  "email": "john@example.com"
}
```

---

## Folder Management

### POST `/api/v1/add_folder`
**Description:** Add a new folder to the system  
**Request Body:**
```json
{
  "path": "/path/to/folder"
}
```
**Response:**
```json
{
  "success": true,
  "folder_id": "uuid-here",
  "path": "/path/to/folder",
  "message": "Folder added successfully"
}
```

### GET `/api/v1/folders`
**Description:** Get all folders in the system  
**Response:**
```json
{
  "folders": [
    {
      "folder_id": "uuid-here",
      "path": "/path/to/folder",
      "name": "folder_name",
      "status": "indexed",
      "file_count": 10,
      "total_size": 1048576,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### GET `/api/v1/folders/{folder_id}`
**Description:** Get specific folder information  
**Path Parameters:**
- `folder_id` (string): Folder UUID

**Response:**
```json
{
  "folder_id": "uuid-here",
  "path": "/path/to/folder",
  "status": "indexed",
  "file_count": 10,
  "segment_count": 50,
  "total_size": 1048576,
  "last_indexed": "2024-01-01T00:00:00Z"
}
```

### DELETE `/api/v1/folders/{folder_id}`
**Description:** Delete a folder from the system  
**Path Parameters:**
- `folder_id` (string): Folder UUID

**Response:**
```json
{
  "success": true,
  "message": "Folder deleted"
}
```

### POST `/api/v1/folder_info`
**Description:** Get detailed folder information  
**Request Body:**
```json
{
  "folderId": "uuid-here"
}
```
**Response:**
```json
{
  "folder": {
    "folder_id": "uuid-here",
    "path": "/path/to/folder",
    "status": "indexed",
    "files": 10,
    "segments": 50
  }
}
```

---

## File Operations

### POST `/api/v1/index_folder`
**Description:** Index files in a folder with progress tracking  
**Request Body:**
```json
{
  "folderId": "uuid-here"
}
```
OR
```json
{
  "folderPath": "/path/to/folder"
}
```
**Response:**
```json
{
  "success": true,
  "files_indexed": 10,
  "progress_id": "index_uuid_timestamp",
  "message": "Indexing started"
}
```

### POST `/api/v1/process_folder`
**Description:** Segment files in a folder for Usenet upload  
**Request Body:**
```json
{
  "folderId": "uuid-here"
}
```
**Response:**
```json
{
  "success": true,
  "segments_created": 50,
  "progress_id": "segment_uuid_timestamp",
  "message": "Segmentation started"
}
```

### POST `/api/v1/folders/index`
**Description:** Alternative indexing endpoint  
**Query Parameters:**
- `folder_path` (string): Path to folder
- `owner_id` (string): Owner UUID

**Response:**
```json
{
  "success": true,
  "folder_id": "uuid-here"
}
```

---

## Upload/Download

### POST `/api/v1/upload_folder`
**Description:** Upload folder segments to Usenet with progress tracking  
**Request Body:**
```json
{
  "folderId": "uuid-here"
}
```
**Response:**
```json
{
  "success": true,
  "segments_uploaded": 50,
  "progress_id": "upload_uuid_timestamp",
  "message": "Upload started"
}
```

### POST `/api/v1/upload/queue`
**Description:** Queue entity for upload  
**Query Parameters:**
- `entity_id` (string): Entity UUID
- `entity_type` (string): Type (file/folder/segment)
- `priority` (int, optional): Priority 1-10, default 5

**Response:**
```json
{
  "success": true,
  "queue_id": "uuid-here",
  "position": 1
}
```

### GET `/api/v1/upload/status`
**Description:** Get upload queue status  
**Response:**
```json
{
  "pending": 10,
  "uploading": 2,
  "completed": 100,
  "failed": 1
}
```

### POST `/api/v1/download_share`
**Description:** Download a shared folder with progress tracking  
**Request Body:**
```json
{
  "share_id": "SHARE-ABC123"
}
```
**Response:**
```json
{
  "success": true,
  "segments_downloaded": 50,
  "progress_id": "download_uuid_timestamp",
  "message": "Download started"
}
```

### POST `/api/v1/download/start`
**Description:** Start download with output path  
**Query Parameters:**
- `share_id` (string): Share ID
- `output_path` (string): Where to save files

**Response:**
```json
{
  "success": true,
  "download_id": "uuid-here"
}
```

---

## Share Management

### POST `/api/v1/create_share`
**Description:** Create a share for a folder  
**Request Body:**
```json
{
  "folder_id": "uuid-here",
  "access_level": "public",
  "password": "optional_password"
}
```
**Response:**
```json
{
  "success": true,
  "share_id": "SHARE-ABC123",
  "url": "https://usenet-share.com/d/SHARE-ABC123"
}
```

### GET `/api/v1/shares`
**Description:** Get all shares  
**Response:**
```json
{
  "shares": [
    {
      "share_id": "SHARE-ABC123",
      "folder_id": "uuid-here",
      "access_level": "public",
      "download_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST `/api/v1/shares`
**Description:** Create a new share  
**Query Parameters:**
- `folder_id` (string): Folder UUID
- `access_level` (string, optional): public/private/protected
- `password` (string, optional): For protected shares
- `expires_days` (int, optional): Expiration in days

**Response:**
```json
{
  "share_id": "SHARE-ABC123",
  "folder_id": "uuid-here",
  "access_level": "public",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### GET `/api/v1/shares/{share_id}`
**Description:** Get share information  
**Path Parameters:**
- `share_id` (string): Share ID

**Response:**
```json
{
  "share_id": "SHARE-ABC123",
  "folder_id": "uuid-here",
  "access_level": "public",
  "download_count": 5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### POST `/api/v1/shares/{share_id}/verify`
**Description:** Verify access to a share  
**Path Parameters:**
- `share_id` (string): Share ID

**Query Parameters:**
- `password` (string, optional): For protected shares

**Response:**
```json
{
  "access_granted": true,
  "folder_id": "uuid-here"
}
```

---

## Progress Tracking

### GET `/api/v1/progress/{progress_id}`
**Description:** Get progress for a specific operation  
**Path Parameters:**
- `progress_id` (string): Progress ID from operation

**Response:**
```json
{
  "operation": "indexing",
  "total": 100,
  "current": 45,
  "percentage": 45,
  "status": "processing",
  "message": "Indexing file 45/100: document.pdf"
}
```

### GET `/api/v1/progress`
**Description:** Get all active progress operations  
**Response:**
```json
{
  "operations": {
    "index_uuid_timestamp": {
      "operation": "indexing",
      "percentage": 45,
      "status": "processing"
    },
    "upload_uuid_timestamp": {
      "operation": "uploading",
      "percentage": 80,
      "status": "processing"
    }
  }
}
```

---

## Monitoring & Logs

### GET `/api/v1/events/transfers`
**Description:** Get real-time transfer events  
**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "type": "upload",
      "file": "document.pdf",
      "progress": 45,
      "speed": "1.5 MB/s",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST `/api/v1/get_logs`
**Description:** Get system logs from database  
**Request Body:**
```json
{
  "limit": 100,
  "level": "info"
}
```
**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "info",
      "message": "System started"
    }
  ]
}
```

### GET `/api/v1/logs`
**Description:** Get recent logs  
**Query Parameters:**
- `limit` (int, optional): Number of logs, default 100
- `level` (string, optional): Log level filter

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "info",
      "message": "Operation completed"
    }
  ]
}
```

### GET `/api/v1/stats`
**Description:** Get system statistics  
**Response:**
```json
{
  "folders": 10,
  "files": 1000,
  "segments": 5000,
  "shares": 50,
  "total_size": 10737418240,
  "uploads_today": 100,
  "downloads_today": 50
}
```

### GET `/api/v1/metrics`
**Description:** Get detailed system metrics  
**Response:**
```json
{
  "cpu_usage": 15.5,
  "memory_usage": 45.2,
  "disk_usage": 60.0,
  "network": {
    "upload_speed": "1.5 MB/s",
    "download_speed": "3.0 MB/s"
  },
  "database": {
    "size": 104857600,
    "connections": 5
  }
}
```

### GET `/api/v1/search`
**Description:** Search files and folders  
**Query Parameters:**
- `query` (string): Search query
- `type` (string, optional): file/folder/share
- `limit` (int, optional): Max results, default 50

**Response:**
```json
{
  "results": [
    {
      "type": "file",
      "id": "uuid-here",
      "name": "document.pdf",
      "path": "/folder/document.pdf",
      "size": 1048576
    }
  ],
  "total": 25
}
```

---

## Server Configuration

### POST `/api/v1/test_server_connection`
**Description:** Test NNTP server connection  
**Request Body:**
```json
{
  "server": "news.newshosting.com",
  "port": 563,
  "ssl": true,
  "username": "user",
  "password": "pass"
}
```
**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "server_info": {
    "welcome": "200 News.Newshosting.com"
  }
}
```

### POST `/api/v1/save_server_config`
**Description:** Save NNTP server configuration  
**Request Body:**
```json
{
  "server": "news.newshosting.com",
  "port": 563,
  "ssl": true,
  "username": "user",
  "password": "pass"
}
```
**Response:**
```json
{
  "success": true,
  "message": "Configuration saved"
}
```

### GET `/api/v1/network/connection_pool`
**Description:** Get connection pool statistics  
**Response:**
```json
{
  "active": 5,
  "idle": 10,
  "total": 15,
  "max": 20
}
```

---

## WebSocket Endpoints

### WS `/ws`
**Description:** WebSocket for real-time updates  
**Message Format:**
```json
{
  "type": "progress",
  "data": {
    "operation": "upload",
    "progress": 45,
    "message": "Uploading segment 45/100"
  }
}
```

**Event Types:**
- `progress`: Operation progress updates
- `status`: System status changes
- `transfer`: Transfer events
- `log`: Real-time logs

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

**Common Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

---

## Authentication

Currently, the API does not require authentication for most endpoints. In production, you should implement:
- API key authentication
- JWT tokens
- OAuth2

---

## Rate Limiting

No rate limiting is currently implemented. In production, consider:
- 100 requests per minute for general endpoints
- 10 requests per minute for heavy operations (indexing, uploading)

---

## Examples

### Complete Workflow Example

1. **Add a folder:**
```bash
curl -X POST http://localhost:8000/api/v1/add_folder \
  -H "Content-Type: application/json" \
  -d '{"path": "/my/folder"}'
```

2. **Index the folder:**
```bash
curl -X POST http://localhost:8000/api/v1/index_folder \
  -H "Content-Type: application/json" \
  -d '{"folderId": "uuid-here"}'
```

3. **Check progress:**
```bash
curl http://localhost:8000/api/v1/progress/index_uuid_timestamp
```

4. **Segment files:**
```bash
curl -X POST http://localhost:8000/api/v1/process_folder \
  -H "Content-Type: application/json" \
  -d '{"folderId": "uuid-here"}'
```

5. **Upload to Usenet:**
```bash
curl -X POST http://localhost:8000/api/v1/upload_folder \
  -H "Content-Type: application/json" \
  -d '{"folderId": "uuid-here"}'
```

6. **Create share:**
```bash
curl -X POST http://localhost:8000/api/v1/create_share \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "uuid-here", "access_level": "public"}'
```

7. **Download share:**
```bash
curl -X POST http://localhost:8000/api/v1/download_share \
  -H "Content-Type: application/json" \
  -d '{"share_id": "SHARE-ABC123"}'
```

---

## Notes

- All timestamps are in ISO 8601 format
- All sizes are in bytes unless otherwise specified
- UUIDs are used for all entity IDs
- Share IDs follow the format: `SHARE-[8-12 chars]`
- Progress IDs include operation type and timestamp

---

**Version:** 1.0.0  
**Last Updated:** December 2024