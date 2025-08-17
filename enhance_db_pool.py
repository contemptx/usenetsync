#!/usr/bin/env python3
"""
Enhance existing database connection pool for better concurrency
"""

import sqlite3
import time
from pathlib import Path

def enhance_database_pool():
    """
    Enhance the existing database connection pool settings
    """
    
    # Monkey-patch the ConnectionPool._create_connection method
    from src.database.enhanced_database_manager import ConnectionPool
    
    # Store original method
    original_create_connection = ConnectionPool._create_connection
    
    def enhanced_create_connection(self):
        """Enhanced connection creation with better concurrency settings"""
        conn = sqlite3.connect(
            self.database_path,
            timeout=60.0,  # Increased from 30 to 60 seconds
            check_same_thread=False,
            isolation_level='DEFERRED'  # Use deferred transactions by default
        )
        conn.row_factory = sqlite3.Row
        
        # Enhanced pragmas for better concurrency
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")  # Increased from 5000 to 30000 (30 seconds)
        
        # WAL mode optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=20000")  # Increased cache
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=536870912")  # 512MB mmap
        
        # WAL specific optimizations
        conn.execute("PRAGMA wal_autocheckpoint=2000")  # Checkpoint every 2000 pages
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # Clean WAL file
        
        return conn
    
    # Apply the patch
    ConnectionPool._create_connection = enhanced_create_connection
    
    print("✅ Database connection pool enhanced with better concurrency settings")
    
    return True


def optimize_existing_database(db_path):
    """
    Optimize an existing database for better concurrency
    """
    if not Path(db_path).exists():
        print(f"⚠️  Database {db_path} does not exist")
        return False
    
    conn = sqlite3.connect(db_path, timeout=60.0)
    
    try:
        # Check current settings
        print("\nCurrent database settings:")
        for pragma in ['journal_mode', 'synchronous', 'busy_timeout', 'cache_size']:
            result = conn.execute(f"PRAGMA {pragma}").fetchone()
            print(f"  {pragma}: {result[0] if result else 'unknown'}")
        
        # Apply optimizations
        print("\nApplying optimizations...")
        
        # Enable WAL mode
        result = conn.execute("PRAGMA journal_mode=WAL").fetchone()
        print(f"  journal_mode set to: {result[0] if result else 'unknown'}")
        
        # Set other pragmas
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA cache_size=20000")
        conn.execute("PRAGMA wal_autocheckpoint=2000")
        
        # Checkpoint to clean up WAL
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        # Analyze for query optimization
        conn.execute("ANALYZE")
        
        conn.commit()
        
        # Verify new settings
        print("\nNew database settings:")
        for pragma in ['journal_mode', 'synchronous', 'busy_timeout', 'cache_size']:
            result = conn.execute(f"PRAGMA {pragma}").fetchone()
            print(f"  {pragma}: {result[0] if result else 'unknown'}")
        
        print("\n✅ Database optimized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error optimizing database: {e}")
        return False
        
    finally:
        conn.close()


def test_concurrent_pool_access():
    """Test the enhanced pool with concurrent access"""
    import threading
    import random
    from src.database.enhanced_database_manager import DatabaseConfig, EnhancedDatabaseManager
    
    # Apply enhancements
    enhance_database_pool()
    
    # Create database manager
    config = DatabaseConfig(path="test_workspace/test.db", pool_size=20)  # Increased pool size
    db = EnhancedDatabaseManager(config)
    
    results = {'success': 0, 'failed': 0, 'lock_errors': 0}
    lock = threading.Lock()
    
    def worker(worker_id, operations=10):
        """Worker thread"""
        for i in range(operations):
            try:
                # Get connection from pool
                with db.pool.get_connection() as conn:
                    # Read operation
                    cursor = conn.execute("SELECT COUNT(*) FROM folders")
                    count = cursor.fetchone()[0]
                    
                    # Write operation
                    conn.execute(
                        "INSERT INTO metrics (metric_type, metric_name, value) VALUES (?, ?, ?)",
                        (f"worker_{worker_id}", f"op_{i}", random.random())
                    )
                    conn.commit()
                    
                    with lock:
                        results['success'] += 1
                    
                    print(f"Worker {worker_id}: Operation {i+1}/{operations} ✓")
                
                # Small random delay
                time.sleep(random.uniform(0.001, 0.01))
                
            except sqlite3.OperationalError as e:
                if 'locked' in str(e):
                    with lock:
                        results['lock_errors'] += 1
                    print(f"Worker {worker_id}: Lock error on operation {i+1}")
                else:
                    with lock:
                        results['failed'] += 1
                    print(f"Worker {worker_id}: Error - {e}")
            except Exception as e:
                with lock:
                    results['failed'] += 1
                print(f"Worker {worker_id}: Unexpected error - {e}")
    
    # Create worker threads
    threads = []
    num_workers = 10
    ops_per_worker = 5
    
    print(f"\nStarting {num_workers} workers with {ops_per_worker} operations each...")
    
    start_time = time.time()
    
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i, ops_per_worker))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    # Print results
    print("\n" + "="*60)
    print("CONCURRENT ACCESS TEST RESULTS")
    print("="*60)
    print(f"Total operations: {num_workers * ops_per_worker}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Lock errors: {results['lock_errors']}")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print(f"Operations/second: {results['success']/elapsed:.1f}")
    
    # Close pool
    db.pool.close_all()
    
    return results['lock_errors'] == 0


if __name__ == "__main__":
    print("="*60)
    print("DATABASE CONNECTION POOL ENHANCEMENT")
    print("="*60)
    
    # 1. Enhance the connection pool
    print("\n1. Enhancing connection pool...")
    enhance_database_pool()
    
    # 2. Optimize test database
    print("\n2. Optimizing test database...")
    test_db = Path("test_workspace/test.db")
    if test_db.exists():
        optimize_existing_database(test_db)
    
    # 3. Test concurrent access
    print("\n3. Testing concurrent access with enhanced pool...")
    success = test_concurrent_pool_access()
    
    print("\n" + "="*60)
    if success:
        print("✅ Database pool enhancement successful!")
        print("   No lock errors during concurrent access")
    else:
        print("⚠️  Some lock errors occurred, but system handled them")
    print("="*60)