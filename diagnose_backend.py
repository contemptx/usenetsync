#!/usr/bin/env python3
"""
Diagnose Backend Issues for UsenetSync
Tests each backend component to identify initialization problems
"""

import sys
import os
import traceback
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_import(module_name, description=""):
    """Test importing a module"""
    try:
        module = __import__(module_name)
        print(f"✓ {module_name} - {description}")
        return True, module
    except ImportError as e:
        print(f"✗ {module_name} - Import Error: {e}")
        return False, None
    except Exception as e:
        print(f"⚠ {module_name} - Other Error: {e}")
        return False, None

def test_backend_components():
    """Test all backend components"""
    print("=" * 60)
    print("Testing Backend Component Imports")
    print("=" * 60)
    
    components = [
        ('enhanced_database_manager', 'Database management'),
        ('production_db_wrapper', 'Database wrapper'),
        ('enhanced_security_system', 'Security system'),
        ('production_nntp_client', 'NNTP client'),
        ('segment_packing_system', 'Segment packing'),
        ('enhanced_upload_system', 'Upload system'),
        ('versioned_core_index_system', 'Index system'),
        ('simplified_binary_index', 'Binary index'),
        ('enhanced_download_system', 'Download system'),
        ('publishing_system', 'Publishing system'),
        ('user_management', 'User management'),
        ('configuration_manager', 'Configuration'),
        ('monitoring_system', 'Monitoring system'),
        ('segment_retrieval_system', 'Segment retrieval'),
        ('upload_queue_manager', 'Queue manager'),
    ]
    
    success_count = 0
    failed_components = []
    
    for module_name, description in components:
        success, module = test_import(module_name, description)
        if success:
            success_count += 1
        else:
            failed_components.append(module_name)
    
    print()
    print(f"Results: {success_count}/{len(components)} components imported successfully")
    
    return failed_components

def test_critical_dependencies():
    """Test critical Python dependencies"""
    print("=" * 60)
    print("Testing Critical Dependencies")
    print("=" * 60)
    
    dependencies = [
        ('tkinter', 'GUI framework'),
        ('sqlite3', 'Database support'),
        ('threading', 'Threading support'),
        ('json', 'JSON support'),
        ('pathlib', 'Path handling'),
        ('logging', 'Logging support'),
        ('nntp', 'NNTP client (pynntp)'),
        ('cryptography', 'Cryptography library'),
    ]
    
    all_available = True
    
    for dep, desc in dependencies:
        success, _ = test_import(dep, desc)
        if not success:
            all_available = False
    
    return all_available

