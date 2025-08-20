# Critical Fixes Implementation Plan

## 🚨 Priority 1: Security Issues

### 1.1 Remove sitecustomize.py with hardcoded credentials
```diff
- sitecustomize.py (DELETE ENTIRELY)
+ Move test logic to proper test files with env vars
```

### 1.2 Purge credentials from history
```bash
# Commands to execute after fixes:
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch sitecustomize.py' \
  --prune-empty --tag-name-filter cat -- --all
```

## 🗄️ Priority 2: Database Schema Unification

### 2.1 Consolidate to single schema source
```diff
# Move conflicting schema to legacy
- src/unified/database_schema.py
+ src/legacy/database_schema.py

# Use only src/unified/core/schema.py as source of truth
```

### 2.2 Fix table naming conflict (publications vs shares)
```diff
# In src/unified/core/schema.py - rename publications to shares for consistency
- 'publications': f"""
-     CREATE TABLE IF NOT EXISTS publications (
+ 'shares': f"""
+     CREATE TABLE IF NOT EXISTS shares (
          id {id_type},
          share_id VARCHAR(255) UNIQUE NOT NULL,
          folder_id {uuid_type} NOT NULL,
-         share_type VARCHAR(50) NOT NULL,
-         access_level VARCHAR(50) NOT NULL,
+         access_type VARCHAR(50) NOT NULL,  -- PUBLIC, PRIVATE, PROTECTED
+         owner_id VARCHAR(255) NOT NULL,
+         encrypted BOOLEAN DEFAULT FALSE,
+         password_hash TEXT,
+         allowed_users TEXT,  -- JSON array
+         access_string TEXT,
+         encrypted_index TEXT,
+         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+         expires_at TIMESTAMP,
          ...
      )
  """
```

### 2.3 Enable schema initialization
```diff
# In src/unified/main.py - UnifiedSystem.__init__
  def __init__(self):
      """Initialize unified system"""
      self._setup_logging()
      self.config = self._load_config()
      self.db = self._initialize_database()
-     # Disabled - we manage schema manually
-     # from .schema import UnifiedSchema
-     # schema = UnifiedSchema(self)
-     # schema.create_all_tables()
-     pass
+     # Initialize schema and run migrations
+     from unified.core.schema import UnifiedSchema
+     from unified.core.migrations import UnifiedMigrations
+     self.schema = UnifiedSchema(self.db)
+     self.schema.create_all_tables()
+     migrations = UnifiedMigrations(self.db)
+     migrations.migrate()
```

## 🔧 Priority 3: API/System Fixes

### 3.1 Initialize upload_queue
```diff
# In src/unified/main.py - UnifiedSystem.__init__
  def __init__(self):
      ...
      self.db = self._initialize_database()
      self.schema = UnifiedSchema(self.db)
      ...
+     # Initialize upload queue
+     from unified.upload.queue import UnifiedUploadQueue
+     self.upload_queue = UnifiedUploadQueue(self.db)
      
      # Initialize other components
      self.auth = UnifiedAuthentication(self.db)
      self.encryption = UnifiedEncryption()
```

### 3.2 Remove duplicate get_statistics
```diff
# In src/unified/main.py - remove the second definition
- def get_statistics(self) -> Dict[str, Any]:
-     """Get system statistics"""
-     return self.get_metrics()

# Keep only the comprehensive first definition
  def get_statistics(self) -> Dict[str, Any]:
      """Get system statistics"""
      db_stats = self.db.get_stats()
      schema_stats = self.schema.get_statistics()
      
      return {
          'total_files': db_stats.get('files', 0),
          'total_size': db_stats.get('total_size', 0),
          'total_shares': db_stats.get('shares', 0),
          'total_users': db_stats.get('users', 0),
          'database_size': db_stats.get('database_size', 0),
          'tables': schema_stats.get('tables', {}),
          'indexes': schema_stats.get('indexes', {})
      }
```

### 3.3 Fix API endpoints to use shares table
```diff
# In src/unified/api/server.py
  @self.app.get("/api/v1/shares/{share_id}")
  async def get_share(share_id: str):
      """Get share details"""
      try:
-         share = self.system.db.fetch_one(
-             "SELECT * FROM publications WHERE share_id = ?",
+         share = self.system.db.fetch_one(
+             "SELECT * FROM shares WHERE share_id = ?",
              (share_id,)
          )
```

## 🌉 Priority 4: GUI Bridge Alignment

### 4.1 Update bridge to use shares table
```diff
# In src/unified/gui_bridge/complete_tauri_bridge.py
  async def _get_shares(self, owner_id: str) -> List[Dict]:
      """Get all shares for a user"""
      shares = self.system.db.fetch_all("""
-         SELECT * FROM shares 
+         SELECT * FROM shares 
          WHERE owner_id = ? 
          ORDER BY created_at DESC
      """, (owner_id,))
```

