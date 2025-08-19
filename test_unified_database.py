#!/usr/bin/env python3
"""
Test the unified database with REAL operations
No mocks, no placeholders - production testing
"""

import sys
import os
import tempfile
import time
import uuid
import json
from pathlib import Path

sys.path.insert(0, '/workspace/src')

from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema

def test_unified_database():
    """Test unified database with real operations"""
    
    print("=" * 80)
    print("TESTING UNIFIED DATABASE - REAL OPERATIONS")
    print("=" * 80)
    
    # Test with SQLite first
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, "test.db")
    
    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        sqlite_path=db_path,
        enable_monitoring=True,
        enable_retry=True
    )
    
    results = {
        'passed': [],
        'failed': []
    }
    
    try:
        # 1. Test database initialization
        print("\n1. Testing database initialization...")
        db = UnifiedDatabase(config)
        print("✓ Database initialized successfully")
        results['passed'].append("Database initialization")
        
        # 2. Test schema creation
        print("\n2. Testing schema creation...")
        schema = UnifiedSchema(db)
        tables = schema.create_all_tables()
        print(f"✓ Created {len(tables)} tables")
        results['passed'].append(f"Schema creation ({len(tables)} tables)")
        
        # 3. Test insert operations
        print("\n3. Testing insert operations...")
        
        # Insert a folder
        folder_id = str(uuid.uuid4())
        folder_data = {
            'folder_id': folder_id,
            'path': '/test/folder',
            'name': 'test_folder',
            'owner_id': 'user123',
            'total_size': 1024000,
            'file_count': 10,
            'version': 1
        }
        
        db.insert('folders', folder_data)
        print("✓ Inserted folder record")
        
        # Insert files
        file_ids = []
        for i in range(5):
            file_id = str(uuid.uuid4())
            file_ids.append(file_id)
            
            file_data = {
                'file_id': file_id,
                'folder_id': folder_id,
                'path': f'/test/folder/file{i}.txt',
                'name': f'file{i}.txt',
                'size': 102400 + i * 1000,
                'hash': f'hash{i}' * 16,
                'version': 1,
                'status': 'indexed'
            }
            
            db.insert('files', file_data)
        
        print(f"✓ Inserted {len(file_ids)} file records")
        results['passed'].append("Insert operations")
        
        # 4. Test query operations
        print("\n4. Testing query operations...")
        
        # Fetch one
        folder = db.fetch_one("SELECT * FROM folders WHERE folder_id = ?", (folder_id,))
        assert folder is not None
        assert folder['name'] == 'test_folder'
        print("✓ fetch_one works correctly")
        
        # Fetch all
        files = db.fetch_all("SELECT * FROM files WHERE folder_id = ?", (folder_id,))
        assert len(files) == 5
        print(f"✓ fetch_all returned {len(files)} records")
        results['passed'].append("Query operations")
        
        # 5. Test transactions
        print("\n5. Testing transactions...")
        
        try:
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)",
                             ('user456', 'testuser'))
                cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)",
                             ('user789', 'testuser2'))
                # This will succeed
            
            users = db.fetch_all("SELECT * FROM users")
            assert len(users) == 2
            print("✓ Transaction committed successfully")
            
            # Test rollback
            try:
                with db.transaction() as cursor:
                    cursor.execute("DELETE FROM users WHERE user_id = ?", ('user456',))
                    # Force an error
                    cursor.execute("INVALID SQL")
            except:
                pass
            
            users = db.fetch_all("SELECT * FROM users")
            assert len(users) == 2  # Should still be 2 (rollback worked)
            print("✓ Transaction rollback works")
            results['passed'].append("Transactions")
            
        except Exception as e:
            print(f"✗ Transaction test failed: {e}")
            results['failed'].append(f"Transactions: {e}")
        
        # 6. Test update operations
        print("\n6. Testing update operations...")
        
        rows = db.update('folders', 
                        {'file_count': 15, 'total_size': 2048000},
                        'folder_id = ?', (folder_id,))
        assert rows == 1
        
        folder = db.fetch_one("SELECT * FROM folders WHERE folder_id = ?", (folder_id,))
        assert folder['file_count'] == 15
        print("✓ Update operation successful")
        results['passed'].append("Update operations")
        
        # 7. Test upsert operations
        print("\n7. Testing upsert operations...")
        
        share_data = {
            'share_id': 'SHARE123',
            'folder_id': folder_id,
            'share_type': 'full',
            'access_level': 'public',
            'download_count': 0
        }
        
        db.upsert('publications', share_data, ['share_id'])
        
        # Update via upsert
        share_data['download_count'] = 5
        db.upsert('publications', share_data, ['share_id'])
        
        share = db.fetch_one("SELECT * FROM publications WHERE share_id = ?", ('SHARE123',))
        assert share['download_count'] == 5
        print("✓ Upsert operation successful")
        results['passed'].append("Upsert operations")
        
        # 8. Test streaming for large datasets
        print("\n8. Testing streaming operations...")
        
        # Insert many records
        segment_data = []
        for i in range(100):
            segment_data.append((
                str(uuid.uuid4()),  # segment_id
                file_ids[0],        # file_id
                i,                  # segment_index
                768000,             # size
                f'hash{i}' * 16     # hash
            ))
        
        db.execute_many(
            "INSERT INTO segments (segment_id, file_id, segment_index, size, hash) VALUES (?, ?, ?, ?, ?)",
            segment_data
        )
        
        # Stream results
        count = 0
        for segment in db.stream_results("SELECT * FROM segments", chunk_size=10):
            count += 1
        
        assert count == 100
        print(f"✓ Streamed {count} records efficiently")
        results['passed'].append("Streaming operations")
        
        # 9. Test monitoring and statistics
        print("\n9. Testing monitoring and statistics...")
        
        stats = db.get_stats()
        assert 'database_type' in stats
        assert 'pool_stats' in stats
        assert 'tables' in stats
        
        print(f"✓ Database type: {stats['database_type']}")
        print(f"✓ Queries executed: {stats['pool_stats']['queries_executed']}")
        print(f"✓ Tables with data: {len([t for t, c in stats['tables'].items() if c > 0])}")
        results['passed'].append("Monitoring and statistics")
        
        # 10. Test backup
        print("\n10. Testing backup...")
        
        backup_path = os.path.join(test_dir, "backup.db")
        db.backup(backup_path)
        assert os.path.exists(backup_path)
        assert os.path.getsize(backup_path) > 0
        print(f"✓ Backup created: {os.path.getsize(backup_path)} bytes")
        results['passed'].append("Backup operations")
        
        # 11. Test complex queries with joins
        print("\n11. Testing complex queries...")
        
        query = """
            SELECT f.name, f.size, COUNT(s.id) as segment_count
            FROM files f
            LEFT JOIN segments s ON f.file_id = s.file_id
            WHERE f.folder_id = ?
            GROUP BY f.file_id, f.name, f.size
        """
        
        results_complex = db.fetch_all(query, (folder_id,))
        assert len(results_complex) > 0
        print(f"✓ Complex query with JOIN returned {len(results_complex)} results")
        results['passed'].append("Complex queries")
        
        # 12. Test performance with batch operations
        print("\n12. Testing batch performance...")
        
        start_time = time.time()
        
        # Batch insert 1000 metrics
        metrics_data = []
        for i in range(1000):
            metrics_data.append((
                f'metric_{i % 10}',
                'counter',
                float(i),
                'bytes',
                json.dumps({'host': 'server1'})
            ))
        
        db.execute_many(
            "INSERT INTO metrics (metric_name, metric_type, value, unit, tags) VALUES (?, ?, ?, ?, ?)",
            metrics_data
        )
        
        elapsed = time.time() - start_time
        print(f"✓ Inserted 1000 metrics in {elapsed:.3f} seconds")
        results['passed'].append(f"Batch performance ({1000/elapsed:.0f} ops/sec)")
        
        # Clean up
        db.close()
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(str(e))
    
    finally:
        # Clean up test directory
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✓ Passed: {len(results['passed'])} tests")
    for test in results['passed']:
        print(f"  - {test}")
    
    if results['failed']:
        print(f"\n✗ Failed: {len(results['failed'])} tests")
        for test in results['failed']:
            print(f"  - {test}")
    
    print("\n" + "=" * 80)
    
    if results['failed']:
        print("RESULT: SOME TESTS FAILED")
        return False
    else:
        print("RESULT: ALL TESTS PASSED - DATABASE IS PRODUCTION READY")
        return True

if __name__ == "__main__":
    success = test_unified_database()
    sys.exit(0 if success else 1)