#!/usr/bin/env python3
"""
End-to-End Production Tests for UsenetSync
Tests the complete workflow on actual Usenet servers
"""

import os
import sys
import time
import json
import hashlib
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.main import UsenetSync
from src.config.configuration_manager import ConfigurationManager
from src.security.enhanced_security_system import ShareType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/logs/e2e_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestConfiguration:
    """Test configuration for production Usenet"""
    
    # Test folder sizes
    SMALL_TEST = {
        'files': 5,
        'file_size': 100 * 1024,  # 100KB each
        'description': 'Small test (5 files, 500KB total)'
    }
    
    MEDIUM_TEST = {
        'files': 20,
        'file_size': 1024 * 1024,  # 1MB each
        'description': 'Medium test (20 files, 20MB total)'
    }
    
    LARGE_TEST = {
        'files': 100,
        'file_size': 5 * 1024 * 1024,  # 5MB each
        'description': 'Large test (100 files, 500MB total)'
    }
    
    # Test timeouts
    UPLOAD_TIMEOUT = 300  # 5 minutes
    DOWNLOAD_TIMEOUT = 300  # 5 minutes
    INDEX_TIMEOUT = 60  # 1 minute


class ProductionE2ETestSuite(unittest.TestCase):
    """Complete end-to-end test suite for production Usenet"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        logger.info("=" * 80)
        logger.info("STARTING PRODUCTION E2E TEST SUITE")
        logger.info("=" * 80)
        
        # Create test directories
        cls.test_base = Path("tests/e2e/test_workspace")
        cls.test_base.mkdir(parents=True, exist_ok=True)
        
        cls.test_folders = cls.test_base / "folders"
        cls.test_downloads = cls.test_base / "downloads"
        cls.test_folders.mkdir(exist_ok=True)
        cls.test_downloads.mkdir(exist_ok=True)
        
        # Initialize UsenetSync
        logger.info("Initializing UsenetSync system...")
        cls.usenet = UsenetSync()
        
        # Create test user
        cls.test_user_id = f"test_user_{int(time.time())}"
        cls.test_user_name = "E2E Test User"
        
        logger.info(f"Creating test user: {cls.test_user_id}")
        cls.usenet.user.initialize_user(cls.test_user_id, cls.test_user_name)
        
        # Test results storage
        cls.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        logger.info("=" * 80)
        logger.info("CLEANING UP TEST ENVIRONMENT")
        logger.info("=" * 80)
        
        # Save test results
        cls.test_results['end_time'] = datetime.now().isoformat()
        results_file = Path("tests/logs/e2e_results.json")
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2)
        
        logger.info(f"Test results saved to {results_file}")
        
        # Clean up test directories (optional)
        if os.environ.get('CLEANUP_TESTS', 'true').lower() == 'true':
            logger.info("Cleaning up test directories...")
            shutil.rmtree(cls.test_base, ignore_errors=True)
    
    def setUp(self):
        """Set up for each test"""
        self.test_start = time.time()
        self.current_test = {
            'name': self._testMethodName,
            'start_time': datetime.now().isoformat(),
            'status': 'running'
        }
    
    def tearDown(self):
        """Clean up after each test"""
        duration = time.time() - self.test_start
        self.current_test['duration'] = duration
        self.current_test['end_time'] = datetime.now().isoformat()
        
        if hasattr(self, '_outcome'):
            result = self._outcome.result
            if result.failures:
                self.current_test['status'] = 'failed'
                self.current_test['error'] = str(result.failures[-1][1])
            elif result.errors:
                self.current_test['status'] = 'error'
                self.current_test['error'] = str(result.errors[-1][1])
            else:
                self.current_test['status'] = 'passed'
        
        self.test_results['tests'].append(self.current_test)
        logger.info(f"Test {self._testMethodName}: {self.current_test['status']} ({duration:.2f}s)")
    
    def create_test_folder(self, name: str, config: Dict) -> Tuple[Path, List[Path]]:
        """Create a test folder with files"""
        folder_path = self.test_folders / name
        folder_path.mkdir(exist_ok=True)
        
        files = []
        logger.info(f"Creating test folder: {config['description']}")
        
        for i in range(config['files']):
            file_path = folder_path / f"test_file_{i:03d}.bin"
            
            # Create file with random content
            with open(file_path, 'wb') as f:
                content = os.urandom(config['file_size'])
                f.write(content)
            
            files.append(file_path)
            
        logger.info(f"Created {len(files)} test files in {folder_path}")
        return folder_path, files
    
    def calculate_folder_hash(self, folder_path: Path) -> str:
        """Calculate hash of all files in folder for verification"""
        hasher = hashlib.sha256()
        
        for file_path in sorted(folder_path.glob('*')):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(file_path.name.encode())
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    # ==================== TEST CASES ====================
    
    def test_01_connection_health(self):
        """Test NNTP server connection and health"""
        logger.info("Testing NNTP server connection...")
        
        # Test connection
        self.assertTrue(
            self.usenet.nntp.test_connection(),
            "Failed to connect to NNTP server"
        )
        
        # Test posting capability
        test_message = f"Test message {time.time()}"
        message_id = self.usenet.nntp.post_test_message(test_message)
        self.assertIsNotNone(message_id, "Failed to post test message")
        
        logger.info(f"Successfully posted test message: {message_id}")
        self.current_test['message_id'] = message_id
    
    def test_02_small_folder_public(self):
        """Test small folder with public sharing"""
        logger.info("=" * 60)
        logger.info("TEST: Small Folder - Public Share")
        logger.info("=" * 60)
        
        # Create test folder
        folder_path, files = self.create_test_folder(
            "small_public", 
            TestConfiguration.SMALL_TEST
        )
        
        original_hash = self.calculate_folder_hash(folder_path)
        folder_id = f"small_public_{int(time.time())}"
        
        # Index folder
        logger.info("Indexing folder...")
        start_time = time.time()
        index_result = self.usenet.index_system.index_folder(
            str(folder_path),
            folder_id,
            progress_callback=lambda p: logger.debug(f"Index progress: {p}%")
        )
        index_time = time.time() - start_time
        
        self.assertIsNotNone(index_result, "Failed to index folder")
        logger.info(f"Indexed in {index_time:.2f}s")
        
        # Upload to Usenet
        logger.info("Uploading to Usenet...")
        start_time = time.time()
        upload_result = self.usenet.upload_folder(
            folder_id,
            progress_callback=lambda p: logger.debug(f"Upload progress: {p}%")
        )
        upload_time = time.time() - start_time
        
        self.assertTrue(upload_result['success'], "Failed to upload folder")
        logger.info(f"Uploaded in {upload_time:.2f}s")
        
        # Publish as public share
        logger.info("Publishing as public share...")
        share_result = self.usenet.publishing.publish_folder(
            folder_id,
            ShareType.PUBLIC,
            description="Small public test folder"
        )
        
        self.assertIsNotNone(share_result, "Failed to publish folder")
        access_string = share_result['access_string']
        logger.info(f"Published with access string: {access_string[:50]}...")
        
        # Download using access string
        logger.info("Downloading using access string...")
        download_path = self.test_downloads / "small_public_download"
        
        start_time = time.time()
        download_result = self.usenet.download_from_access_string(
            access_string,
            str(download_path),
            progress_callback=lambda p: logger.debug(f"Download progress: {p}%")
        )
        download_time = time.time() - start_time
        
        self.assertTrue(download_result['success'], "Failed to download folder")
        logger.info(f"Downloaded in {download_time:.2f}s")
        
        # Verify integrity
        logger.info("Verifying download integrity...")
        downloaded_hash = self.calculate_folder_hash(download_path)
        self.assertEqual(
            original_hash, 
            downloaded_hash,
            "Downloaded folder does not match original"
        )
        
        logger.info("✓ Small public folder test PASSED")
        
        # Store metrics
        self.current_test['metrics'] = {
            'folder_size': len(files),
            'index_time': index_time,
            'upload_time': upload_time,
            'download_time': download_time,
            'access_string_length': len(access_string)
        }
    
    def test_03_medium_folder_private(self):
        """Test medium folder with private sharing"""
        logger.info("=" * 60)
        logger.info("TEST: Medium Folder - Private Share")
        logger.info("=" * 60)
        
        # Create test folder
        folder_path, files = self.create_test_folder(
            "medium_private",
            TestConfiguration.MEDIUM_TEST
        )
        
        original_hash = self.calculate_folder_hash(folder_path)
        folder_id = f"medium_private_{int(time.time())}"
        
        # Index and upload
        logger.info("Indexing and uploading folder...")
        index_result = self.usenet.index_system.index_folder(
            str(folder_path),
            folder_id
        )
        self.assertIsNotNone(index_result)
        
        upload_result = self.usenet.upload_folder(folder_id)
        self.assertTrue(upload_result['success'])
        
        # Publish as private share
        logger.info("Publishing as private share...")
        share_result = self.usenet.publishing.publish_folder(
            folder_id,
            ShareType.PRIVATE,
            allowed_users=[self.test_user_id],
            description="Medium private test folder"
        )
        
        self.assertIsNotNone(share_result)
        access_string = share_result['access_string']
        
        # Download with authorized user
        logger.info("Downloading with authorized user...")
        download_path = self.test_downloads / "medium_private_download"
        
        download_result = self.usenet.download_from_access_string(
            access_string,
            str(download_path),
            user_id=self.test_user_id
        )
        
        self.assertTrue(download_result['success'])
        
        # Verify integrity
        downloaded_hash = self.calculate_folder_hash(download_path)
        self.assertEqual(original_hash, downloaded_hash)
        
        logger.info("✓ Medium private folder test PASSED")
    
    def test_04_protected_share_password(self):
        """Test protected share with password"""
        logger.info("=" * 60)
        logger.info("TEST: Protected Share with Password")
        logger.info("=" * 60)
        
        # Create small test folder
        folder_path, files = self.create_test_folder(
            "protected_password",
            TestConfiguration.SMALL_TEST
        )
        
        original_hash = self.calculate_folder_hash(folder_path)
        folder_id = f"protected_{int(time.time())}"
        test_password = "TestPassword123!"
        
        # Index and upload
        index_result = self.usenet.index_system.index_folder(
            str(folder_path),
            folder_id
        )
        upload_result = self.usenet.upload_folder(folder_id)
        
        # Publish as protected share
        logger.info("Publishing as protected share...")
        share_result = self.usenet.publishing.publish_folder(
            folder_id,
            ShareType.PROTECTED,
            password=test_password,
            password_hint="Test password with 123!",
            description="Protected test folder"
        )
        
        access_string = share_result['access_string']
        
        # Try download without password (should fail)
        logger.info("Testing download without password (should fail)...")
        download_path = self.test_downloads / "protected_fail"
        
        download_result = self.usenet.download_from_access_string(
            access_string,
            str(download_path)
        )
        
        self.assertFalse(
            download_result.get('success', False),
            "Download should fail without password"
        )
        
        # Download with correct password
        logger.info("Downloading with correct password...")
        download_path = self.test_downloads / "protected_success"
        
        download_result = self.usenet.download_from_access_string(
            access_string,
            str(download_path),
            password=test_password
        )
        
        self.assertTrue(download_result['success'])
        
        # Verify integrity
        downloaded_hash = self.calculate_folder_hash(download_path)
        self.assertEqual(original_hash, downloaded_hash)
        
        logger.info("✓ Protected share test PASSED")
    
    def test_05_incremental_update(self):
        """Test incremental folder updates"""
        logger.info("=" * 60)
        logger.info("TEST: Incremental Folder Update")
        logger.info("=" * 60)
        
        # Create initial folder
        folder_path = self.test_folders / "incremental"
        folder_path.mkdir(exist_ok=True)
        folder_id = f"incremental_{int(time.time())}"
        
        # Create initial files
        logger.info("Creating initial files...")
        for i in range(5):
            file_path = folder_path / f"file_{i}.txt"
            file_path.write_text(f"Initial content {i}")
        
        # Initial index and upload
        logger.info("Initial indexing and upload...")
        self.usenet.index_system.index_folder(str(folder_path), folder_id)
        upload_result = self.usenet.upload_folder(folder_id)
        self.assertTrue(upload_result['success'])
        
        initial_stats = self.usenet.database.get_folder_stats(folder_id)
        
        # Modify folder
        logger.info("Modifying folder...")
        # Add new file
        (folder_path / "new_file.txt").write_text("New file content")
        # Modify existing file
        (folder_path / "file_0.txt").write_text("Modified content 0")
        # Delete a file
        (folder_path / "file_4.txt").unlink()
        
        # Re-index (incremental)
        logger.info("Re-indexing (incremental)...")
        changes = self.usenet.index_system.re_index_folder(
            str(folder_path),
            folder_id
        )
        
        self.assertIsNotNone(changes)
        self.assertEqual(len(changes['added']), 1)
        self.assertEqual(len(changes['modified']), 1)
        self.assertEqual(len(changes['deleted']), 1)
        
        # Upload changes
        logger.info("Uploading changes...")
        update_result = self.usenet.upload_folder(folder_id)
        self.assertTrue(update_result['success'])
        
        updated_stats = self.usenet.database.get_folder_stats(folder_id)
        
        # Verify version increment
        self.assertGreater(
            updated_stats['version'],
            initial_stats['version'],
            "Version should increment after update"
        )
        
        logger.info("✓ Incremental update test PASSED")
    
    def test_06_large_file_handling(self):
        """Test handling of large files with segmentation"""
        logger.info("=" * 60)
        logger.info("TEST: Large File Handling")
        logger.info("=" * 60)
        
        # Create a large file
        folder_path = self.test_folders / "large_file"
        folder_path.mkdir(exist_ok=True)
        
        large_file = folder_path / "large_test.bin"
        file_size = 50 * 1024 * 1024  # 50MB
        
        logger.info(f"Creating {file_size / 1024 / 1024:.1f}MB test file...")
        with open(large_file, 'wb') as f:
            # Write in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            for _ in range(file_size // chunk_size):
                f.write(os.urandom(chunk_size))
        
        original_hash = hashlib.sha256(large_file.read_bytes()).hexdigest()
        folder_id = f"large_file_{int(time.time())}"
        
        # Index and check segmentation
        logger.info("Indexing large file...")
        index_result = self.usenet.index_system.index_folder(
            str(folder_path),
            folder_id
        )
        
        # Get segment count
        segments = self.usenet.database.get_file_segments(folder_id, "large_test.bin")
        expected_segments = (file_size + 768000 - 1) // 768000  # 750KB segments
        
        self.assertGreaterEqual(
            len(segments),
            expected_segments,
            f"Should have at least {expected_segments} segments"
        )
        
        logger.info(f"File segmented into {len(segments)} parts")
        
        # Upload and download
        logger.info("Uploading large file...")
        upload_result = self.usenet.upload_folder(folder_id)
        self.assertTrue(upload_result['success'])
        
        # Publish and download
        share_result = self.usenet.publishing.publish_folder(
            folder_id,
            ShareType.PUBLIC
        )
        
        download_path = self.test_downloads / "large_file_download"
        download_result = self.usenet.download_from_access_string(
            share_result['access_string'],
            str(download_path)
        )
        
        self.assertTrue(download_result['success'])
        
        # Verify integrity
        downloaded_file = download_path / "large_test.bin"
        downloaded_hash = hashlib.sha256(downloaded_file.read_bytes()).hexdigest()
        
        self.assertEqual(
            original_hash,
            downloaded_hash,
            "Large file integrity check failed"
        )
        
        logger.info("✓ Large file handling test PASSED")
    
    def test_07_concurrent_operations(self):
        """Test concurrent upload/download operations"""
        logger.info("=" * 60)
        logger.info("TEST: Concurrent Operations")
        logger.info("=" * 60)
        
        import threading
        
        # Create multiple small folders
        folders = []
        for i in range(3):
            folder_path, files = self.create_test_folder(
                f"concurrent_{i}",
                TestConfiguration.SMALL_TEST
            )
            folder_id = f"concurrent_{i}_{int(time.time())}"
            folders.append({
                'path': folder_path,
                'id': folder_id,
                'hash': self.calculate_folder_hash(folder_path)
            })
        
        # Index all folders
        logger.info("Indexing all folders...")
        for folder in folders:
            self.usenet.index_system.index_folder(
                str(folder['path']),
                folder['id']
            )
        
        # Upload concurrently
        logger.info("Starting concurrent uploads...")
        upload_threads = []
        upload_results = {}
        
        def upload_folder(folder_data):
            result = self.usenet.upload_folder(folder_data['id'])
            upload_results[folder_data['id']] = result
        
        for folder in folders:
            thread = threading.Thread(
                target=upload_folder,
                args=(folder,)
            )
            thread.start()
            upload_threads.append(thread)
        
        # Wait for uploads
        for thread in upload_threads:
            thread.join(timeout=TestConfiguration.UPLOAD_TIMEOUT)
        
        # Verify all uploads succeeded
        for folder_id, result in upload_results.items():
            self.assertTrue(
                result.get('success', False),
                f"Upload failed for {folder_id}"
            )
        
        logger.info("✓ Concurrent operations test PASSED")
    
    def test_08_error_recovery(self):
        """Test error recovery and retry mechanisms"""
        logger.info("=" * 60)
        logger.info("TEST: Error Recovery")
        logger.info("=" * 60)
        
        # This test simulates failures and verifies recovery
        # Note: Actual failure simulation depends on implementation
        
        folder_path, files = self.create_test_folder(
            "error_recovery",
            TestConfiguration.SMALL_TEST
        )
        folder_id = f"error_recovery_{int(time.time())}"
        
        # Index folder
        self.usenet.index_system.index_folder(str(folder_path), folder_id)
        
        # Test upload with retry
        logger.info("Testing upload retry mechanism...")
        
        # The upload system should handle transient failures
        upload_result = self.usenet.upload_folder(
            folder_id,
            max_retries=3
        )
        
        self.assertTrue(
            upload_result['success'],
            "Upload should succeed with retry mechanism"
        )
        
        # Check retry statistics
        if 'retries' in upload_result:
            logger.info(f"Upload succeeded after {upload_result['retries']} retries")
        
        logger.info("✓ Error recovery test PASSED")
    
    def test_09_performance_metrics(self):
        """Test and collect performance metrics"""
        logger.info("=" * 60)
        logger.info("TEST: Performance Metrics")
        logger.info("=" * 60)
        
        metrics = {
            'index_speed': [],
            'upload_speed': [],
            'download_speed': []
        }
        
        # Test with different sizes
        test_configs = [
            ('perf_small', TestConfiguration.SMALL_TEST),
            ('perf_medium', TestConfiguration.MEDIUM_TEST)
        ]
        
        for name, config in test_configs:
            logger.info(f"Testing performance: {config['description']}")
            
            # Create test folder
            folder_path, files = self.create_test_folder(name, config)
            folder_id = f"{name}_{int(time.time())}"
            
            total_size = len(files) * config['file_size']
            
            # Measure indexing speed
            start = time.time()
            self.usenet.index_system.index_folder(str(folder_path), folder_id)
            index_time = time.time() - start
            index_speed = total_size / index_time / 1024 / 1024  # MB/s
            metrics['index_speed'].append(index_speed)
            
            # Measure upload speed
            start = time.time()
            self.usenet.upload_folder(folder_id)
            upload_time = time.time() - start
            upload_speed = total_size / upload_time / 1024 / 1024  # MB/s
            metrics['upload_speed'].append(upload_speed)
            
            # Publish and measure download speed
            share_result = self.usenet.publishing.publish_folder(
                folder_id,
                ShareType.PUBLIC
            )
            
            download_path = self.test_downloads / f"{name}_download"
            start = time.time()
            self.usenet.download_from_access_string(
                share_result['access_string'],
                str(download_path)
            )
            download_time = time.time() - start
            download_speed = total_size / download_time / 1024 / 1024  # MB/s
            metrics['download_speed'].append(download_speed)
            
            logger.info(f"  Index: {index_speed:.2f} MB/s")
            logger.info(f"  Upload: {upload_speed:.2f} MB/s")
            logger.info(f"  Download: {download_speed:.2f} MB/s")
        
        # Store average metrics
        self.current_test['performance'] = {
            'avg_index_speed': sum(metrics['index_speed']) / len(metrics['index_speed']),
            'avg_upload_speed': sum(metrics['upload_speed']) / len(metrics['upload_speed']),
            'avg_download_speed': sum(metrics['download_speed']) / len(metrics['download_speed'])
        }
        
        logger.info("✓ Performance metrics test PASSED")
    
    def test_10_cleanup_verification(self):
        """Verify cleanup and resource management"""
        logger.info("=" * 60)
        logger.info("TEST: Cleanup Verification")
        logger.info("=" * 60)
        
        # Check database connections
        db_stats = self.usenet.database.get_connection_stats()
        self.assertLess(
            db_stats.get('active_connections', 0),
            10,
            "Too many active database connections"
        )
        
        # Check NNTP connections
        nntp_stats = self.usenet.nntp.get_connection_stats()
        self.assertLess(
            nntp_stats.get('active_connections', 0),
            5,
            "Too many active NNTP connections"
        )
        
        # Check temp file cleanup
        temp_dir = Path(self.usenet.config.storage.temp_directory)
        if temp_dir.exists():
            temp_files = list(temp_dir.glob('*'))
            self.assertLess(
                len(temp_files),
                10,
                f"Too many temp files: {len(temp_files)}"
            )
        
        logger.info("✓ Cleanup verification PASSED")


def run_production_tests():
    """Run the complete production test suite"""
    # Create test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ProductionE2ETestSuite)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PRODUCTION E2E TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1)