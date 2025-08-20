#!/usr/bin/env python3
"""Test to identify refactoring issues in the unified system"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_refactoring_issues():
    """Comprehensive test to identify refactoring issues"""
    
    print("=" * 80)
    print("TESTING FOR REFACTORING ISSUES")
    print("=" * 80)
    
    issues = []
    
    # Test 1: Module imports
    print("\n1. Testing module imports...")
    modules_to_test = [
        'unified.main',
        'unified.core.database',
        'unified.core.schema',
        'unified.core.config',
        'unified.core.models',
        'unified.security.authentication',
        'unified.security.encryption',
        'unified.security.access_control',
        'unified.indexing.scanner',
        'unified.segmentation.processor',
        'unified.networking.real_nntp_client',
        'unified.api.server',
        'unified.gui_bridge.complete_tauri_bridge',
        'gui_backend_bridge'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {e}")
            issues.append(f"Import error in {module}: {e}")
    
    # Test 2: Database operations
    print("\n2. Testing database operations...")
    try:
        from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
        from unified.core.schema import UnifiedSchema
        
        # Use SQLite for testing
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, sqlite_path=":memory:")
        db = UnifiedDatabase(config)
        schema = UnifiedSchema(db)
        schema.create_all_tables()
        
        # Test basic operations
        test_data = {'test_field': 'test_value', 'user_id': 'test123'}
        
        # Check if we can insert into users table
        try:
            db.insert('users', {
                'user_id': 'test123',
                'username': 'testuser',
                'email': 'test@test.com',
                'public_key': 'testkey',
                'private_key_encrypted': 'encrypted',
                'api_key': 'apikey'
            })
            print("   ✅ User insertion works")
        except Exception as e:
            print(f"   ❌ User insertion failed: {e}")
            issues.append(f"Database user insertion: {e}")
        
        print("   ✅ Database operations")
    except Exception as e:
        print(f"   ❌ Database operations: {e}")
        issues.append(f"Database operations: {e}")
    
    # Test 3: UnifiedSystem initialization
    print("\n3. Testing UnifiedSystem initialization...")
    try:
        from unified.main import UnifiedSystem
        system = UnifiedSystem()
        print("   ✅ UnifiedSystem initialized")
    except Exception as e:
        print(f"   ❌ UnifiedSystem initialization: {e}")
        issues.append(f"UnifiedSystem initialization: {e}")
    
    # Test 4: File operations
    print("\n4. Testing file operations...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")
            
            # Test indexing
            try:
                result = system.index_folder(tmpdir, "test_user")
                print(f"   ✅ Folder indexing: {result.get('files_indexed', 0)} files")
            except Exception as e:
                print(f"   ❌ Folder indexing: {e}")
                issues.append(f"Folder indexing: {e}")
    except Exception as e:
        print(f"   ❌ File operations: {e}")
        issues.append(f"File operations: {e}")
    
    # Test 5: API endpoints
    print("\n5. Testing API server initialization...")
    try:
        from unified.api.server import create_app
        app = create_app()
        print("   ✅ API server created")
    except Exception as e:
        print(f"   ❌ API server: {e}")
        issues.append(f"API server: {e}")
    
    # Test 6: GUI bridge
    print("\n6. Testing GUI bridge...")
    try:
        from unified.gui_bridge.complete_tauri_bridge import TauriBridge
        bridge = TauriBridge()
        print("   ✅ GUI bridge initialized")
    except Exception as e:
        print(f"   ❌ GUI bridge: {e}")
        issues.append(f"GUI bridge: {e}")
    
    # Test 7: Check for common refactoring issues
    print("\n7. Checking for common refactoring issues...")
    
    # Check for mismatched field names
    try:
        from unified.core.models import File, Folder, Segment
        
        # Check if models have expected fields
        file_fields = [f for f in dir(File) if not f.startswith('_')]
        folder_fields = [f for f in dir(Folder) if not f.startswith('_')]
        segment_fields = [f for f in dir(Segment) if not f.startswith('_')]
        
        print(f"   File model fields: {len(file_fields)}")
        print(f"   Folder model fields: {len(folder_fields)}")
        print(f"   Segment model fields: {len(segment_fields)}")
        
        # Check for specific critical fields
        critical_file_fields = ['file_id', 'filename', 'size', 'hash']
        for field in critical_file_fields:
            if field not in file_fields:
                issues.append(f"Missing field in File model: {field}")
        
        print("   ✅ Model fields check")
    except Exception as e:
        print(f"   ❌ Model fields check: {e}")
        issues.append(f"Model fields check: {e}")
    
    # Test 8: Check configuration loading
    print("\n8. Testing configuration loading...")
    try:
        from unified.core.config import load_config, UnifiedConfig
        
        # Test with environment variables
        os.environ['USENETSYNC_DATABASE_TYPE'] = 'postgresql'
        config = load_config()
        
        if config.database_type != 'postgresql':
            issues.append(f"Config not loading from env: database_type is {config.database_type}")
            print(f"   ⚠️  Config database_type: {config.database_type} (expected postgresql)")
        else:
            print(f"   ✅ Config loading from environment")
        
        # Reset for other tests
        if 'USENETSYNC_DATABASE_TYPE' in os.environ:
            del os.environ['USENETSYNC_DATABASE_TYPE']
        
    except Exception as e:
        print(f"   ❌ Configuration loading: {e}")
        issues.append(f"Configuration loading: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("REFACTORING ISSUES SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"\n❌ Found {len(issues)} issues:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        return False
    else:
        print("\n✅ No refactoring issues found! System appears to be working correctly.")
        return True

if __name__ == "__main__":
    # Activate virtual environment
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print("Restarting with virtual environment...")
        os.execv(venv_python, [venv_python] + sys.argv)
    
    success = test_refactoring_issues()
    sys.exit(0 if success else 1)