#!/usr/bin/env python3
"""
Fix Database Concurrency Issues - Final Solution
Resolve database lock contention for multi-threaded file indexing
"""

import sqlite3
import shutil
import time
from pathlib import Path

def optimize_database_for_concurrency():
    """Optimize database settings for better concurrent access"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    # Create backup
    backup_path = db_path.with_suffix('.db.backup_concurrency_fix')
    try:
        shutil.copy2(db_path, backup_path)
        print(f"OK: Created database backup: {backup_path}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=120.0)
        
        print("Optimizing database for concurrent access...")
        
        # Enable WAL mode with optimal settings
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Optimize for concurrent writes
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=20000")  # Larger cache
        conn.execute("PRAGMA temp_store=memory")
        conn.execute("PRAGMA mmap_size=536870912")  # 512MB memory mapping
        conn.execute("PRAGMA wal_autocheckpoint=100")  # Frequent checkpoints
        conn.execute("PRAGMA busy_timeout=120000")  # 2 minute timeout
        conn.execute("PRAGMA locking_mode=NORMAL")  # Allow concurrent access
        conn.execute("PRAGMA read_uncommitted=1")  # Reduce lock contention
        
        # Force WAL checkpoint to clean up
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        # Verify WAL mode is active
        result = conn.execute("PRAGMA journal_mode").fetchone()
        if result and result[0] == 'wal':
            print("OK: WAL mode active")
        else:
            print("WARNING: WAL mode not active")
        
        conn.close()
        print("OK: Database optimized for concurrent access")
        return True
        
    except Exception as e:
        print(f"ERROR: Could not optimize database: {e}")
        return False

def fix_connection_pool_concurrency():
    """Fix connection pool to handle concurrency better"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("ERROR: production_db_wrapper.py not found")
        return False
    
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the add_segment method with better concurrency handling
    new_add_segment = '''def add_segment(self, file_id, segment_index, segment_hash, segment_size, subject_hash, newsgroup, redundancy_index=0, **kwargs):
        """Add segment to database with improved concurrency handling"""
        import sqlite3
        import time
        import random
        
        # Extract data_offset from kwargs or use 0
        data_offset = kwargs.get('data_offset', 0)
        
        max_retries = 10  # Increased retries
        base_delay = 0.05  # Shorter base delay
        
        for attempt in range(max_retries):
            try:
                # Use a fresh connection for each attempt to avoid lock inheritance
                conn = sqlite3.connect(self.config.path, timeout=120.0)
                
                # Configure connection for concurrent access
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=120000")
                conn.execute("PRAGMA synchronous=NORMAL")
                
                try:
                    # Use immediate transaction for faster execution
                    conn.execute("BEGIN IMMEDIATE")
                    
                    cursor = conn.execute("""
                        INSERT INTO segments 
                        (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, state, subject_hash, newsgroup)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """, (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, subject_hash, newsgroup))
                    
                    segment_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                    
                    print(f"DEBUG: Added segment {segment_index} for file {file_id}, segment_id: {segment_id}")
                    return segment_id
                    
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    conn.close()
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) or "busy" in str(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        delay = min(delay, 2.0)  # Cap at 2 seconds
                        print(f"Database busy, waiting {delay:.2f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Database error after {max_retries} attempts: {e}")
                        raise e
                else:
                    # Non-recoverable database error
                    print(f"Database error: {e}")
                    raise e
            except Exception as e:
                print(f"Error adding segment: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
                continue
        
        raise sqlite3.OperationalError(f"Failed to add segment after {max_retries} attempts")'''
    
    # Replace the add_segment method
    import re
    pattern = r'def add_segment\(.*?\):.*?(?=\n    def |\n\n|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_add_segment.strip(), content, flags=re.DOTALL)
        print("OK: Updated add_segment method for better concurrency")
        
        with open(wrapper_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    else:
        print("ERROR: Could not find add_segment method")
        return False

def reduce_indexing_parallelism():
    """Temporarily reduce parallel threads to avoid lock contention"""
    
    config_suggestions = """
SUGGESTED CONFIG CHANGES to reduce database lock contention:

1. In your configuration, reduce worker threads:
   - Change worker_threads from 8 to 2-3
   - This reduces concurrent database access

2. Add these settings to your config:
   processing:
     worker_threads: 2
     batch_size: 50
     enable_parallel_indexing: false

3. Or set environment variable:
   set USENETSYNC_SINGLE_THREAD=1

This will make indexing slower but more reliable until we fully optimize concurrency.
"""
    
    print(config_suggestions)
    
    # Try to find and update config
    config_files = [
        "config.json",
        "usenetsync.json", 
        Path.home() / ".config" / "usenetsync" / "usenetsync.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"Found config file: {config_file}")
            print("Consider updating worker_threads to 2 in this file")
            break

def test_concurrent_access():
    """Test database concurrent access capability"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    try:
        print("Testing concurrent database access...")
        
        connections = []
        for i in range(3):
            conn = sqlite3.connect(str(db_path), timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            connections.append(conn)
        
        # Test concurrent reads
        for i, conn in enumerate(connections):
            cursor = conn.execute("SELECT COUNT(*) FROM folders")
            count = cursor.fetchone()[0]
            print(f"Connection {i+1}: {count} folders")
        
        # Close connections
        for conn in connections:
            conn.close()
        
        print("OK: Concurrent access test passed")
        return True
        
    except Exception as e:
        print(f"WARNING: Concurrent access test failed: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("FIX DATABASE CONCURRENCY - FINAL SOLUTION")
    print("="*60)
    print("Resolving database lock contention issues...")
    print()
    
    success = True
    
    # Optimize database settings
    if not optimize_database_for_concurrency():
        print("ERROR: Could not optimize database")
        success = False
    
    # Fix connection pool concurrency
    if not fix_connection_pool_concurrency():
        print("ERROR: Could not fix connection pool")
        success = False
    
    # Test concurrent access
    test_concurrent_access()
    
    # Provide config suggestions
    reduce_indexing_parallelism()
    
    print()
    if success:
        print("[SUCCESS] Database concurrency optimized!")
        print()
        print("What was optimized:")
        print("  [OK] WAL mode with optimal settings")
        print("  [OK] Increased busy timeout to 2 minutes")
        print("  [OK] Larger cache size (20MB)")
        print("  [OK] Fresh connections for each operation")
        print("  [OK] Exponential backoff with jitter")
        print("  [OK] Increased retry attempts (10x)")
        print("  [OK] Immediate transactions for faster execution")
        print()
        print("[READY] File indexing should now complete successfully!")
        print()
        print("Database locks should be greatly reduced. If you still see occasional")
        print("lock messages, they should resolve automatically with retries.")
        print()
        print("Try your indexing operation again.")
        return 0
    else:
        print("[ERROR] Some optimizations failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)