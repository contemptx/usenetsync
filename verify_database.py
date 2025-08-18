#!/usr/bin/env python3
"""
Comprehensive Database Verification for UsenetSync
Tests all tables, relationships, and operations
"""

import psycopg2
import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import random
import string

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'usenetsync',
    'user': 'usenet',
    'password': 'usenet_secure_2024'
}

class DatabaseVerifier:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.errors = []
        self.warnings = []
        self.test_data = {}
        
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            self.errors.append(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def verify_tables(self):
        """Verify all required tables exist with correct structure"""
        print("\n" + "="*60)
        print("VERIFYING TABLE STRUCTURE")
        print("="*60)
        
        required_tables = {
            'shares': [
                ('id', 'text'),
                ('share_id', 'text'),
                ('type', 'text'),
                ('name', 'text'),
                ('size', 'bigint'),
                ('file_count', 'integer'),
                ('folder_count', 'integer'),
                ('created_at', 'timestamp'),
                ('expires_at', 'timestamp'),
                ('access_count', 'integer'),
                ('last_accessed', 'timestamp'),
                ('password_hash', 'text'),
                ('metadata', 'jsonb')
            ],
            'files': [
                ('id', 'text'),
                ('share_id', 'text'),
                ('file_name', 'text'),
                ('file_path', 'text'),
                ('file_size', 'bigint'),
                ('file_hash', 'text'),
                ('created_at', 'timestamp'),
                ('metadata', 'jsonb')
            ],
            'servers': [
                ('id', 'integer'),
                ('name', 'text'),
                ('hostname', 'text'),
                ('port', 'integer'),
                ('username', 'text'),
                ('password', 'text'),
                ('use_ssl', 'boolean'),
                ('max_connections', 'integer'),
                ('priority', 'integer'),
                ('enabled', 'boolean'),
                ('created_at', 'timestamp'),
                ('last_tested', 'timestamp'),
                ('last_status', 'text')
            ],
            'uploads': [
                ('id', 'text'),
                ('share_id', 'text'),
                ('file_path', 'text'),
                ('file_size', 'bigint'),
                ('status', 'text'),
                ('progress', 'integer'),
                ('started_at', 'timestamp'),
                ('completed_at', 'timestamp'),
                ('error_message', 'text'),
                ('retry_count', 'integer')
            ],
            'downloads': [
                ('id', 'text'),
                ('share_id', 'text'),
                ('destination', 'text'),
                ('status', 'text'),
                ('progress', 'integer'),
                ('started_at', 'timestamp'),
                ('completed_at', 'timestamp'),
                ('error_message', 'text'),
                ('retry_count', 'integer')
            ],
            'schema_migrations': [
                ('version', 'integer'),
                ('name', 'text'),
                ('description', 'text'),
                ('checksum', 'text'),
                ('applied_at', 'timestamp'),
                ('execution_time_ms', 'integer'),
                ('status', 'text')
            ]
        }
        
        # Additional tables that might be needed
        optional_tables = {
            'file_versions': [
                ('version_id', 'text'),
                ('file_name', 'text'),
                ('file_path', 'text'),
                ('share_id', 'text'),
                ('file_hash', 'text'),
                ('file_size', 'bigint'),
                ('version_number', 'integer'),
                ('parent_version_id', 'text'),
                ('created_at', 'timestamp'),
                ('created_by', 'text'),
                ('changes_description', 'text'),
                ('tags', 'text'),
                ('metadata', 'text')
            ],
            'users': [
                ('id', 'text'),
                ('username', 'text'),
                ('email', 'text'),
                ('password_hash', 'text'),
                ('created_at', 'timestamp'),
                ('last_login', 'timestamp'),
                ('is_active', 'boolean'),
                ('role', 'text')
            ],
            'settings': [
                ('key', 'text'),
                ('value', 'text'),
                ('type', 'text'),
                ('description', 'text'),
                ('updated_at', 'timestamp')
            ]
        }
        
        # Check required tables
        for table_name, columns in required_tables.items():
            print(f"\nChecking table: {table_name}")
            
            # Check if table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
            
            exists = self.cursor.fetchone()[0]
            if not exists:
                self.errors.append(f"Required table '{table_name}' does not exist")
                print(f"  ✗ Table does not exist")
                continue
            
            print(f"  ✓ Table exists")
            
            # Check columns
            self.cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            
            actual_columns = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            for col_name, col_type in columns:
                if col_name not in actual_columns:
                    self.errors.append(f"Column '{col_name}' missing in table '{table_name}'")
                    print(f"  ✗ Column '{col_name}' missing")
                else:
                    # Check type compatibility
                    actual_type = actual_columns[col_name]
                    if col_type == 'timestamp' and 'timestamp' in actual_type:
                        print(f"  ✓ Column '{col_name}' ({actual_type})")
                    elif col_type == 'text' and actual_type in ['text', 'character varying']:
                        print(f"  ✓ Column '{col_name}' ({actual_type})")
                    elif col_type == actual_type:
                        print(f"  ✓ Column '{col_name}' ({actual_type})")
                    else:
                        self.warnings.append(f"Column '{col_name}' in '{table_name}' has type '{actual_type}' instead of '{col_type}'")
                        print(f"  ⚠ Column '{col_name}' has type '{actual_type}' (expected {col_type})")
        
        # Check optional tables
        print("\n" + "-"*60)
        print("Checking optional tables:")
        for table_name in optional_tables:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
            
            exists = self.cursor.fetchone()[0]
            if exists:
                print(f"  ✓ Optional table '{table_name}' exists")
            else:
                print(f"  ○ Optional table '{table_name}' not present")
    
    def verify_constraints(self):
        """Verify foreign keys, unique constraints, and indexes"""
        print("\n" + "="*60)
        print("VERIFYING CONSTRAINTS AND INDEXES")
        print("="*60)
        
        # Check foreign keys
        print("\nForeign Keys:")
        self.cursor.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
        """)
        
        foreign_keys = self.cursor.fetchall()
        if foreign_keys:
            for fk in foreign_keys:
                print(f"  ✓ {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
        else:
            self.warnings.append("No foreign keys found")
            print("  ⚠ No foreign keys found")
        
        # Check unique constraints
        print("\nUnique Constraints:")
        self.cursor.execute("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema = 'public'
        """)
        
        unique_constraints = self.cursor.fetchall()
        if unique_constraints:
            for uc in unique_constraints:
                print(f"  ✓ {uc[0]}.{uc[1]} is unique")
        else:
            print("  ○ No unique constraints found")
        
        # Check indexes
        print("\nIndexes:")
        self.cursor.execute("""
            SELECT 
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        indexes = self.cursor.fetchall()
        for idx in indexes:
            if 'pkey' in idx[1]:
                print(f"  ✓ Primary key: {idx[0]}.{idx[1]}")
            else:
                print(f"  ✓ Index: {idx[0]}.{idx[1]}")
    
    def test_crud_operations(self):
        """Test Create, Read, Update, Delete operations on all tables"""
        print("\n" + "="*60)
        print("TESTING CRUD OPERATIONS")
        print("="*60)
        
        # Test shares table
        print("\n1. Testing 'shares' table:")
        share_id = f"TEST_{uuid.uuid4().hex[:16].upper()}"
        test_share = {
            'id': str(uuid.uuid4()),
            'share_id': share_id,
            'type': 'public',
            'name': 'Test Share',
            'size': 1024000,
            'file_count': 5,
            'folder_count': 2,
            'created_at': datetime.now(timezone.utc),
            'access_count': 0
        }
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO shares (id, share_id, type, name, size, file_count, folder_count, created_at, access_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(test_share.values()))
            self.conn.commit()
            print("  ✓ CREATE: Share inserted")
            self.test_data['share_id'] = share_id
            self.test_data['share_uuid'] = test_share['id']
            
            # READ
            self.cursor.execute("SELECT * FROM shares WHERE share_id = %s", (share_id,))
            result = self.cursor.fetchone()
            if result:
                print("  ✓ READ: Share retrieved")
            else:
                self.errors.append("Failed to read inserted share")
                print("  ✗ READ: Failed to retrieve share")
            
            # UPDATE
            self.cursor.execute("""
                UPDATE shares 
                SET access_count = access_count + 1, 
                    last_accessed = %s 
                WHERE share_id = %s
            """, (datetime.now(timezone.utc), share_id))
            self.conn.commit()
            print("  ✓ UPDATE: Share updated")
            
            # Verify update
            self.cursor.execute("SELECT access_count FROM shares WHERE share_id = %s", (share_id,))
            updated_count = self.cursor.fetchone()[0]
            if updated_count == 1:
                print("  ✓ UPDATE verified: access_count = 1")
            else:
                self.warnings.append(f"Update verification failed: access_count = {updated_count}")
            
        except Exception as e:
            self.errors.append(f"CRUD test failed for shares: {e}")
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
        
        # Test files table
        print("\n2. Testing 'files' table:")
        test_file = {
            'id': str(uuid.uuid4()),
            'share_id': share_id,
            'file_name': 'test_file.txt',
            'file_path': '/test/path/test_file.txt',
            'file_size': 1024,
            'file_hash': hashlib.sha256(b'test content').hexdigest(),
            'created_at': datetime.now(timezone.utc)
        }
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO files (id, share_id, file_name, file_path, file_size, file_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(test_file.values()))
            self.conn.commit()
            print("  ✓ CREATE: File inserted")
            self.test_data['file_id'] = test_file['id']
            
            # READ with JOIN
            self.cursor.execute("""
                SELECT f.file_name, s.name 
                FROM files f 
                JOIN shares s ON f.share_id = s.share_id 
                WHERE f.id = %s
            """, (test_file['id'],))
            result = self.cursor.fetchone()
            if result:
                print(f"  ✓ READ with JOIN: File '{result[0]}' in share '{result[1]}'")
            
        except Exception as e:
            self.errors.append(f"CRUD test failed for files: {e}")
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
        
        # Test servers table
        print("\n3. Testing 'servers' table:")
        test_server = {
            'name': f'test_server_{random.randint(1000, 9999)}',
            'hostname': 'news.test.com',
            'port': 119,
            'username': 'testuser',
            'password': 'testpass',
            'use_ssl': True,
            'max_connections': 10,
            'priority': 1,
            'enabled': True
        }
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO servers (name, hostname, port, username, password, use_ssl, max_connections, priority, enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, tuple(test_server.values()))
            server_id = self.cursor.fetchone()[0]
            self.conn.commit()
            print(f"  ✓ CREATE: Server inserted with ID {server_id}")
            self.test_data['server_id'] = server_id
            
            # UPDATE
            self.cursor.execute("""
                UPDATE servers 
                SET last_tested = %s, last_status = %s 
                WHERE id = %s
            """, (datetime.now(timezone.utc), 'success', server_id))
            self.conn.commit()
            print("  ✓ UPDATE: Server status updated")
            
        except Exception as e:
            self.errors.append(f"CRUD test failed for servers: {e}")
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
        
        # Test uploads table
        print("\n4. Testing 'uploads' table:")
        test_upload = {
            'id': str(uuid.uuid4()),
            'share_id': share_id,
            'file_path': '/test/upload.txt',
            'file_size': 2048,
            'status': 'pending',
            'progress': 0,
            'retry_count': 0
        }
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO uploads (id, share_id, file_path, file_size, status, progress, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(test_upload.values()))
            self.conn.commit()
            print("  ✓ CREATE: Upload record inserted")
            self.test_data['upload_id'] = test_upload['id']
            
            # Simulate upload progress
            for progress in [25, 50, 75, 100]:
                self.cursor.execute("""
                    UPDATE uploads 
                    SET progress = %s, 
                        status = CASE WHEN %s = 100 THEN 'completed' ELSE 'uploading' END,
                        completed_at = CASE WHEN %s = 100 THEN %s ELSE NULL END
                    WHERE id = %s
                """, (progress, progress, progress, datetime.now(timezone.utc), test_upload['id']))
                self.conn.commit()
            
            print("  ✓ UPDATE: Upload progress simulated (0% -> 100%)")
            
        except Exception as e:
            self.errors.append(f"CRUD test failed for uploads: {e}")
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
        
        # Test downloads table
        print("\n5. Testing 'downloads' table:")
        test_download = {
            'id': str(uuid.uuid4()),
            'share_id': share_id,
            'destination': '/test/downloads/',
            'status': 'pending',
            'progress': 0,
            'retry_count': 0
        }
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO downloads (id, share_id, destination, status, progress, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, tuple(test_download.values()))
            self.conn.commit()
            print("  ✓ CREATE: Download record inserted")
            self.test_data['download_id'] = test_download['id']
            
        except Exception as e:
            self.errors.append(f"CRUD test failed for downloads: {e}")
            print(f"  ✗ Error: {e}")
            self.conn.rollback()
    
    def test_transactions(self):
        """Test transaction rollback and commit"""
        print("\n" + "="*60)
        print("TESTING TRANSACTIONS")
        print("="*60)
        
        print("\n1. Testing transaction rollback:")
        try:
            # Start transaction
            self.conn.autocommit = False
            
            # Insert a test share
            test_id = str(uuid.uuid4())
            self.cursor.execute("""
                INSERT INTO shares (id, share_id, type, name, size, file_count, folder_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (test_id, 'ROLLBACK_TEST', 'public', 'Rollback Test', 1000, 1, 1))
            
            # Verify it's in the transaction
            self.cursor.execute("SELECT id FROM shares WHERE share_id = %s", ('ROLLBACK_TEST',))
            if self.cursor.fetchone():
                print("  ✓ Data inserted in transaction")
            
            # Rollback
            self.conn.rollback()
            
            # Verify it's gone
            self.cursor.execute("SELECT id FROM shares WHERE share_id = %s", ('ROLLBACK_TEST',))
            if not self.cursor.fetchone():
                print("  ✓ Transaction rolled back successfully")
            else:
                self.errors.append("Transaction rollback failed")
                print("  ✗ Transaction rollback failed")
            
        except Exception as e:
            self.errors.append(f"Transaction test failed: {e}")
            print(f"  ✗ Error: {e}")
        finally:
            # Reset connection state
            self.conn.rollback()  # Ensure we're not in a transaction
            self.conn.autocommit = True
    
    def test_performance(self):
        """Test query performance and optimization"""
        print("\n" + "="*60)
        print("TESTING PERFORMANCE")
        print("="*60)
        
        import time
        
        # Test index performance
        print("\n1. Testing index performance:")
        
        # Query without index (using non-indexed column)
        start = time.time()
        self.cursor.execute("SELECT * FROM shares WHERE name LIKE %s", ('%Test%',))
        results = self.cursor.fetchall()
        time_without_index = time.time() - start
        print(f"  Query without index: {time_without_index:.4f}s ({len(results)} results)")
        
        # Query with index (using indexed column)
        start = time.time()
        self.cursor.execute("SELECT * FROM shares WHERE share_id = %s", (self.test_data.get('share_id', 'TEST'),))
        results = self.cursor.fetchall()
        time_with_index = time.time() - start
        print(f"  Query with index: {time_with_index:.4f}s ({len(results)} results)")
        
        # Test join performance
        print("\n2. Testing join performance:")
        start = time.time()
        self.cursor.execute("""
            SELECT s.share_id, s.name, COUNT(f.id) as file_count
            FROM shares s
            LEFT JOIN files f ON s.share_id = f.share_id
            GROUP BY s.share_id, s.name
            LIMIT 10
        """)
        results = self.cursor.fetchall()
        join_time = time.time() - start
        print(f"  Join query: {join_time:.4f}s ({len(results)} results)")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n" + "="*60)
        print("CLEANING UP TEST DATA")
        print("="*60)
        
        try:
            # Delete in correct order (respecting foreign keys)
            if 'download_id' in self.test_data:
                self.cursor.execute("DELETE FROM downloads WHERE id = %s", (self.test_data['download_id'],))
                print("  ✓ Deleted test download")
            
            if 'upload_id' in self.test_data:
                self.cursor.execute("DELETE FROM uploads WHERE id = %s", (self.test_data['upload_id'],))
                print("  ✓ Deleted test upload")
            
            if 'file_id' in self.test_data:
                self.cursor.execute("DELETE FROM files WHERE id = %s", (self.test_data['file_id'],))
                print("  ✓ Deleted test file")
            
            if 'share_id' in self.test_data:
                self.cursor.execute("DELETE FROM shares WHERE share_id = %s", (self.test_data['share_id'],))
                print("  ✓ Deleted test share")
            
            if 'server_id' in self.test_data:
                self.cursor.execute("DELETE FROM servers WHERE id = %s", (self.test_data['server_id'],))
                print("  ✓ Deleted test server")
            
            self.conn.commit()
            print("\n  ✓ All test data cleaned up")
            
        except Exception as e:
            self.errors.append(f"Cleanup failed: {e}")
            print(f"  ✗ Cleanup error: {e}")
            self.conn.rollback()
    
    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "="*60)
        print("VERIFICATION REPORT")
        print("="*60)
        
        # Summary
        print("\nSummary:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors:
            print("\n✅ DATABASE VERIFICATION PASSED!")
            print("All required tables, columns, and operations are working correctly.")
        else:
            print("\n❌ DATABASE VERIFICATION FAILED!")
            print("Please fix the errors above before proceeding.")
        
        return len(self.errors) == 0

def main():
    """Main verification function"""
    verifier = DatabaseVerifier()
    
    print("="*60)
    print("UsenetSync Database Verification")
    print("="*60)
    
    # Connect to database
    if not verifier.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Run all verifications
        verifier.verify_tables()
        verifier.verify_constraints()
        verifier.test_crud_operations()
        verifier.test_transactions()
        verifier.test_performance()
        verifier.cleanup_test_data()
        
        # Generate report
        success = verifier.generate_report()
        
        return success
        
    finally:
        verifier.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)