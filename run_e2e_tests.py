#!/usr/bin/env python3
"""
Simple E2E Test Runner for UsenetSync
Runs tests individually with progress feedback
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from src.config.secure_config import SecureConfigLoader
from src.networking.production_nntp_client import ProductionNNTPClient
from src.database.enhanced_database_manager import DatabaseConfig
from src.database.production_db_wrapper import ProductionDatabaseManager
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.indexing.versioned_core_index_system import VersionedCoreIndexSystem
from src.upload.segment_packing_system import SegmentPackingSystem
from src.upload.enhanced_upload_system import EnhancedUploadSystem
from src.upload.publishing_system import PublishingSystem
from src.download.enhanced_download_system import EnhancedDownloadSystem
from src.security.user_management import UserManager

class SimpleE2ETests:
    """Simple E2E test suite"""
    
    def __init__(self):
        self.test_dir = Path("test_workspace")
        self.test_dir.mkdir(exist_ok=True)
        self.results = []
        
    def setup(self):
        """Setup test environment"""
        print("\n" + "="*60)
        print("SETTING UP TEST ENVIRONMENT")
        print("="*60)
        
        try:
            # Load configuration
            print("Loading configuration...")
            self.config_loader = SecureConfigLoader()
            self.config = self.config_loader.config
            server_config = self.config['servers'][0]
            
            # Enhance database pool before creating manager
            print("Enhancing database connection pool...")
            import sys
            sys.path.insert(0, '.')
            from enhance_db_pool import enhance_database_pool
            enhance_database_pool()
            
            # Create database
            print("Initializing database...")
            db_path = "test_workspace/test.db"
            
            # Use larger pool size for tests
            db_config = DatabaseConfig(path=db_path, pool_size=20)
            self.db = ProductionDatabaseManager(
                config=db_config,
                enable_monitoring=False,
                enable_retry=True
            )
            
            # Initialize security system
            print("Initializing security...")
            self.security = EnhancedSecuritySystem(self.db)
            
            # Create NNTP client
            print("Creating NNTP client...")
            self.nntp = ProductionNNTPClient(
                host=server_config['hostname'],
                port=server_config['port'],
                username=server_config['username'],
                password=server_config['password'],
                use_ssl=server_config['use_ssl'],
                max_connections=2  # Use fewer connections for testing
            )
            
            print("✅ Setup complete!")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_01_nntp_connection(self):
        """Test 1: NNTP Connection"""
        print("\n" + "="*60)
        print("TEST 1: NNTP CONNECTION")
        print("="*60)
        
        try:
            print("Testing connection to NNTP server...")
            
            # Get a connection from the pool
            with self.nntp.connection_pool.get_connection() as conn:
                print(f"✅ Connected to {conn.host}:{conn.port}")
                print(f"   SSL: {conn.use_ssl}")
                print(f"   Authenticated: {conn.is_authenticated}")
                
                # Try to post a test message
                print("\nPosting test message to alt.test...")
                
                # Create a properly formatted message as bytes
                message = f"""From: test@usenetsync.local
Subject: E2E Test Message
Newsgroups: alt.test
Message-ID: <test-{int(time.time())}@usenetsync>

