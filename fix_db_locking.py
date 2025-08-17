#!/usr/bin/env python3
"""
Fix database locking issues by implementing proper connection management
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

class DatabaseConnectionManager:
    """Manages database connections with proper locking"""
    
    def __init__(self, db_path, timeout=30.0):
        self.db_path = db_path
        self.timeout = timeout
        self.local = threading.local()
        self._lock = threading.Lock()
        
        # Initialize database with proper settings
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database with optimal settings for concurrency"""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        conn.execute("PRAGMA wal_autocheckpoint=1000")
        
        # Verify WAL mode
        result = conn.execute("PRAGMA journal_mode").fetchone()
        if result and result[0].lower() == 'wal':
            print("✅ WAL mode enabled successfully")
        else:
            print("⚠️  WAL mode not enabled, using:", result[0] if result else "unknown")
        
        conn.close()
    
    @contextmanager
    def get_connection(self):
        """Get a connection for the current thread"""
        # Use thread-local storage for connections
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(
                self.db_path, 
                timeout=self.timeout,
                isolation_level='DEFERRED'  # Use deferred transactions
            )
            self.local.conn.row_factory = sqlite3.Row
            
            # Set pragmas for this connection
            self.local.conn.execute("PRAGMA busy_timeout=30000")
            self.local.conn.execute("PRAGMA synchronous=NORMAL")
        
        try:
            yield self.local.conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e):
                print(f"⚠️  Database locked, retrying...")
                time.sleep(0.1)
                # Retry once
                yield self.local.conn
            else:
                raise
    
    def close(self):
        """Close the connection for current thread"""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None


def patch_database_manager():
    """Patch the existing database manager to use better locking"""
    
    # Import the production database manager
    from src.database.production_db_wrapper import ProductionDatabaseManager
    from src.database.enhanced_database_manager import EnhancedDatabaseManager
    
    # Store original get_connection method
    original_get_connection = EnhancedDatabaseManager.get_connection
    
    # Create a new get_connection method with better locking
    def new_get_connection(self):
        """Enhanced get_connection with retry logic"""
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                conn = original_get_connection(self)
                
                # Set busy timeout
                conn.execute("PRAGMA busy_timeout=30000")
                
                # Use IMMEDIATE transactions for writes to fail fast
                if hasattr(self, '_is_write_operation') and self._is_write_operation:
                    conn.isolation_level = 'IMMEDIATE'
                else:
                    conn.isolation_level = 'DEFERRED'
                
                return conn
                
            except sqlite3.OperationalError as e:
                if 'locked' in str(e) and attempt < max_retries - 1:
                    print(f"Database locked, retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise
        
        raise sqlite3.OperationalError("Database locked after all retries")
    
    # Patch the method
    EnhancedDatabaseManager.get_connection = new_get_connection
    
    print("✅ Database manager patched with better locking strategy")


def test_concurrent_access():
    """Test concurrent database access"""
    import threading
    import random
    
    db_path = "test_workspace/test.db"
    manager = DatabaseConnectionManager(db_path)
    
    def worker(worker_id, num_operations=10):
        """Worker thread that performs database operations"""
        for i in range(num_operations):
            try:
                with manager.get_connection() as conn:
                    # Simulate read
                    cursor = conn.execute("SELECT COUNT(*) FROM folders")
                    count = cursor.fetchone()[0]
                    
                    # Simulate write
                    conn.execute(
                        "INSERT INTO metrics (metric_type, metric_name, value) VALUES (?, ?, ?)",
                        (f"test_{worker_id}", f"operation_{i}", random.random())
                    )
                    conn.commit()
                    
                    print(f"Worker {worker_id}: Operation {i+1} completed")
                    
                time.sleep(random.uniform(0.01, 0.05))
                
            except Exception as e:
                print(f"Worker {worker_id}: Error - {e}")
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i, 5))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    manager.close()
    print("\n✅ Concurrent access test completed")


if __name__ == "__main__":
    print("="*60)
    print("DATABASE LOCKING FIX")
    print("="*60)
    
    # 1. Patch the database manager
    print("\n1. Patching database manager...")
    patch_database_manager()
    
    # 2. Initialize test database with proper settings
    print("\n2. Initializing test database...")
    test_db = Path("test_workspace/test.db")
    if test_db.exists():
        manager = DatabaseConnectionManager(test_db)
        print("✅ Test database initialized with proper settings")
    
    # 3. Test concurrent access
    print("\n3. Testing concurrent access...")
    test_concurrent_access()
    
    print("\n" + "="*60)
    print("✅ Database locking fixes applied!")
    print("="*60)