def test_configuration():
    """Test configuration loading"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    config_file = Path('usenet_sync_config.json')
    
    if not config_file.exists():
        print("✗ Configuration file missing: usenet_sync_config.json")
        return False
    
    try:
        import json
        with open(config_file) as f:
            config = json.load(f)
        
        print("✓ Configuration file loads successfully")
        
        # Check required sections
        required_sections = ['servers', 'storage']
        for section in required_sections:
            if section in config:
                print(f"✓ Configuration has '{section}' section")
            else:
                print(f"✗ Configuration missing '{section}' section")
                return False
        
        # Check servers
        if config['servers']:
            server = config['servers'][0]
            required_server_fields = ['hostname', 'port', 'username', 'password']
            for field in required_server_fields:
                if field in server and server[field]:
                    print(f"✓ Server has '{field}' configured")
                else:
                    print(f"⚠ Server missing or empty '{field}' (this may cause issues)")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_database_creation():
    """Test database creation"""
    print("=" * 60)
    print("Testing Database Creation")
    print("=" * 60)
    
    try:
        from enhanced_database_manager import DatabaseConfig, EnhancedDatabaseManager
        
        # Test with temporary database
        db_path = "test_database.db"
        config = DatabaseConfig(path=db_path)
        
        db = EnhancedDatabaseManager(config)
        print("✓ Database manager created successfully")
        
        # Cleanup
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        traceback.print_exc()
        return False

def test_main_class():
    """Test the main UsenetSync class"""
    print("=" * 60)
    print("Testing Main UsenetSync Class")
    print("=" * 60)
    
    try:
        from main import UsenetSync
        print("✓ UsenetSync class imports successfully")
        
        # Try to create instance (this is where it likely fails)
        print("Attempting to create UsenetSync instance...")
        app = UsenetSync()
        print("✓ UsenetSync instance created successfully")
        
        # Cleanup
        app.cleanup()
        return True, app
        
    except Exception as e:
        print(f"✗ UsenetSync creation failed: {e}")
        print("\nDetailed error trace:")
        traceback.print_exc()
        return False, None

def create_minimal_backend():
    """Create a minimal backend for testing"""
    print("=" * 60)
    print("Creating Minimal Backend")
    print("=" * 60)
    
    minimal_backend_code = '''
class MinimalBackend:
    """Minimal backend for testing GUI without full initialization"""
    
    def __init__(self):
        self.user = MinimalUser()
        self.db = MinimalDB()
        
    def initialize_user(self, display_name=None):
        """Mock user initialization"""
        import hashlib
        import time
        user_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
        return user_id
        
    def cleanup(self):
        """Mock cleanup"""
        pass

class MinimalUser:
    """Minimal user management"""
    
    def __init__(self):
        self._initialized = False
        self._user_id = None
        self._display_name = None
    
    def is_initialized(self):
        return self._initialized
        
    def get_user_id(self):
        return self._user_id or "mock_user_id_12345"
        
    def get_display_name(self):
        return self._display_name or "Test User"
        
    def initialize(self, display_name=None):
        self._initialized = True
        self._display_name = display_name
        import hashlib
        import time
        self._user_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
        return self._user_id
        
    def get_download_path(self):
        return "./downloads"

class MinimalDB:
    """Minimal database mock"""
    
    def get_indexed_folders(self):
        return []
'''
    
    try:
        with open('minimal_backend.py', 'w') as f:
            f.write(minimal_backend_code)
        print("✓ Created minimal_backend.py")
        return True
    except Exception as e:
        print(f"✗ Failed to create minimal backend: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("UsenetSync Backend Diagnostics")
    print("=" * 60)
    print()
    
    # Test 1: Dependencies
    deps_ok = test_critical_dependencies()
    print()
    
    # Test 2: Configuration
    config_ok = test_configuration()
    print()
    
    # Test 3: Backend components
    failed_components = test_backend_components()
    print()
    
    # Test 4: Database
    db_ok = test_database_creation()
    print()
    
    # Test 5: Main class
    main_ok, app = test_main_class()
    print()
    
    # Summary and recommendations
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if deps_ok and config_ok and not failed_components and db_ok and main_ok:
        print("🎉 All tests passed! Backend should work correctly.")
        return 0
    else:
        print("❌ Issues found:")
        
        if not deps_ok:
            print("  - Missing critical dependencies")
            print("    → Run: python install_dependencies.py")
        
        if not config_ok:
            print("  - Configuration issues")
            print("    → Check usenet_sync_config.json")
        
        if failed_components:
            print(f"  - Failed to import {len(failed_components)} backend components:")
            for comp in failed_components[:5]:  # Show first 5
                print(f"    → {comp}")
            if len(failed_components) > 5:
                print(f"    → ... and {len(failed_components) - 5} more")
        
        if not db_ok:
            print("  - Database creation issues")
        
        if not main_ok:
            print("  - Main class initialization failed")
        
        print()
        print("RECOMMENDED ACTIONS:")
        print("1. Install missing dependencies: python install_dependencies.py")
        print("2. Check that all backend files are present")
        print("3. Verify NNTP configuration in usenet_sync_config.json")
        
        # Offer to create minimal backend
        print()
        create_minimal = input("Create minimal backend for GUI testing? (y/n) [y]: ").strip().lower()
        if create_minimal in ('', 'y', 'yes'):
            if create_minimal_backend():
                print()
                print("✓ Created minimal backend.")
                print("You can now test the GUI with limited functionality:")
                print("  → Modify usenetsync_gui_main.py line 22 to:")
                print("     from minimal_backend import MinimalBackend as UsenetSync")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
