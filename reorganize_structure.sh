#!/bin/bash

# Create new organized directory structure
mkdir -p src/core
mkdir -p src/networking
mkdir -p src/database
mkdir -p src/security
mkdir -p src/upload
mkdir -p src/download
mkdir -p src/indexing
mkdir -p src/monitoring
mkdir -p src/config
mkdir -p src/utils

# Create test directory structure
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p tests/fixtures
mkdir -p tests/logs

# Create tools directory for utilities
mkdir -p tools/scripts
mkdir -p tools/launchers

# Move core components to src/core
mv main.py src/core/ 2>/dev/null
mv usenet_sync_integrated.py src/core/ 2>/dev/null

# Move networking components
mv production_nntp_client.py src/networking/ 2>/dev/null
mv connection_pool.py src/networking/ 2>/dev/null

# Move database components
mv production_db_wrapper.py src/database/ 2>/dev/null
mv enhanced_database_manager.py src/database/ 2>/dev/null
mv init_database.py src/database/ 2>/dev/null
mv ensure_database_schema.py src/database/ 2>/dev/null
mv ensure_db_schema.py src/database/ 2>/dev/null

# Move security components
mv enhanced_security_system.py src/security/ 2>/dev/null
mv security_audit_system.py src/security/ 2>/dev/null
mv user_management.py src/security/ 2>/dev/null
mv encrypted_index_cache.py src/security/ 2>/dev/null

# Move upload components
mv enhanced_upload_system.py src/upload/ 2>/dev/null
mv upload_queue_manager.py src/upload/ 2>/dev/null
mv segment_packing_system.py src/upload/ 2>/dev/null
mv publishing_system.py src/upload/ 2>/dev/null

# Move download components
mv enhanced_download_system.py src/download/ 2>/dev/null
mv segment_retrieval_system.py src/download/ 2>/dev/null

# Move indexing components
mv versioned_core_index_system.py src/indexing/ 2>/dev/null
mv simplified_binary_index.py src/indexing/ 2>/dev/null
mv share_id_generator.py src/indexing/ 2>/dev/null

# Move monitoring components
mv monitoring_system.py src/monitoring/ 2>/dev/null
mv monitoring_dashboard.py src/monitoring/ 2>/dev/null
mv monitoring_cli.py src/monitoring/ 2>/dev/null
mv production_monitoring.py src/monitoring/ 2>/dev/null
mv usenet_sync_monitor.py src/monitoring/ 2>/dev/null

# Move configuration components
mv configuration_manager.py src/config/ 2>/dev/null
mv newsgroup_config.py src/config/ 2>/dev/null
mv setup_config.py src/config/ 2>/dev/null

# Move utility scripts to tools
mv windows_launcher.bat tools/launchers/ 2>/dev/null
mv production_launcher.py tools/launchers/ 2>/dev/null
mv setup_production_gui.py tools/launchers/ 2>/dev/null
mv start_workflow.bat tools/scripts/ 2>/dev/null
mv stop_workflow.bat tools/scripts/ 2>/dev/null
mv set_nntp_env.bat tools/scripts/ 2>/dev/null

# Keep configuration files in root
# usenet_sync_config.json stays in root
# usenetsync.json stays in root
# requirements*.txt stay in root
# README.md stays in root
# LICENSE stays in root
# setup.py stays in root

echo "Directory structure reorganized"
