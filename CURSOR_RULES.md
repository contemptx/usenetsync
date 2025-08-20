# UsenetSync Cursor Rules — Live Testing with Real Usenet

## Core Principles
- **REAL COMPONENTS ONLY**: All tests use actual UsenetSync modules with live Usenet
- **news.newshosting.com:563** with SSL is the ONLY server
- **Zero mocks/stubs**: Every test hits real infrastructure
- **Project-specific**: Tests validate actual UsenetSync functionality

## Required Environment Configuration

```bash
# Newshosting Production Server (NEVER use test/mock servers)
NNTP_HOST=news.newshosting.com
NNTP_PORT=563
NNTP_SSL=true
NNTP_USERNAME=contemptx
NNTP_PASSWORD=Kia211101#
NNTP_GROUP=alt.binaries.test
NNTP_TIMEOUT_SECS=30

# UsenetSync Database
DATABASE_URL=postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync
USENETSYNC_DATABASE_TYPE=postgresql
USENETSYNC_DATABASE_HOST=localhost
USENETSYNC_DATABASE_PORT=5432
USENETSYNC_DATABASE_NAME=usenetsync
USENETSYNC_DATABASE_USER=usenetsync
USENETSYNC_DATABASE_PASSWORD=usenetsync123

# UsenetSync API
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
API_HOST=0.0.0.0
API_PORT=8000

# UsenetSync Frontend
FRONTEND_BASE_URL=http://localhost:5173
VITE_BACKEND_URL=http://localhost:8000

# UsenetSync Components
USENET_CLIENT_MODULE=unified.networking.real_nntp_client:RealNNTPClient
INDEXING_MODULE=unified.indexing.scanner:UnifiedIndexingScanner
SEGMENTATION_MODULE=unified.segmentation.processor:SegmentationProcessor
ENCRYPTION_MODULE=unified.security.encryption:UnifiedEncryption
```

## UsenetSync Test Requirements

### Must Test These Real Components:
1. **RealNNTPClient** - Connect to Newshosting, authenticate, post/retrieve
2. **UnifiedIndexingScanner** - Index real files from filesystem
3. **SegmentationProcessor** - Segment real files for Usenet posting
4. **UnifiedEncryption** - Encrypt/decrypt real data
5. **UnifiedDatabase** - Store/retrieve with PostgreSQL
6. **UnifiedAPIServer** - Real HTTP endpoints
7. **TauriBridge** - Real GUI command handling

### Test Scenarios (All Live):
- Post a real file to alt.binaries.test
- Retrieve and verify the posted file
- Create real user with encryption keys
- Index a real folder with files
- Segment files and track in database
- Share creation with access control
- Full upload/download cycle

## Enforcement Rules

### Always:
- ✅ Use `pynntp` as `nntp` (block nntplib)
- ✅ Connect to news.newshosting.com:563 with SSL
- ✅ Use real UsenetSync modules (no test doubles)
- ✅ PostgreSQL for all database operations
- ✅ Real file I/O (create actual test files)

### Never:
- ❌ Mock NNTP connections
- ❌ Skip tests due to missing resources
- ❌ Use SQLite in tests
- ❌ Ignore warnings
- ❌ Use fake/stub modules

## Test Categories

```python
# Markers for UsenetSync tests
markers =
    live_nntp: Tests that connect to real Newshosting server
    live_database: Tests that use real PostgreSQL
    live_indexing: Tests that index real files
    live_encryption: Tests that encrypt/decrypt real data
    live_api: Tests that hit real API endpoints
    live_e2e: Full end-to-end with all real components
```

## Validation Checklist
- [ ] Can post real article to alt.binaries.test
- [ ] Can retrieve posted article by Message-ID
- [ ] Can index folder with 10+ real files
- [ ] Can segment large file (>1MB) correctly
- [ ] Can encrypt/decrypt with real keys
- [ ] Can create share and access it
- [ ] API returns real data from database
- [ ] Frontend displays real Usenet articles