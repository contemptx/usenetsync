#!/usr/bin/env python3
"""
Basic test to verify the system can be imported and initialized
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test config import
        from src.config.secure_config import SecureConfigLoader
        print("✓ Config module imported")
        
        # Test database imports
        from src.database.enhanced_database_manager import EnhancedDatabaseManager
        from src.database.production_db_wrapper import ProductionDatabaseManager
        print("✓ Database modules imported")
        
        # Test security imports
        from src.security.enhanced_security_system import EnhancedSecuritySystem
        from src.security.user_management import UserManager
        print("✓ Security modules imported")
        
        # Test networking imports
        from src.networking.production_nntp_client import ProductionNNTPClient
        from src.networking.connection_pool import ConnectionManager
        print("✓ Networking modules imported")
        
        # Test upload imports
        from src.upload.enhanced_upload_system import EnhancedUploadSystem
        from src.upload.segment_packing_system import SegmentPackingSystem
        from src.upload.publishing_system import PublishingSystem
        print("✓ Upload modules imported")
        
        # Test download imports
        from src.download.enhanced_download_system import EnhancedDownloadSystem
        from src.download.segment_retrieval_system import SegmentRetrievalSystem
        print("✓ Download modules imported")
        
        # Test indexing imports
        from src.indexing.versioned_core_index_system import VersionedCoreIndexSystem
        from src.indexing.share_id_generator import ShareIDGenerator
        print("✓ Indexing modules imported")
        
        # Test monitoring imports
        from src.monitoring.monitoring_system import MonitoringSystem
        print("✓ Monitoring modules imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")
    
    try:
        from src.config.secure_config import SecureConfigLoader
        
        # Check if credentials are set
        if not os.environ.get('NNTP_USERNAME'):
            print("⚠️  NNTP_USERNAME not set in environment")
            print("   You can set it with: export NNTP_USERNAME='your_username'")
            return False
        
        if not os.environ.get('NNTP_PASSWORD'):
            print("⚠️  NNTP_PASSWORD not set in environment")
            print("   You can set it with: export NNTP_PASSWORD='your_password'")
            return False
        
        # Try to load config
        loader = SecureConfigLoader()
        config = loader.config
        
        print(f"✓ Configuration loaded")
        print(f"  Server: {config['servers'][0]['hostname']}")
        print(f"  Port: {config['servers'][0]['port']}")
        print(f"  SSL: {config['servers'][0]['use_ssl']}")
        print(f"  Username: {config['servers'][0]['username'][:3]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_database_init():
    """Test database initialization"""
    print("\nTesting database initialization...")
    
    try:
        from src.database.enhanced_database_manager import DatabaseConfig
        from src.database.production_db_wrapper import ProductionDatabaseManager
        
        # Create test database
        db_config = DatabaseConfig(path="data/test.db")
        db = ProductionDatabaseManager(
            config=db_config,
            enable_monitoring=False,
            enable_retry=True
        )
        
        # Test basic operation
        db.initialize_schema()
        
        print("✓ Database initialized successfully")
        
        # Clean up
        Path("data/test.db").unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_main_module():
    """Test main module initialization"""
    print("\nTesting main module...")
    
    try:
        # Check if credentials are available
        if not os.environ.get('NNTP_USERNAME') or not os.environ.get('NNTP_PASSWORD'):
            print("⚠️  Skipping main module test (credentials not set)")
            return True  # Not a failure, just skipped
        
        from src.core.main import UsenetSync
        
        # Try to create instance (will fail if no valid config)
        # We won't actually initialize to avoid connecting to NNTP
        print("✓ Main module can be imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Main module error: {e}")
        return False

def main():
    """Run all basic tests"""
    print("=" * 60)
    print("BASIC SYSTEM TESTS")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test config
    results.append(("Configuration", test_config_loading()))
    
    # Test database
    results.append(("Database", test_database_init()))
    
    # Test main module
    results.append(("Main Module", test_main_module()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All basic tests passed!")
        print("\nYou can now run the full E2E tests with:")
        print("  python3 run_tests.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nMake sure to set environment variables:")
        print("  export NNTP_USERNAME='your_username'")
        print("  export NNTP_PASSWORD='your_password'")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)