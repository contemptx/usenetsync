# UsenetSync API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core APIs](#core-apis)
4. [Tauri Commands](#tauri-commands)
5. [Python CLI](#python-cli)
6. [Error Handling](#error-handling)

## Overview

UsenetSync provides multiple API interfaces:
- **Tauri Commands**: Frontend-to-backend communication
- **Python CLI**: Command-line interface for backend operations
- **REST API**: (Future) HTTP API for remote access

## Authentication

### License Management
The application uses TurboActivate for license management:

```typescript
// Activate license
await activateLicense(licenseKey: string): Promise<boolean>

// Check license status
await checkLicense(): Promise<LicenseStatus>

// Deactivate license
await deactivateLicense(): Promise<void>
```

## Core APIs

### File Operations

#### Upload File
```typescript
interface UploadRequest {
  filePath: string;
  shareId?: string;
  password?: string;
  encryption?: boolean;
}

async function uploadFile(request: UploadRequest): Promise<UploadResult>
```

**Response:**
```typescript
interface UploadResult {
  success: boolean;
  shareId: string;
  fileId: string;
  articleIds: string[];
  encryptionKey?: string;
}
```

#### Download File
```typescript
interface DownloadRequest {
  shareId: string;
  destination: string;
  password?: string;
}

async function downloadFile(request: DownloadRequest): Promise<DownloadResult>
```

**Response:**
```typescript
interface DownloadResult {
  success: boolean;
  files: FileInfo[];
  totalSize: number;
  downloadTime: number;
}
```

### Share Management

#### Create Share
```typescript
interface CreateShareRequest {
  files: string[];
  type: 'public' | 'private' | 'protected';
  password?: string;
  expiresIn?: number; // hours
  title?: string;
  description?: string;
}

async function createShare(request: CreateShareRequest): Promise<Share>
```

**Response:**
```typescript
interface Share {
  shareId: string;
  url: string;
  qrCode: string;
  type: string;
  fileCount: number;
  totalSize: number;
  createdAt: string;
  expiresAt?: string;
}
```

#### Get Share Details
```typescript
async function getShareDetails(shareId: string): Promise<ShareDetails>
```

#### Delete Share
```typescript
async function deleteShare(shareId: string): Promise<boolean>
```

#### List Shares
```typescript
interface ListSharesOptions {
  limit?: number;
  offset?: number;
  sortBy?: 'created' | 'size' | 'downloads';
  order?: 'asc' | 'desc';
}

async function listShares(options?: ListSharesOptions): Promise<ShareList>
```

### Settings Management

#### Get Settings
```typescript
async function getSettings(): Promise<Settings>

interface Settings {
  servers: ServerConfig[];
  bandwidth: BandwidthSettings;
  encryption: EncryptionSettings;
  cache: CacheSettings;
  ui: UISettings;
}
```

#### Update Settings
```typescript
async function updateSettings(settings: Partial<Settings>): Promise<Settings>
```

### Server Management

#### Add Server
```typescript
interface ServerConfig {
  hostname: string;
  port: number;
  username: string;
  password: string;
  ssl: boolean;
  maxConnections?: number;
  priority?: number;
}

async function addServer(config: ServerConfig): Promise<boolean>
```

#### Test Server Connection
```typescript
async function testServerConnection(serverId: string): Promise<ConnectionTestResult>

interface ConnectionTestResult {
  success: boolean;
  latency: number;
  capabilities: string[];
  error?: string;
}
```

#### Remove Server
```typescript
async function removeServer(serverId: string): Promise<boolean>
```

### Bandwidth Control

#### Set Bandwidth Limits
```typescript
interface BandwidthLimits {
  uploadKbps: number;
  downloadKbps: number;
  enabled: boolean;
}

async function setBandwidthLimit(limits: BandwidthLimits): Promise<void>
```

#### Get Bandwidth Statistics
```typescript
async function getBandwidthStats(): Promise<BandwidthStats>

interface BandwidthStats {
  currentUpload: number;
  currentDownload: number;
  averageUpload: number;
  averageDownload: number;
  totalUploaded: number;
  totalDownloaded: number;
}
```

### System Operations

#### Get System Information
```typescript
async function getSystemInfo(): Promise<SystemInfo>

interface SystemInfo {
  version: string;
  platform: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  uptime: number;
}
```

#### Get Logs
```typescript
interface LogFilter {
  level?: 'debug' | 'info' | 'warn' | 'error';
  component?: string;
  startDate?: string;
  endDate?: string;
  limit?: number;
}

async function getLogs(filter?: LogFilter): Promise<LogEntry[]>
```

#### Clear Cache
```typescript
async function clearCache(type?: 'all' | 'files' | 'shares' | 'thumbnails'): Promise<void>
```

#### Export Data
```typescript
interface ExportOptions {
  format: 'json' | 'csv' | 'zip';
  includeSettings: boolean;
  includeShares: boolean;
  includeLogs: boolean;
}

async function exportData(options: ExportOptions): Promise<Blob>
```

#### Import Data
```typescript
async function importData(data: File, options?: ImportOptions): Promise<ImportResult>
```

## Tauri Commands

All Tauri commands are invoked through the `invoke` function:

```typescript
import { invoke } from '@tauri-apps/api/tauri';

// Example usage
const result = await invoke('command_name', { param1: value1, param2: value2 });
```

### Available Commands

| Command | Parameters | Returns | Description |
|---------|------------|---------|-------------|
| `create_share` | `files: string[], shareType: string, password?: string` | `Share` | Create a new share |
| `download_share` | `shareId: string, destination: string, password?: string` | `boolean` | Download a share |
| `get_system_stats` | - | `SystemStats` | Get system statistics |
| `select_files` | - | `FileNode[]` | Open file selection dialog |
| `activate_license` | `key: string` | `boolean` | Activate license |
| `check_license` | - | `LicenseStatus` | Check license status |
| `start_trial` | - | `number` | Start trial period |
| `deactivate_license` | - | `void` | Deactivate license |
| `get_logs` | `filter?: LogFilter` | `LogEntry[]` | Get system logs |
| `set_bandwidth_limit` | `uploadKbps: number, downloadKbps: number, enabled: boolean` | `void` | Set bandwidth limits |
| `get_bandwidth_stats` | - | `BandwidthStats` | Get bandwidth statistics |
| `export_data` | `options: ExportOptions` | `string` | Export application data |
| `import_data` | `data: string, options?: ImportOptions` | `boolean` | Import application data |
| `clear_cache` | - | `void` | Clear application cache |
| `restart_services` | - | `void` | Restart backend services |

## Python CLI

The Python CLI provides command-line access to all backend functionality:

### Basic Usage
```bash
python src/cli.py [command] [options]
```

### Commands

#### Create Share
```bash
python src/cli.py create-share \
  --files file1.txt file2.pdf \
  --type public \
  --password "optional_password" \
  --title "My Share" \
  --description "Share description"
```

#### Download Share
```bash
python src/cli.py download-share \
  --share-id SHARE123 \
  --destination /path/to/download \
  --password "optional_password"
```

#### List Shares
```bash
python src/cli.py list-shares \
  --limit 10 \
  --sort-by created
```

#### Test Connection
```bash
python src/cli.py test-connection \
  --server news.example.com \
  --port 563 \
  --ssl
```

#### Configuration
```bash
# Set configuration
python src/cli.py config set \
  --key server.hostname \
  --value news.example.com

# Get configuration
python src/cli.py config get --key server.hostname

# List all configuration
python src/cli.py config list
```

## Error Handling

### Error Response Format
All API errors follow a consistent format:

```typescript
interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_REQUIRED` | Authentication required | 401 |
| `LICENSE_INVALID` | Invalid or expired license | 403 |
| `SHARE_NOT_FOUND` | Share ID not found | 404 |
| `FILE_NOT_FOUND` | File not found | 404 |
| `INVALID_PASSWORD` | Incorrect password | 401 |
| `ENCRYPTION_ERROR` | Encryption/decryption failed | 500 |
| `NNTP_ERROR` | NNTP server error | 502 |
| `BANDWIDTH_EXCEEDED` | Bandwidth limit exceeded | 429 |
| `STORAGE_FULL` | Storage quota exceeded | 507 |
| `INVALID_REQUEST` | Invalid request parameters | 400 |
| `SERVER_ERROR` | Internal server error | 500 |

### Error Handling Examples

#### TypeScript/Frontend
```typescript
try {
  const result = await invoke('create_share', {
    files: selectedFiles,
    shareType: 'public'
  });
  console.log('Share created:', result.shareId);
} catch (error) {
  if (error.code === 'LICENSE_INVALID') {
    // Handle license error
    showLicenseDialog();
  } else {
    // Handle other errors
    showErrorMessage(error.message);
  }
}
```

#### Python/Backend
```python
try:
    share = share_manager.create_share(
        files=file_list,
        share_type='public',
        password=password
    )
    return {'success': True, 'share_id': share.id}
except EncryptionError as e:
    return {'success': False, 'error': 'ENCRYPTION_ERROR', 'message': str(e)}
except NNTPError as e:
    return {'success': False, 'error': 'NNTP_ERROR', 'message': str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {'success': False, 'error': 'SERVER_ERROR', 'message': 'Internal server error'}
```

## Rate Limiting

API calls are subject to rate limiting:

- **Default limits**: 100 requests per minute
- **Upload/Download**: Subject to bandwidth throttling
- **Search**: 10 requests per minute
- **Share creation**: 20 per hour

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## WebSocket Events

For real-time updates, the application supports WebSocket connections:

### Connection
```typescript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleEvent(data);
};
```

### Event Types

| Event | Data | Description |
|-------|------|-------------|
| `upload.progress` | `{fileId, progress, speed}` | Upload progress update |
| `download.progress` | `{shareId, progress, speed}` | Download progress update |
| `share.created` | `{shareId, url}` | New share created |
| `share.deleted` | `{shareId}` | Share deleted |
| `server.connected` | `{serverId, hostname}` | Server connected |
| `server.disconnected` | `{serverId, reason}` | Server disconnected |
| `bandwidth.update` | `{upload, download}` | Bandwidth usage update |

## Pagination

List endpoints support pagination:

```typescript
interface PaginationParams {
  limit: number;   // Items per page (default: 20, max: 100)
  offset: number;  // Starting position (default: 0)
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
```

Example:
```typescript
const shares = await listShares({
  limit: 20,
  offset: 40  // Page 3 (assuming 20 items per page)
});
```

## Versioning

The API uses semantic versioning. The current version is included in:
- Response header: `X-API-Version: 1.0.0`
- System info: `getSystemInfo().version`

## Security

### HTTPS/TLS
All production API calls should use HTTPS with TLS 1.2 or higher.

### Authentication Token
After license activation, an authentication token is generated:
```typescript
const token = await getAuthToken();
// Include in headers: Authorization: Bearer <token>
```

### CORS
Cross-Origin Resource Sharing (CORS) is configured for:
- Allowed origins: Configured in settings
- Allowed methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed headers: Content-Type, Authorization

### Input Validation
All inputs are validated against:
- Type constraints
- Length limits
- Pattern matching (regex)
- SQL injection prevention
- XSS prevention

## Support

For API support and questions:
- GitHub Issues: https://github.com/contemptx/usenetsync/issues
- Documentation: https://github.com/contemptx/usenetsync/wiki
- Email: support@usenetsync.com