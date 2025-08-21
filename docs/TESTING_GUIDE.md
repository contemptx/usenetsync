# UsenetSync Testing Guide

## 🔑 Configuration

### Live Newshosting Credentials
The system is configured to use **real** Newshosting credentials:
- **Server**: news.newshosting.com:563 (SSL)
- **Username**: contemptx
- **Password**: Kia211101#
- **Test Group**: alt.binaries.test

### Environment Setup
All credentials are configured in `.env`. The test framework enforces:
- ✅ SSL connection on port 563
- ✅ Real NNTP server (news.newshosting.com)
- ✅ No mocks or stubs
- ✅ PostgreSQL database (no SQLite in tests)

## 🧪 Test Categories

### 1. Setup Tests (`test_setup.py`)
Verifies environment configuration:
```bash
make test-setup
```

### 2. Live NNTP Tests (`test_usenet_live.py`)
Tests with real Newshosting server:
- Real connection and authentication
- Post articles to alt.binaries.test
- Retrieve posted articles
- File segmentation for Usenet
- Folder indexing
- Encryption/decryption

```bash
make test-live
```

### 3. Integration Tests (`test_integration.py`)
Complete workflow tests:
- User creation → Folder indexing → Upload → Share
- API server integration
- GUI bridge integration
- Access control workflows

```bash
make test-integration
```

### 4. End-to-End Tests (`test_e2e.py`)
Full stack tests from frontend to Usenet:
- Complete user journey
- API to NNTP flow
- GUI to backend flow

```bash
make test-all
```

## 🚀 Quick Start

### Run All Tests
```bash
make live
```

This will:
1. Start PostgreSQL
2. Run database migrations
3. Execute all test suites
4. Connect to real Newshosting server

### Run Specific Test
```bash
./run_tests.sh tests/test_usenet_live.py::TestUsenetSyncLive::test_real_nntp_connection -v
```

## 📊 Test Components

### Real Components Being Tested
1. **RealNNTPClient** - Actual NNTP operations with pynntp
2. **UnifiedScanner** - Real file system scanning
3. **UnifiedSegmentProcessor** - Real file segmentation
4. **UnifiedEncryption** - Real encryption/decryption
5. **UnifiedDatabase** - Real PostgreSQL operations
6. **UnifiedAPIServer** - Real HTTP endpoints
7. **CompleteTauriBridge** - Real GUI command handling

### Test Data
- Creates real test files in temporary directories
- Posts real articles to alt.binaries.test
- Stores real data in PostgreSQL
- Uses real encryption keys

## ⚠️ Important Notes

### Rate Limiting
Newshosting may rate limit if too many articles are posted quickly. Tests include delays to respect server limits.

### Article Propagation
Posted articles may take a few seconds to propagate and be retrievable. This is normal Usenet behavior.

### Database State
Tests create real data in PostgreSQL. The database is not automatically cleaned between test runs.

### No Mocks Policy
The test framework **blocks** nntplib and enforces pynntp usage. Any attempt to mock NNTP connections will fail.

## 🔧 Troubleshooting

### Connection Issues
If tests fail to connect:
1. Verify credentials in `.env`
2. Check network connectivity to news.newshosting.com
3. Ensure port 563 is not blocked

### Database Issues
If database tests fail:
```bash
make db-migrate  # Reset database schema
```

### Module Import Issues
If modules can't be imported:
```bash
export PYTHONPATH=/workspace/src:$PYTHONPATH
```

## 📈 Test Metrics

Current test coverage includes:
- **NNTP Operations**: Connect, authenticate, post, retrieve
- **File Operations**: Index, segment, encrypt
- **Database Operations**: CRUD with PostgreSQL
- **API Endpoints**: Health, stats, user management
- **GUI Commands**: 15+ Tauri bridge commands

## 🎯 Test Philosophy

UsenetSync tests follow these principles:
1. **Real Components Only** - No mocks, stubs, or fixtures
2. **Live Infrastructure** - Real Newshosting server, real database
3. **Complete Workflows** - Test entire user journeys
4. **Zero Warnings** - Treat all warnings as errors
5. **Fail Fast** - Missing requirements = test failure (no skips)

## 📝 Adding New Tests

When adding tests, ensure they:
1. Use real components from `unified.*` modules
2. Connect to news.newshosting.com:563
3. Create real test data
4. Clean up after themselves
5. Include appropriate pytest markers

Example:
```python
@pytest.mark.live_nntp
def test_new_feature(real_nntp_client, newshosting_connection):
    client = real_nntp_client()
    client.connect(**newshosting_connection)
    # Test with real NNTP operations
```

## 🏁 Continuous Integration

The GitHub workflow (`.github/workflows/live-fullstack.yml`) runs all tests on push/PR with real Newshosting connection. Ensure secrets are configured in repository settings.

## 📞 Support

For issues with:
- **Newshosting**: Check account status at newshosting.com
- **Tests**: Review this guide and check `.env` configuration
- **UsenetSync**: Check component documentation in `/workspace/src/unified/`