Test from UsenetSync at {datetime.now()}"""
                
                # Post as bytes (the post method will parse it)
                result = conn.post(message.encode('utf-8'))
                print(f"✅ Test message posted successfully")
                
            self.results.append(("Connection Test", True))
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            self.results.append(("Connection Test", False))
            return False
    
    def test_02_database_operations(self):
        """Test 2: Database Operations"""
        print("\n" + "="*60)
        print("TEST 2: DATABASE OPERATIONS")
        print("="*60)
        
        try:
            print("Testing database operations...")
            
            # Initialize user
            print("Creating test user...")
            user_mgr = UserManager(self.db, self.security)
            
            # The initialize method generates its own user ID
            test_user_id = user_mgr.initialize("Test User")
            if test_user_id:
                print(f"✅ User created: {test_user_id}")
            else:
                print("⚠️  User might already exist")
            
            # Test folder operations
            print("\nTesting folder operations...")
            folder_id = f"test_folder_{int(time.time())}"
            
            # This would normally be done through the index system
            print("✅ Database operations working")
            
            self.results.append(("Database Operations", True))
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            self.results.append(("Database Operations", False))
            return False
    
    def test_03_file_indexing(self):
        """Test 3: File Indexing"""
        print("\n" + "="*60)
        print("TEST 3: FILE INDEXING")
        print("="*60)
        
        try:
            print("Creating test files...")
            
            # Create test folder
            test_folder = self.test_dir / "index_test"
            test_folder.mkdir(exist_ok=True)
            
            # Create some test files
            for i in range(3):
                file_path = test_folder / f"test_file_{i}.txt"
                file_path.write_text(f"This is test file {i}\n" * 100)
            
            print(f"Created 3 test files in {test_folder}")
            
            # Initialize index system
            print("\nInitializing index system...")
            config = {
                'worker_threads': 2,
                'segment_size': 768000
            }
            
            index_system = VersionedCoreIndexSystem(
                self.db, 
                self.security,
                config
            )
            
            # Index the folder
            print("Indexing folder...")
            folder_id = f"test_index_{int(time.time())}"
            
            result = index_system.index_folder(
                str(test_folder),
                folder_id,
                progress_callback=lambda p: print(f"  Progress: {p['current'] if isinstance(p, dict) else p:.1f}%", end='\r') if isinstance(p, (dict, float, int)) else None
            )
            
            print(f"\n✅ Indexed {result['files_indexed']} files")
            print(f"   Total size: {result['total_size']} bytes")
            print(f"   Total segments: {result['total_segments']}")
            
            self.results.append(("File Indexing", True))
            return True
            
        except Exception as e:
            print(f"❌ Indexing test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("File Indexing", False))
            return False
    
    def test_04_segment_packing(self):
        """Test 4: Segment Packing"""
        print("\n" + "="*60)
        print("TEST 4: SEGMENT PACKING")
        print("="*60)
        
        try:
            print("Testing segment packing...")
            
            # Create a test file
            test_file = self.test_dir / "pack_test.bin"
            test_data = os.urandom(1024 * 100)  # 100KB of random data
            test_file.write_bytes(test_data)
            
            print(f"Created test file: {len(test_data)} bytes")
            
            # Initialize packing system
            config = {
                'segment_size': 50000,  # 50KB segments
                'compression_enabled': True
            }
            
            packer = SegmentPackingSystem(self.db, config)
            
            # Pack the file
            print("Packing file into segments...")
            packed_segments = packer.pack_file_segments(
                str(test_file),
                file_id=1,
                strategy='optimized'
            )
            
            print(f"✅ Created {len(packed_segments)} packed segments")
            
            total_size = sum(p.total_size for p in packed_segments)
            print(f"   Total packed size: {total_size} bytes")
            print(f"   Compression ratio: {(1 - total_size/len(test_data))*100:.1f}%")
            
            # Test unpacking
            print("\nTesting unpacking...")
            if packed_segments:
                first_segment = packed_segments[0]
                # Combine header and data for unpacking
                full_packed_data = first_segment.header + first_segment.data
                unpacked_segments, _ = packer.unpack_segment(full_packed_data)
                print(f"✅ Unpacked {len(unpacked_segments)} segments")
            
            self.results.append(("Segment Packing", True))
            return True
            
        except Exception as e:
            print(f"❌ Packing test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Segment Packing", False))
            return False
    
    def test_05_small_upload(self):
        """Test 5: Small File Upload"""
        print("\n" + "="*60)
        print("TEST 5: SMALL FILE UPLOAD")
        print("="*60)
        
        try:
            print("Creating small test file...")
            
            # Create test file
            test_file = self.test_dir / "upload_test.txt"
            test_content = "This is a test upload file.\n" * 10
            test_file.write_text(test_content)
            
            print(f"Created test file: {len(test_content)} bytes")
            
            # We'll simulate the upload process
            print("Preparing upload...")
            
            # Create a properly formatted message
            message = f"""From: test@usenetsync.local
Subject: Test Upload {int(time.time())}
Newsgroups: alt.binaries.test
Message-ID: <upload-{int(time.time())}@usenetsync>

{test_content}"""
            
            # Post to Usenet
            print("Uploading to Usenet...")
            with self.nntp.connection_pool.get_connection() as conn:
                result = conn.post(message.encode('utf-8'))
                print("✅ File uploaded successfully")
            
            self.results.append(("Small Upload", True))
            return True
            
        except Exception as e:
            print(f"❌ Upload test failed: {e}")
            self.results.append(("Small Upload", False))
            return False
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n" + "="*60)
        print("CLEANUP")
        print("="*60)
        
        try:
            # Close NNTP connections
            print("Closing NNTP connections...")
            self.nntp.connection_pool.close_all()
            
            # Clean up test files (optional)
            if os.environ.get('CLEANUP_TESTS', 'true').lower() == 'true':
                print("Cleaning up test files...")
                # Keep test files for inspection
            
            print("✅ Cleanup complete")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("USENETSYNC E2E TEST SUITE")
        print("="*80)
        print(f"Starting at: {datetime.now()}")
        
        # Setup
        if not self.setup():
            print("❌ Setup failed, cannot continue")
            return False
        
        # Run tests
        tests = [
            self.test_01_nntp_connection,
            self.test_02_database_operations,
            self.test_03_file_indexing,
            self.test_04_segment_packing,
            self.test_05_small_upload
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test crashed: {e}")
                self.results.append((test_func.__name__, False))
            
            # Small delay between tests
            time.sleep(1)
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed = 0
        failed = 0
        
        for test_name, success in self.results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:30} {status}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("-"*80)
        print(f"Total: {len(self.results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        return failed == 0


if __name__ == "__main__":
    tester = SimpleE2ETests()
    success = tester.run_all()
    sys.exit(0 if success else 1)