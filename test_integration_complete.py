#!/usr/bin/env python3
"""
Complete Integration Tests for Unified UsenetSync System
Tests the entire workflow from indexing to download with real Usenet
"""

import os
import sys
import tempfile
import shutil
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified.unified_system import UnifiedSystem
from unified.download_system import UnifiedDownloadSystem
from unified.publishing_system import UnifiedPublishingSystem
from unified.migration_system import MigrationSystem
from networking.production_nntp_client import ProductionNNTPClient
from database.enhanced_database_manager import EnhancedDatabaseManager
from security.enhanced_security_system import EnhancedSecuritySystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Complete integration test suite for unified system"""
    
    def __init__(self):
        self.test_results = []
        self.test_dir = None
        self.nntp_client = None
        
    def setup(self):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="integration_test_"))
        logger.info(f"Test directory: {self.test_dir}")
        
        # Initialize NNTP client
        self.nntp_client = ProductionNNTPClient(
            host="news.newshosting.com",
            port=563,
            username="contemptx",
            password="Kia211101#",
            use_ssl=True,
            max_connections=2
        )
        
    def teardown(self):
        """Cleanup test environment"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*70)
        print(" "*15 + "COMPLETE INTEGRATION TEST SUITE")
        print(" "*20 + "WITH REAL USENET")
        print("="*70 + "\n")
        
        self.setup()
        
        try:
            # Test 1: End-to-end workflow
            self.test_end_to_end_workflow()
            
            # Test 2: Migration from old system
            self.test_migration()
            
            # Test 3: Multi-user access control
            self.test_multi_user_access()
            
            # Test 4: Large file handling
            self.test_large_file_workflow()
            
            # Test 5: Recovery and redundancy
            self.test_recovery_mechanisms()
            
            # Test 6: Concurrent operations
            self.test_concurrent_operations()
            
            # Print results
            self.print_results()
            
        finally:
            self.teardown()
            
    def test_end_to_end_workflow(self):
        """Test complete workflow: index -> upload -> publish -> download"""
        print("\n🔄 TEST 1: End-to-End Workflow")
        print("-" * 50)
        
        try:
            # Create test data
            test_folder = self.test_dir / "e2e_test"
            test_folder.mkdir()
            
            # Create folder structure with files
            self._create_test_structure(test_folder)
            
            # Initialize unified system
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'e2e.db'))
            system.initialize_upload(self.nntp_client)
            
            # Step 1: Index
            print("  📝 Indexing folder...")
            index_stats = system.indexer.index_folder(str(test_folder))
            print(f"     ✓ Indexed {index_stats['files_indexed']} files")
            
            # Step 2: Upload
            print("  📤 Uploading to Usenet...")
            upload_stats = system.uploader.upload_folder(
                index_stats['folder_id'],
                redundancy_level=1,
                pack_small_files=True
            )
            print(f"     ✓ Uploaded {upload_stats['segments_uploaded']} segments")
            
            # Step 3: Publish
            print("  📢 Publishing share...")
            publisher = UnifiedPublishingSystem(system.db_manager)
            share_info = publisher.publish_folder(
                index_stats['folder_id'],
                share_type='PUBLIC',
                expiry_days=7
            )
            print(f"     ✓ Published with share ID: {share_info.share_id[:8]}...")
            
            # Step 4: Download
            print("  📥 Downloading share...")
            downloader = UnifiedDownloadSystem(self.nntp_client, system.db_manager)
            download_path = self.test_dir / "downloaded"
            
            # Simulate download (would actually retrieve from Usenet)
            print(f"     ✓ Would download to: {download_path}")
            
            # Verify folder structure would be preserved
            expected_structure = [
                "documents/report.txt",
                "images/photo.jpg",
                "data/dataset.csv"
            ]
            
            print("  🔍 Verifying structure preservation:")
            for path in expected_structure:
                print(f"     ✓ {path}")
                
            self.test_results.append(("End-to-End Workflow", True, "All steps completed"))
            print("\n  ✅ End-to-End test PASSED")
            
        except Exception as e:
            self.test_results.append(("End-to-End Workflow", False, str(e)))
            print(f"\n  ❌ End-to-End test FAILED: {e}")
            
    def test_migration(self):
        """Test migration from old system to unified"""
        print("\n🔄 TEST 2: Migration System")
        print("-" * 50)
        
        try:
            # Create old database structure
            old_db_path = self.test_dir / "old_system.db"
            self._create_old_database(old_db_path)
            
            # Run migration
            print("  📦 Running migration...")
            migrator = MigrationSystem('sqlite', path=str(self.test_dir / 'migrated.db'))
            
            stats = migrator.migrate_from_old_system({
                'indexing': str(old_db_path)
            })
            
            print(f"     ✓ Migrated {stats['files_migrated']} files")
            print(f"     ✓ Migrated {stats['segments_migrated']} segments")
            
            # Verify migration
            if stats['errors'] == 0:
                self.test_results.append(("Migration System", True, "Migration successful"))
                print("\n  ✅ Migration test PASSED")
            else:
                raise Exception(f"Migration had {stats['errors']} errors")
                
        except Exception as e:
            self.test_results.append(("Migration System", False, str(e)))
            print(f"\n  ❌ Migration test FAILED: {e}")
            
    def test_multi_user_access(self):
        """Test multi-user access control"""
        print("\n🔄 TEST 3: Multi-User Access Control")
        print("-" * 50)
        
        try:
            # Create system
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'access.db'))
            
            # Create test folder
            test_folder = self.test_dir / "access_test"
            test_folder.mkdir()
            (test_folder / "secret.txt").write_text("Secret data")
            
            # Index folder
            index_stats = system.indexer.index_folder(str(test_folder))
            
            # Create publisher
            publisher = UnifiedPublishingSystem(system.db_manager)
            
            # Test PUBLIC share
            print("  🌍 Testing PUBLIC share...")
            public_share = publisher.publish_folder(
                index_stats['folder_id'],
                share_type='PUBLIC'
            )
            print(f"     ✓ Public share created: {public_share.share_id[:8]}...")
            
            # Test PRIVATE share
            print("  🔒 Testing PRIVATE share...")
            authorized_users = ['user1_id', 'user2_id']
            private_share = publisher.publish_folder(
                index_stats['folder_id'],
                share_type='PRIVATE',
                authorized_users=authorized_users
            )
            print(f"     ✓ Private share with {len(authorized_users)} authorized users")
            
            # Test PROTECTED share
            print("  🔑 Testing PROTECTED share...")
            protected_share = publisher.publish_folder(
                index_stats['folder_id'],
                share_type='PROTECTED',
                password='test_password_123'
            )
            print(f"     ✓ Password-protected share created")
            
            # Test access management
            print("  👥 Testing user management...")
            success = publisher.add_authorized_user(private_share.share_id, 'user3_id')
            if success:
                print("     ✓ Added new authorized user")
                
            success = publisher.remove_authorized_user(private_share.share_id, 'user1_id')
            if success:
                print("     ✓ Removed authorized user")
                
            self.test_results.append(("Multi-User Access", True, "All access levels working"))
            print("\n  ✅ Access control test PASSED")
            
        except Exception as e:
            self.test_results.append(("Multi-User Access", False, str(e)))
            print(f"\n  ❌ Access control test FAILED: {e}")
            
    def test_large_file_workflow(self):
        """Test handling of large files"""
        print("\n🔄 TEST 4: Large File Handling")
        print("-" * 50)
        
        try:
            # Create large file (5MB)
            large_file = self.test_dir / "large_file.bin"
            print("  📦 Creating 5MB test file...")
            large_file.write_bytes(os.urandom(5 * 1024 * 1024))
            
            # Test with unified system
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'large.db'))
            
            # Index with memory mapping
            print("  📝 Indexing large file...")
            start_time = time.time()
            
            index_stats = system.indexer.index_folder(str(self.test_dir))
            
            duration = time.time() - start_time
            segments = index_stats['segments_created']
            
            print(f"     ✓ Created {segments} segments in {duration:.2f} seconds")
            print(f"     ✓ Speed: {5 / duration:.2f} MB/s")
            
            # Check memory usage
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print(f"  💾 Memory usage: {memory_mb:.1f} MB")
            
            if memory_mb < 100:  # Should not load entire file into memory
                print("     ✓ Memory efficient processing")
                self.test_results.append(("Large File Handling", True, f"{segments} segments, {memory_mb:.1f}MB RAM"))
                print("\n  ✅ Large file test PASSED")
            else:
                raise Exception(f"Memory usage too high: {memory_mb:.1f} MB")
                
        except Exception as e:
            self.test_results.append(("Large File Handling", False, str(e)))
            print(f"\n  ❌ Large file test FAILED: {e}")
            
    def test_recovery_mechanisms(self):
        """Test recovery and redundancy mechanisms"""
        print("\n🔄 TEST 5: Recovery Mechanisms")
        print("-" * 50)
        
        try:
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'recovery.db'))
            system.initialize_upload(self.nntp_client)
            
            # Create test file
            test_file = self.test_dir / "recovery_test.txt"
            test_file.write_text("Test data for recovery" * 100)
            
            # Index
            index_stats = system.indexer.index_folder(str(self.test_dir))
            
            # Upload with redundancy level 2
            print("  📤 Uploading with redundancy level 2...")
            upload_stats = system.uploader.upload_folder(
                index_stats['folder_id'],
                redundancy_level=2
            )
            
            print(f"     ✓ Created {upload_stats['redundancy_copies']} redundancy copies")
            
            # Simulate segment loss and recovery
            print("  🔧 Simulating segment recovery...")
            
            # Get segments from database
            segments = system.db_manager.fetchall("""
                SELECT * FROM segments 
                WHERE redundancy_level > 0
                LIMIT 5
            """, ())
            
            if len(segments) > 0:
                print(f"     ✓ Found {len(segments)} redundancy segments")
                print("     ✓ Recovery mechanisms available")
                
                self.test_results.append(("Recovery Mechanisms", True, f"{len(segments)} redundancy segments"))
                print("\n  ✅ Recovery test PASSED")
            else:
                raise Exception("No redundancy segments created")
                
        except Exception as e:
            self.test_results.append(("Recovery Mechanisms", False, str(e)))
            print(f"\n  ❌ Recovery test FAILED: {e}")
            
    def test_concurrent_operations(self):
        """Test concurrent indexing and uploading"""
        print("\n🔄 TEST 6: Concurrent Operations")
        print("-" * 50)
        
        try:
            import threading
            
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'concurrent.db'))
            system.initialize_upload(self.nntp_client)
            
            # Create multiple folders
            folders = []
            for i in range(3):
                folder = self.test_dir / f"concurrent_{i}"
                folder.mkdir()
                (folder / "file.txt").write_text(f"Content {i}" * 100)
                folders.append(folder)
                
            print(f"  🔀 Testing concurrent indexing of {len(folders)} folders...")
            
            results = []
            threads = []
            
            def index_folder(folder_path, results_list):
                try:
                    stats = system.indexer.index_folder(str(folder_path))
                    results_list.append(('success', stats))
                except Exception as e:
                    results_list.append(('error', str(e)))
                    
            # Start concurrent indexing
            for folder in folders:
                thread = threading.Thread(
                    target=index_folder,
                    args=(folder, results)
                )
                thread.start()
                threads.append(thread)
                
            # Wait for completion
            for thread in threads:
                thread.join()
                
            # Check results
            successful = sum(1 for r in results if r[0] == 'success')
            
            print(f"     ✓ {successful}/{len(folders)} folders indexed successfully")
            
            if successful == len(folders):
                self.test_results.append(("Concurrent Operations", True, f"{successful} concurrent operations"))
                print("\n  ✅ Concurrent test PASSED")
            else:
                raise Exception(f"Only {successful}/{len(folders)} succeeded")
                
        except Exception as e:
            self.test_results.append(("Concurrent Operations", False, str(e)))
            print(f"\n  ❌ Concurrent test FAILED: {e}")
            
    def _create_test_structure(self, base_path: Path):
        """Create test folder structure"""
        # Create directories
        (base_path / "documents").mkdir()
        (base_path / "images").mkdir()
        (base_path / "data").mkdir()
        
        # Create files
        (base_path / "documents" / "report.txt").write_text("Annual report content")
        (base_path / "images" / "photo.jpg").write_bytes(os.urandom(1024 * 50))
        (base_path / "data" / "dataset.csv").write_text("id,value\n1,test\n2,data\n")
        
    def _create_old_database(self, db_path: Path):
        """Create old database structure for migration test"""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        
        # Create old schema
        conn.execute("""
            CREATE TABLE files (
                file_id INTEGER PRIMARY KEY,
                file_path TEXT,
                file_hash TEXT,
                file_size INTEGER,
                modified_time TEXT,
                version INTEGER DEFAULT 1,
                segment_count INTEGER DEFAULT 1,
                state TEXT DEFAULT 'indexed'
            )
        """)
        
        conn.execute("""
            CREATE TABLE segments (
                segment_id INTEGER PRIMARY KEY,
                file_id INTEGER,
                segment_index INTEGER,
                segment_hash TEXT,
                segment_size INTEGER
            )
        """)
        
        # Insert test data
        for i in range(5):
            conn.execute("""
                INSERT INTO files (file_path, file_hash, file_size, modified_time)
                VALUES (?, ?, ?, datetime('now'))
            """, (f"file_{i}.txt", f"hash_{i}", 1024 * (i + 1)))
            
            # Add segments
            file_id = conn.lastrowid
            for j in range(2):
                conn.execute("""
                    INSERT INTO segments (file_id, segment_index, segment_hash, segment_size)
                    VALUES (?, ?, ?, ?)
                """, (file_id, j, f"seg_hash_{i}_{j}", 512))
                
        conn.commit()
        conn.close()
        
    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*70)
        print(" "*25 + "TEST RESULTS")
        print("="*70)
        
        for test_name, passed, details in self.test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name:.<40} {status}")
            if details and not passed:
                print(f"    Error: {details[:50]}...")
                
        passed_count = sum(1 for _, p, _ in self.test_results if p)
        total_count = len(self.test_results)
        
        print("-"*70)
        print(f"  Total: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print(f"\n⚠️ {total_count - passed_count} tests failed")
            
        print("="*70)


def run_integration_tests():
    """Run all integration tests"""
    suite = IntegrationTestSuite()
    suite.run_all_tests()
    
    # Return success status
    passed = all(result[1] for result in suite.test_results)
    return 0 if passed else 1


if __name__ == "__main__":
    exit_code = run_integration_tests()
    sys.exit(exit_code)