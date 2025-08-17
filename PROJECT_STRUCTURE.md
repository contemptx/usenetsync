# UsenetSync Project Structure

## Overview
The UsenetSync project has been reorganized into a clean, modular structure for better maintainability and testing.

## Directory Structure

```
/workspace/
├── src/                    # Source code
│   ├── core/              # Core application logic
│   │   ├── main.py        # Main application entry point
│   │   └── usenet_sync_integrated.py  # Integrated sync system
│   │
│   ├── networking/        # Network and NNTP components
│   │   ├── production_nntp_client.py  # NNTP client implementation
│   │   └── connection_pool.py         # Connection pool management
│   │
│   ├── database/          # Database layer
│   │   ├── production_db_wrapper.py      # Production database wrapper
│   │   ├── enhanced_database_manager.py  # Enhanced database manager
│   │   └── init_database.py             # Database initialization
│   │
│   ├── security/          # Security and encryption
│   │   ├── enhanced_security_system.py  # Main security system
│   │   ├── user_management.py          # User management
│   │   └── encrypted_index_cache.py    # Encrypted caching
│   │
│   ├── upload/            # Upload system
│   │   ├── enhanced_upload_system.py   # Upload system
│   │   ├── upload_queue_manager.py     # Queue management
│   │   ├── segment_packing_system.py   # Segment packing
│   │   └── publishing_system.py        # Publishing shares
│   │
│   ├── download/          # Download system
│   │   ├── enhanced_download_system.py    # Download system
│   │   └── segment_retrieval_system.py    # Segment retrieval
│   │
│   ├── indexing/          # File indexing
│   │   ├── versioned_core_index_system.py  # Version control indexing
│   │   ├── simplified_binary_index.py      # Binary indexing
│   │   └── share_id_generator.py          # Share ID generation
│   │
│   ├── monitoring/        # Monitoring and logging
│   │   ├── monitoring_system.py         # Main monitoring
│   │   ├── monitoring_dashboard.py      # Dashboard
│   │   ├── monitoring_cli.py           # CLI monitoring
│   │   └── production_monitoring.py    # Production monitoring
│   │
│   └── config/            # Configuration
│       ├── configuration_manager.py    # Configuration management
│       ├── newsgroup_config.py        # Newsgroup configuration
│       └── setup_config.py            # Setup configuration
│
├── tests/                 # Test suite
│   ├── e2e/              # End-to-end tests
│   │   └── test_production_e2e.py  # Production E2E tests
│   ├── integration/      # Integration tests (to be added)
│   ├── fixtures/         # Test fixtures
│   └── logs/            # Test logs
│
├── gui/                   # GUI components (existing)
│   ├── components/       # GUI components
│   ├── dialogs/         # Dialog windows
│   ├── widgets/         # Custom widgets
│   └── resources/       # GUI resources
│
├── tools/                 # Utility tools
│   ├── launchers/        # Application launchers
│   └── scripts/          # Utility scripts
│
├── obsolete/             # Old/deprecated files
│   ├── old_gui/         # Old GUI implementations
│   ├── old_workflows/   # Old GitHub workflows
│   ├── old_scripts/     # Old scripts
│   └── old_tests/       # Old test files
│
├── docs/                 # Documentation
├── templates/            # Templates
│
├── run_tests.py          # Main test runner
├── usenet_sync_config.json  # Main configuration
├── requirements.txt      # Python dependencies
├── README.md            # Project README
└── LICENSE              # License file
```

## Running Tests

### Full Test Suite
```bash
python run_tests.py
```

### Specific Tests
```bash
# Run only connection test
python run_tests.py --test test_01_connection_health

# Run multiple specific tests
python run_tests.py --test test_01_connection_health test_02_small_folder_public

# Skip cleanup after tests
python run_tests.py --skip-cleanup

# Verbose output
python run_tests.py --verbose
```

## Import Changes

Due to the reorganization, imports need to be updated:

### Old Import Style
```python
from enhanced_database_manager import EnhancedDatabaseManager
from production_nntp_client import ProductionNNTPClient
```

### New Import Style
```python
from src.database.enhanced_database_manager import EnhancedDatabaseManager
from src.networking.production_nntp_client import ProductionNNTPClient
```

## Configuration

The main configuration file `usenet_sync_config.json` remains in the root directory.

**IMPORTANT**: Remove hardcoded credentials and use environment variables:

```bash
export NNTP_USERNAME="your_username"
export NNTP_PASSWORD="your_password"
```

## Next Steps

1. **Fix Import Paths**: Update all Python files to use the new import structure
2. **Remove Credentials**: Remove hardcoded credentials from config files
3. **Run Tests**: Execute the E2E test suite to verify everything works
4. **Build New GUI**: Create a fresh GUI implementation from scratch

## Test Coverage

The E2E test suite covers:

1. **Connection Health** - Verify NNTP server connectivity
2. **Small Folder Public Share** - Test basic upload/download
3. **Medium Folder Private Share** - Test user-based access control
4. **Protected Share with Password** - Test password protection
5. **Incremental Updates** - Test version control and updates
6. **Large File Handling** - Test segmentation of large files
7. **Concurrent Operations** - Test parallel uploads/downloads
8. **Error Recovery** - Test retry mechanisms
9. **Performance Metrics** - Measure system performance
10. **Cleanup Verification** - Verify resource management

## Development Workflow

1. Make changes in the appropriate `src/` subdirectory
2. Run relevant tests with `python run_tests.py --test <test_name>`
3. Run full test suite before committing
4. Document any new features or changes

## Security Notes

- **Never commit credentials** to version control
- Use environment variables for sensitive data
- Rotate any exposed credentials immediately
- Enable encryption for all shares in production