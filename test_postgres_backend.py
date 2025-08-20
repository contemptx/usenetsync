#!/usr/bin/env python3
"""Test PostgreSQL backend integration"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_postgres_backend():
    """Test the backend with PostgreSQL"""
    
    print("=" * 80)
    print("TESTING POSTGRESQL BACKEND INTEGRATION")
    print("=" * 80)
    
    # Test 1: Direct PostgreSQL connection
    print("\n1. Testing direct PostgreSQL connection...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='usenetsync',
            user='usenetsync',
            password='usenetsync123'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ Connected to PostgreSQL: {version[:50]}...")
        conn.close()
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return False
    
    # Test 2: Import unified modules
    print("\n2. Testing module imports...")
    try:
        from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
        from unified.core.schema import UnifiedSchema
        from unified.main import UnifiedSystem
        print("   ✅ All modules imported successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 3: Initialize database with PostgreSQL
    print("\n3. Initializing PostgreSQL database...")
    try:
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            pg_host='localhost',
            pg_port=5432,
            pg_database='usenetsync',
            pg_user='usenetsync',
            pg_password='usenetsync123'
        )
        db = UnifiedDatabase(config)
        print("   ✅ Database initialized")
    except Exception as e:
        print(f"   ❌ Database initialization failed: {e}")
        return False
    
    # Test 4: Create schema
    print("\n4. Creating database schema...")
    try:
        schema = UnifiedSchema(db)
        schema.create_all_tables()
        print("   ✅ Schema created successfully")
    except Exception as e:
        print(f"   ❌ Schema creation failed: {e}")
        return False
    
    # Test 5: Initialize UnifiedSystem
    print("\n5. Initializing UnifiedSystem...")
    try:
        system = UnifiedSystem(db_type='postgresql')
        print("   ✅ UnifiedSystem initialized")
    except Exception as e:
        print(f"   ❌ UnifiedSystem initialization failed: {e}")
        # Try with environment variable
        print("   Retrying with environment variable...")
        os.environ['DATABASE_TYPE'] = 'postgresql'
        os.environ['DATABASE_HOST'] = 'localhost'
        os.environ['DATABASE_PORT'] = '5432'
        os.environ['DATABASE_NAME'] = 'usenetsync'
        os.environ['DATABASE_USER'] = 'usenetsync'
        os.environ['DATABASE_PASSWORD'] = 'usenetsync123'
        try:
            system = UnifiedSystem()
            print("   ✅ UnifiedSystem initialized with env vars")
        except Exception as e2:
            print(f"   ❌ Still failed: {e2}")
            return False
    
    # Test 6: Create a test user
    print("\n6. Creating test user...")
    try:
        user = system.create_user("testuser", "test@example.com")
        print(f"   ✅ User created: {user['user_id'][:16]}...")
    except Exception as e:
        print(f"   ❌ User creation failed: {e}")
        return False
    
    # Test 7: Get system statistics
    print("\n7. Getting system statistics...")
    try:
        stats = system.get_statistics()
        print(f"   ✅ Statistics retrieved:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"      {key}: {len(value)} items")
            else:
                print(f"      {key}: {value}")
    except Exception as e:
        print(f"   ❌ Failed to get statistics: {e}")
    
    print("\n" + "=" * 80)
    print("POSTGRESQL BACKEND TEST COMPLETE")
    print("=" * 80)
    return True

if __name__ == "__main__":
    # Activate virtual environment
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print("Restarting with virtual environment...")
        os.execv(venv_python, [venv_python] + sys.argv)
    
    success = test_postgres_backend()
    sys.exit(0 if success else 1)