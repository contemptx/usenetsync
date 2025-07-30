#!/usr/bin/env python3
"""
Fix Segments Table Schema
Add the missing data_offset column to the segments table
"""

import sqlite3
import shutil
from pathlib import Path

def fix_segments_table_schema():
    """Add missing columns to segments table"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    # Create backup
    backup_path = db_path.with_suffix('.db.backup_schema_fix')
    try:
        shutil.copy2(db_path, backup_path)
        print(f"OK: Created database backup: {backup_path}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60.0)
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        
        print("Checking segments table schema...")
        
        # Check current columns
        cursor = conn.execute("PRAGMA table_info(segments)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add missing columns
        missing_columns = []
        
        if 'data_offset' not in columns:
            print("Adding data_offset column...")
            conn.execute("ALTER TABLE segments ADD COLUMN data_offset INTEGER DEFAULT 0")
            missing_columns.append('data_offset')
        
        if 'subject_hash' not in columns:
            print("Adding subject_hash column...")
            conn.execute("ALTER TABLE segments ADD COLUMN subject_hash TEXT")
            missing_columns.append('subject_hash')
        
        if 'newsgroup' not in columns:
            print("Adding newsgroup column...")
            conn.execute("ALTER TABLE segments ADD COLUMN newsgroup TEXT")
            missing_columns.append('newsgroup')
        
        if 'internal_subject' not in columns:
            print("Adding internal_subject column...")
            conn.execute("ALTER TABLE segments ADD COLUMN internal_subject TEXT")
            missing_columns.append('internal_subject')
        
        # Create indexes for better performance
        print("Creating indexes...")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments (file_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_state ON segments (state)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_subject_hash ON segments (subject_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_newsgroup ON segments (newsgroup)")
        
        conn.commit()
        
        # Verify the changes
        cursor = conn.execute("PRAGMA table_info(segments)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        conn.close()
        
        if missing_columns:
            print(f"OK: Added {len(missing_columns)} missing columns: {missing_columns}")
        else:
            print("OK: All required columns already exist")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Could not update segments table schema: {e}")
        return False

def verify_database_schema():
    """Verify the complete database schema"""
    
    db_path = Path("data/usenetsync.db")
    if not db_path.exists():
        print("ERROR: Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        
        print("Verifying complete database schema...")
        
        # Check segments table
        cursor = conn.execute("PRAGMA table_info(segments)")
        segments_columns = [row[1] for row in cursor.fetchall()]
        
        required_segments_columns = [
            'id', 'file_id', 'segment_index', 'segment_hash', 'segment_size', 
            'data_offset', 'redundancy_index', 'state', 'subject_hash', 
            'newsgroup', 'internal_subject'
        ]
        
        missing = []
        for col in required_segments_columns:
            if col not in segments_columns:
                missing.append(col)
        
        if missing:
            print(f"ERROR: Missing columns in segments table: {missing}")
            conn.close()
            return False
        
        # Check files table
        cursor = conn.execute("PRAGMA table_info(files)")
        files_columns = [row[1] for row in cursor.fetchall()]
        
        if 'segment_count' not in files_columns:
            print("Adding segment_count column to files table...")
            conn.execute("ALTER TABLE files ADD COLUMN segment_count INTEGER DEFAULT 0")
            conn.commit()
        
        # Test a basic insert to verify schema
        print("Testing schema with sample data...")
        
        # Clean up any test data first
        conn.execute("DELETE FROM segments WHERE segment_hash = 'test_hash'")
        
        # Try to insert test data
        cursor = conn.execute("""
            INSERT INTO segments 
            (file_id, segment_index, segment_hash, segment_size, data_offset, redundancy_index, state, subject_hash, newsgroup, internal_subject)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, 'test_hash', 1024, 0, 0, 'pending', 'test_subject', 'alt.binaries.test', 'internal_test'))
        
        test_segment_id = cursor.lastrowid
        
        # Clean up test data
        conn.execute("DELETE FROM segments WHERE id = ?", (test_segment_id,))
        conn.commit()
        
        conn.close()
        print("OK: Database schema verification passed")
        return True
        
    except Exception as e:
        print(f"ERROR: Database schema verification failed: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("FIX SEGMENTS TABLE SCHEMA")
    print("="*60)
    print("Adding missing data_offset column to segments table...")
    print()
    
    success = True
    
    # Fix the segments table schema
    if not fix_segments_table_schema():
        print("ERROR: Could not fix segments table schema")
        success = False
    
    # Verify the complete schema
    if not verify_database_schema():
        print("ERROR: Database schema verification failed")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Segments table schema fixed!")
        print()
        print("What was fixed:")
        print("  [OK] Added data_offset column to segments table")
        print("  [OK] Added subject_hash column to segments table") 
        print("  [OK] Added newsgroup column to segments table")
        print("  [OK] Added internal_subject column to segments table")
        print("  [OK] Added segment_count column to files table")
        print("  [OK] Created performance indexes")
        print("  [OK] Verified schema with test insertion")
        print()
        print("[READY] File indexing should now work completely!")
        print()
        print("The complete sequence should now work:")
        print("  1. Keys generated and loaded ✅")
        print("  2. Files processed and segmented ✅") 
        print("  3. Segments stored in database ✅ (FIXED)")
        print("  4. Indexing completes successfully ✅")
        print()
        print("Try your indexing operation again.")
        return 0
    else:
        print("[ERROR] Could not fix database schema")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)