### 4.2 Use high-level system methods
```diff
# In src/unified/gui_bridge/complete_tauri_bridge.py
  async def _index_folder(self, args: Dict) -> Dict:
      """Index a folder"""
      path = args['path']
      owner_id = args.get('owner_id', 'default')
      
-     # Direct scanner usage (wrong)
-     scanner = UnifiedScanner()
-     files = list(scanner.scan_folder(path, folder_id))
+     # Use system method
+     result = self.system.index_folder(path, owner_id)
      
-     return {'files_indexed': len(files)}
+     return result  # Already has files_indexed, total_size, etc.
```

## 🗑️ Priority 5: Legacy Code Isolation

### 5.1 Move legacy modules
```bash
# Create legacy directory
mkdir -p src/legacy

# Move old modules
mv src/folder_management src/legacy/
mv src/download/enhanced_download_system.py src/legacy/
mv src/upload/enhanced_upload_system.py src/legacy/
mv src/unified/database_schema.py src/legacy/
mv src/unified/gui_bridge/tauri_bridge.py src/legacy/
```

### 5.2 Update imports to remove legacy references
```diff
# Remove all imports of moved modules
- from folder_management import FolderManager
- from download.enhanced_download_system import EnhancedDownloadSystem
- from upload.enhanced_upload_system import EnhancedUploadSystem
```

## 🎨 Priority 6: Frontend Integration

### 6.1 Add missing API endpoints
```diff
# In src/unified/api/server.py - add new endpoints
+ @self.app.get("/api/v1/logs")
+ async def get_logs(limit: int = 100, level: str = None):
+     """Get recent logs"""
+     from unified.core.log_manager import LogManager
+     logs = LogManager.get_recent_logs(limit, level)
+     return {"logs": logs}
+ 
+ @self.app.get("/api/v1/search")
+ async def search(query: str, type: str = None):
+     """Search files and folders"""
+     results = self.system.search(query, type)
+     return {"results": results}
+ 
+ @self.app.get("/api/v1/network/connection_pool")
+ async def get_connection_pool():
+     """Get connection pool stats"""
+     from unified.networking.connection_pool import ConnectionPool
+     stats = ConnectionPool.get_stats()
+     return {"pool": stats}
```

### 6.2 Wire frontend components
```diff
# In usenet-sync-app/src/pages/Logs.tsx
  const loadLogs = async () => {
-     // TODO: Implement real-time log fetching from backend
-     await loadLogs();
+     const response = await fetch('/api/v1/logs');
+     const data = await response.json();
+     setLogs(data.logs);
  };
```

## 📦 Priority 7: Requirements Consolidation

### 7.1 Merge requirements files
```diff
# In requirements.txt - add missing packages
+ yenc==0.4.0
+ zstandard==0.22.0
+ numpy==1.26.4
+ psycopg2-binary==2.9.10

# Delete requirements_complete.txt
```

## 🧪 Priority 8: Test Fixes

### 8.1 Create proper test configuration
```python
# tests/test_config.py
import os
from dotenv import load_dotenv

load_dotenv('.env.test')  # Use test-specific env file

NNTP_HOST = os.getenv('NNTP_HOST', 'news.newshosting.com')
NNTP_PORT = int(os.getenv('NNTP_PORT', '563'))
NNTP_USERNAME = os.getenv('NNTP_USERNAME')
NNTP_PASSWORD = os.getenv('NNTP_PASSWORD')

if not all([NNTP_USERNAME, NNTP_PASSWORD]):
    raise ValueError("Set NNTP credentials in .env.test")
```

## 📋 Implementation Order

1. **IMMEDIATE**: Remove sitecustomize.py (security critical)
2. **Day 1**: Schema unification and migrations
3. **Day 1**: Fix UnifiedSystem initialization (upload_queue, schema)
4. **Day 2**: Update API/Bridge to use consistent schema
5. **Day 2**: Move legacy code to isolation
6. **Day 3**: Add missing API endpoints
7. **Day 3**: Update frontend integration
8. **Day 3**: Consolidate requirements

## ✅ Validation Checklist

- [ ] No hardcoded credentials in code
- [ ] Single schema source (src/unified/core/schema.py)
- [ ] All tables use 'shares' not 'publications'
- [ ] upload_queue initialized in UnifiedSystem
- [ ] No duplicate methods in UnifiedSystem
- [ ] Legacy code moved to src/legacy/
- [ ] Frontend TODOs replaced with API calls
- [ ] Single requirements.txt file
- [ ] All tests use environment variables
- [ ] Schema migrations run on startup

## 🚀 Quick Start After Fixes

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with real credentials

# 2. Initialize database
python -c "from unified.main import UnifiedSystem; UnifiedSystem()"

# 3. Start backend
python start_unified_backend.py

# 4. Start frontend
cd usenet-sync-app && npm run dev

# 5. Run tests
make test-all
```

## 🔍 Expected Outcomes

After implementing these fixes:
1. **Security**: No exposed credentials
2. **Consistency**: Single schema, consistent table names
3. **Functionality**: All API endpoints working
4. **Integration**: Frontend fully connected to backend
5. **Maintainability**: Clear separation of legacy code
6. **Testing**: Proper test isolation with env vars