#!/usr/bin/env python3
"""
Test complete integration of all fixes
"""
import sys
import os
sys.path.insert(0, 'src')
os.environ['DATABASE_URL'] = 'postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync'

def test_system_initialization():
    """Test that UnifiedSystem initializes properly"""
    print("Testing system initialization...")
    
    from unified.main import UnifiedSystem
    system = UnifiedSystem()
    
    # Check that all critical components are initialized
    assert system.db is not None, "Database not initialized"
    assert system.schema is not None, "Schema not initialized"
    assert system.upload_queue is not None, "Upload queue not initialized"
    assert hasattr(system, 'get_statistics'), "Missing get_statistics method"
    
    # Check that there's only one get_statistics method
    import inspect
    methods = [m for m in inspect.getmembers(system) if m[0] == 'get_statistics']
    assert len(methods) == 1, f"Multiple get_statistics methods found: {len(methods)}"
    
    print("✅ System initialization successful")
    return system

def test_database_schema():
    """Test that database schema is correct"""
    print("\nTesting database schema...")
    
    from unified.main import UnifiedSystem
    system = UnifiedSystem()
    
    # Check that shares table exists (not publications)
    tables = system.db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t['name'] for t in tables] if tables else []
    
    assert 'shares' in table_names or system.db.fetch_one("SELECT 1 FROM shares LIMIT 0") is not None, "Shares table not found"
    print("✅ Database schema correct")

def test_api_endpoints():
    """Test that API endpoints are available"""
    print("\nTesting API endpoints...")
    
    from unified.api.server import UnifiedAPIServer
    server = UnifiedAPIServer()
    
    # Check that new endpoints exist
    routes = [route.path for route in server.app.routes]
    
    assert '/api/v1/logs' in routes, "Logs endpoint missing"
    assert '/api/v1/search' in routes, "Search endpoint missing"
    assert '/api/v1/network/connection_pool' in routes, "Connection pool endpoint missing"
    
    print("✅ API endpoints available")

def test_migrations():
    """Test that migrations system works"""
    print("\nTesting migrations system...")
    
    from unified.core.migrations import UnifiedMigrations
    from unified.main import UnifiedSystem
    
    system = UnifiedSystem()
    migrations = UnifiedMigrations(system.db)
    
    # Check current version
    version = migrations.get_current_version()
    print(f"  Current schema version: {version}")
    
    # Run migrations
    applied = migrations.migrate()
    print(f"  Applied {applied} migrations")
    
    print("✅ Migrations system working")

def test_legacy_isolation():
    """Test that legacy code is isolated"""
    print("\nTesting legacy code isolation...")
    
    import os
    
    # Check that legacy directory exists
    assert os.path.exists('src/legacy'), "Legacy directory not found"
    
    # Check that old modules are moved
    assert not os.path.exists('src/folder_management'), "folder_management should be in legacy"
    assert not os.path.exists('src/download'), "download should be in legacy"
    assert not os.path.exists('src/upload'), "upload should be in legacy"
    assert not os.path.exists('src/unified/database_schema.py'), "database_schema.py should be in legacy"
    
    print("✅ Legacy code properly isolated")

def test_gui_bridge():
    """Test that GUI bridge uses high-level methods"""
    print("\nTesting GUI bridge...")
    
    from unified.gui_bridge.complete_tauri_bridge import CompleteTauriBridge
    from unified.main import UnifiedSystem
    
    system = UnifiedSystem()
    bridge = CompleteTauriBridge(system)
    
    # Check that bridge has system reference
    assert bridge.system is not None, "Bridge not connected to system"
    
    # Check that index_folder method exists
    assert hasattr(bridge, '_index_folder'), "Missing _index_folder method"
    
    print("✅ GUI bridge configured correctly")

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPLETE INTEGRATION TEST")
    print("=" * 60)
    
    try:
        system = test_system_initialization()
        test_database_schema()
        test_api_endpoints()
        test_migrations()
        test_legacy_isolation()
        test_gui_bridge()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - INTEGRATION COMPLETE!")
        print("=" * 60)
        
        # Get final statistics
        stats = system.get_statistics()
        print("\nSystem Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
