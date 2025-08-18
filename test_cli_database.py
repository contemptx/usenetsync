#!/usr/bin/env python3
"""
Comprehensive CLI and Database Integration Test
Tests all CLI commands with real database operations
"""

import subprocess
import json
import os
import sys
import tempfile
import psycopg2
from pathlib import Path
import time
import uuid

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'usenetsync',
    'user': 'usenet',
    'password': 'usenet_secure_2024'
}

class CLIDatabaseTester:
    def __init__(self):
        self.test_results = []
        self.test_files = []
        self.test_shares = []
        self.temp_dir = None
        self.conn = None
        self.cursor = None
        
    def setup(self):
        """Set up test environment"""
        print("Setting up test environment...")
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="usenetsync_test_")
        print(f"  Created temp directory: {self.temp_dir}")
        
        # Create test files
        for i in range(3):
            file_path = Path(self.temp_dir) / f"test_file_{i}.txt"
            content = f"Test content {i}\n" * 100  # Make files with some size
            file_path.write_text(content)
            self.test_files.append(str(file_path))
            print(f"  Created test file: {file_path.name}")
        
        # Connect to database
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("  Connected to database")
        except Exception as e:
            print(f"  Failed to connect to database: {e}")
            return False
        
        return True
    
    def cleanup(self):
        """Clean up test environment"""
        print("\nCleaning up test environment...")
        
        # Delete test shares from database
        if self.cursor and self.test_shares:
            for share_id in self.test_shares:
                try:
                    # Delete related records first
                    self.cursor.execute("DELETE FROM files WHERE share_id = %s", (share_id,))
                    self.cursor.execute("DELETE FROM uploads WHERE share_id = %s", (share_id,))
                    self.cursor.execute("DELETE FROM downloads WHERE share_id = %s", (share_id,))
                    self.cursor.execute("DELETE FROM shares WHERE share_id = %s", (share_id,))
                    self.conn.commit()
                    print(f"  Deleted share: {share_id}")
                except Exception as e:
                    print(f"  Failed to delete share {share_id}: {e}")
        
        # Close database connection
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        
        # Delete temp files
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"  Deleted temp directory: {self.temp_dir}")
    
    def run_cli_command(self, command_args):
        """Run a CLI command and return the result"""
        cmd = ['python3', 'src/cli.py'] + command_args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Try to parse JSON output
            if result.stdout:
                try:
                    return json.loads(result.stdout), result.returncode
                except json.JSONDecodeError:
                    return result.stdout, result.returncode
            elif result.stderr:
                try:
                    return json.loads(result.stderr), result.returncode
                except json.JSONDecodeError:
                    return result.stderr, result.returncode
            else:
                return None, result.returncode
                
        except subprocess.TimeoutExpired:
            return "Command timed out", 1
        except Exception as e:
            return str(e), 1
    
    def test_create_share(self):
        """Test creating shares"""
        print("\n" + "="*60)
        print("TEST: Create Share")
        print("="*60)
        
        test_cases = [
            {
                'name': 'Public share with single file',
                'args': ['create-share', '--files', self.test_files[0], '--type', 'public'],
                'expected_type': 'public'
            },
            {
                'name': 'Private share with multiple files',
                'args': ['create-share'] + ['--files', self.test_files[0], '--files', self.test_files[1]] + ['--type', 'private'],
                'expected_type': 'private'
            },
            {
                'name': 'Protected share with password',
                'args': ['create-share', '--files', self.test_files[2], '--type', 'protected', '--password', 'secret123'],
                'expected_type': 'protected'
            }
        ]
        
        for test in test_cases:
            print(f"\n{test['name']}:")
            output, returncode = self.run_cli_command(test['args'])
            
            if returncode == 0 and isinstance(output, dict):
                share_id = output.get('shareId')
                self.test_shares.append(share_id)
                
                # Verify in database
                self.cursor.execute(
                    "SELECT type, file_count, size FROM shares WHERE share_id = %s",
                    (share_id,)
                )
                db_result = self.cursor.fetchone()
                
                if db_result:
                    print(f"  ✓ Share created: {share_id}")
                    print(f"    Type: {db_result[0]}")
                    print(f"    Files: {db_result[1]}")
                    print(f"    Size: {db_result[2]} bytes")
                    
                    if db_result[0] == test['expected_type']:
                        print(f"  ✓ Type matches expected: {test['expected_type']}")
                        self.test_results.append(('create_share', test['name'], True))
                    else:
                        print(f"  ✗ Type mismatch: expected {test['expected_type']}, got {db_result[0]}")
                        self.test_results.append(('create_share', test['name'], False))
                else:
                    print(f"  ✗ Share not found in database")
                    self.test_results.append(('create_share', test['name'], False))
            else:
                print(f"  ✗ Failed to create share: {output}")
                self.test_results.append(('create_share', test['name'], False))
    
    def test_share_details(self):
        """Test retrieving share details"""
        print("\n" + "="*60)
        print("TEST: Share Details")
        print("="*60)
        
        if not self.test_shares:
            print("  ⚠ No shares to test")
            return
        
        for share_id in self.test_shares[:1]:  # Test first share
            print(f"\nRetrieving details for: {share_id}")
            output, returncode = self.run_cli_command(['share-details', '--share-id', share_id])
            
            if returncode == 0 and isinstance(output, dict):
                print(f"  ✓ Retrieved share details")
                print(f"    ID: {output.get('shareId')}")
                print(f"    Type: {output.get('type')}")
                print(f"    Size: {output.get('size')} bytes")
                print(f"    Files: {output.get('fileCount')}")
                print(f"    Created: {output.get('createdAt')}")
                self.test_results.append(('share_details', share_id, True))
            else:
                print(f"  ✗ Failed to retrieve details: {output}")
                self.test_results.append(('share_details', share_id, False))
    
    def test_server_management(self):
        """Test server configuration in database"""
        print("\n" + "="*60)
        print("TEST: Server Management")
        print("="*60)
        
        # Add a test server directly to database
        test_server = {
            'name': f'test_server_{uuid.uuid4().hex[:8]}',
            'hostname': 'news.example.com',
            'port': 119,
            'username': 'testuser',
            'password': 'testpass',
            'use_ssl': True,
            'enabled': True
        }
        
        try:
            self.cursor.execute("""
                INSERT INTO servers (name, hostname, port, username, password, use_ssl, enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, tuple(test_server.values()))
            server_id = self.cursor.fetchone()[0]
            self.conn.commit()
            print(f"  ✓ Added test server: {test_server['name']}")
            
            # Test connection (will fail but should handle gracefully)
            output, returncode = self.run_cli_command([
                'test-connection',
                '--hostname', test_server['hostname'],
                '--port', str(test_server['port']),
                '--username', test_server['username'],
                '--password', test_server['password'],
                '--ssl' if test_server['use_ssl'] else '--no-ssl'
            ])
            
            # We expect it to fail since it's a fake server
            if returncode != 0:
                print(f"  ✓ Connection test handled gracefully")
                if isinstance(output, dict) and 'error' in output:
                    print(f"    Error: {output['error']}")
                self.test_results.append(('server_test', test_server['name'], True))
            else:
                print(f"  ⚠ Unexpected success for fake server")
                self.test_results.append(('server_test', test_server['name'], False))
            
            # Clean up
            self.cursor.execute("DELETE FROM servers WHERE id = %s", (server_id,))
            self.conn.commit()
            
        except Exception as e:
            print(f"  ✗ Server test failed: {e}")
            self.test_results.append(('server_test', 'test_server', False))
    
    def test_upload_tracking(self):
        """Test upload tracking in database"""
        print("\n" + "="*60)
        print("TEST: Upload Tracking")
        print("="*60)
        
        if not self.test_shares:
            print("  ⚠ No shares to test")
            return
        
        # Simulate upload record
        upload_id = str(uuid.uuid4())
        share_id = self.test_shares[0]
        
        try:
            # Insert upload record
            self.cursor.execute("""
                INSERT INTO uploads (id, share_id, file_path, file_size, status, progress)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (upload_id, share_id, self.test_files[0], 1024, 'uploading', 0))
            self.conn.commit()
            print(f"  ✓ Created upload record: {upload_id}")
            
            # Simulate progress updates
            for progress in [25, 50, 75, 100]:
                self.cursor.execute("""
                    UPDATE uploads 
                    SET progress = %s,
                        status = CASE WHEN %s = 100 THEN 'completed' ELSE 'uploading' END
                    WHERE id = %s
                """, (progress, progress, upload_id))
                self.conn.commit()
                time.sleep(0.1)  # Small delay to simulate real upload
            
            # Verify final status
            self.cursor.execute("SELECT status, progress FROM uploads WHERE id = %s", (upload_id,))
            status, progress = self.cursor.fetchone()
            
            if status == 'completed' and progress == 100:
                print(f"  ✓ Upload completed successfully")
                self.test_results.append(('upload_tracking', upload_id, True))
            else:
                print(f"  ✗ Upload status incorrect: {status}, {progress}%")
                self.test_results.append(('upload_tracking', upload_id, False))
            
            # Clean up
            self.cursor.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
            self.conn.commit()
            
        except Exception as e:
            print(f"  ✗ Upload tracking failed: {e}")
            self.test_results.append(('upload_tracking', upload_id, False))
    
    def test_download_tracking(self):
        """Test download tracking in database"""
        print("\n" + "="*60)
        print("TEST: Download Tracking")
        print("="*60)
        
        if not self.test_shares:
            print("  ⚠ No shares to test")
            return
        
        # Test download command (won't actually download but should create record)
        share_id = self.test_shares[0]
        dest_dir = Path(self.temp_dir) / "downloads"
        dest_dir.mkdir(exist_ok=True)
        
        output, returncode = self.run_cli_command([
            'download-share',
            '--share-id', share_id,
            '--destination', str(dest_dir)
        ])
        
        # Check if download record was created
        self.cursor.execute(
            "SELECT COUNT(*) FROM downloads WHERE share_id = %s",
            (share_id,)
        )
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            print(f"  ✓ Download record created for share: {share_id}")
            self.test_results.append(('download_tracking', share_id, True))
            
            # Clean up download records
            self.cursor.execute("DELETE FROM downloads WHERE share_id = %s", (share_id,))
            self.conn.commit()
        else:
            print(f"  ⚠ No download record created")
            self.test_results.append(('download_tracking', share_id, False))
    
    def test_database_consistency(self):
        """Test database consistency and relationships"""
        print("\n" + "="*60)
        print("TEST: Database Consistency")
        print("="*60)
        
        # Check orphaned files
        self.cursor.execute("""
            SELECT COUNT(*) FROM files f
            LEFT JOIN shares s ON f.share_id = s.share_id
            WHERE s.share_id IS NULL
        """)
        orphaned_files = self.cursor.fetchone()[0]
        
        if orphaned_files == 0:
            print("  ✓ No orphaned files")
            self.test_results.append(('consistency', 'orphaned_files', True))
        else:
            print(f"  ✗ Found {orphaned_files} orphaned files")
            self.test_results.append(('consistency', 'orphaned_files', False))
        
        # Check share statistics accuracy
        self.cursor.execute("""
            SELECT s.share_id, s.file_count, COUNT(f.id) as actual_count
            FROM shares s
            LEFT JOIN files f ON s.share_id = f.share_id
            WHERE s.share_id = ANY(%s)
            GROUP BY s.share_id, s.file_count
        """, (self.test_shares,))
        
        mismatches = []
        for row in self.cursor.fetchall():
            if row[1] != row[2]:
                mismatches.append(row[0])
        
        if not mismatches:
            print("  ✓ Share file counts are accurate")
            self.test_results.append(('consistency', 'file_counts', True))
        else:
            print(f"  ✗ File count mismatches in shares: {mismatches}")
            self.test_results.append(('consistency', 'file_counts', False))
    
    def test_index_folder(self):
        """Test folder indexing"""
        print("\n" + "="*60)
        print("TEST: Folder Indexing")
        print("="*60)
        
        output, returncode = self.run_cli_command(['index-folder', '--path', self.temp_dir])
        
        if returncode == 0 and isinstance(output, dict):
            print(f"  ✓ Indexed folder: {output.get('name')}")
            print(f"    Total size: {output.get('size')} bytes")
            print(f"    Children: {len(output.get('children', []))}")
            
            # Verify it found our test files
            children = output.get('children', [])
            test_file_names = [Path(f).name for f in self.test_files]
            found_files = [c['name'] for c in children if c['type'] == 'file']
            
            if all(name in found_files for name in test_file_names):
                print(f"  ✓ All test files found in index")
                self.test_results.append(('index_folder', self.temp_dir, True))
            else:
                print(f"  ✗ Some test files missing from index")
                self.test_results.append(('index_folder', self.temp_dir, False))
        else:
            print(f"  ✗ Failed to index folder: {output}")
            self.test_results.append(('index_folder', self.temp_dir, False))
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("TEST REPORT")
        print("="*60)
        
        # Count results
        passed = sum(1 for _, _, result in self.test_results if result)
        failed = sum(1 for _, _, result in self.test_results if not result)
        total = len(self.test_results)
        
        print(f"\nResults: {passed}/{total} passed, {failed}/{total} failed")
        
        if failed > 0:
            print("\nFailed tests:")
            for category, name, result in self.test_results:
                if not result:
                    print(f"  ✗ {category}: {name}")
        
        print("\nAll tests:")
        for category, name, result in self.test_results:
            status = "✓" if result else "✗"
            print(f"  {status} {category}: {name}")
        
        return failed == 0

def main():
    """Main test function"""
    print("="*60)
    print("CLI and Database Integration Test")
    print("="*60)
    
    tester = CLIDatabaseTester()
    
    try:
        # Setup
        if not tester.setup():
            print("Failed to set up test environment")
            return False
        
        # Run tests
        tester.test_create_share()
        tester.test_share_details()
        tester.test_server_management()
        tester.test_upload_tracking()
        tester.test_download_tracking()
        tester.test_database_consistency()
        tester.test_index_folder()
        
        # Generate report
        success = tester.generate_report()
        
        return success
        
    finally:
        # Cleanup
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)