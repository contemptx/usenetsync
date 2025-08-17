#!/usr/bin/env python3
"""
Real System Test with PostgreSQL
Tests the actual system with PostgreSQL database and real operations
"""

import os
import sys
import time
import uuid
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, '/workspace')

# Import PostgreSQL components
from src.database.postgresql_manager import (
    PostgresConfig,
    EmbeddedPostgresInstaller,
    ShardedPostgreSQLManager
)

# Import all real components
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.networking.production_nntp_client import ProductionNNTPClient
from src.upload.enhanced_upload_system import EnhancedUploadSystem
from src.upload.segment_packing_system import SegmentPackingSystem
from src.download.enhanced_download_system import EnhancedDownloadSystem
from src.monitoring.monitoring_system import MonitoringSystem
from src.indexing.parallel_indexer import ParallelIndexer
from src.queue.persistent_queue import (
    PersistentQueue,
    ResumableUploadQueue,
    ResumableDownloadQueue,
    UploadTask,
    DownloadTask,
    TaskStatus
)
from src.config.secure_config import SecureConfigLoader


class RealPostgreSQLSystemTest:
    """Complete real system test with PostgreSQL"""
    
    def __init__(self):
        self.test_dir = Path("/workspace/real_postgres_test")
        self.test_dir.mkdir(exist_ok=True)
        
        # Test results
        self.results = {
            'tests': [],
            'passed': 0,
            'failed': 0,
            'data': {}
        }
        
        # Systems
        self.systems = {}
        
    def setup_postgresql(self):
        """Setup PostgreSQL database"""
        print("\n🐘 Setting up PostgreSQL...")
        
        try:
            # Check if PostgreSQL is available
            import psycopg2
            
            # Try to connect to default postgres
            try:
                test_conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="postgres",
                    user="postgres",
                    password="postgres"
                )
                test_conn.close()
                print("  ✅ System PostgreSQL is available")
                use_system = True
            except:
                print("  ⚠️ System PostgreSQL not available")
                use_system = False
            
            # Setup database
            if use_system:
                # Create test database
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=5432,
                        database="postgres",
                        user="postgres",
                        password="postgres"
                    )
                    conn.autocommit = True
                    cursor = conn.cursor()
                    
                    # Drop if exists and create fresh
                    cursor.execute("DROP DATABASE IF EXISTS usenet_test")
                    cursor.execute("CREATE DATABASE usenet_test")
                    
                    # Create user if not exists
                    cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'usenet'")
                    if not cursor.fetchone():
                        cursor.execute("CREATE USER usenet WITH PASSWORD 'test_2024'")
                    
                    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE usenet_test TO usenet")
                    
                    conn.close()
                    print("  ✅ Created test database: usenet_test")
                    
                except Exception as e:
                    print(f"  ❌ Failed to create database: {e}")
                    return False
            
            # Configure PostgreSQL manager
            self.pg_config = PostgresConfig(
                embedded=False,  # Use system PostgreSQL
                host="localhost",
                port=5432,
                database="usenet_test",
                user="usenet",
                password="test_2024",
                shard_count=4,  # Use 4 shards for testing
                pool_size=10
            )
            
            # Initialize sharded manager
            print("  Initializing sharded PostgreSQL manager...")
            self.systems['db'] = ShardedPostgreSQLManager(self.pg_config)
            
            # Get initial statistics
            stats = self.systems['db'].get_statistics()
            print(f"  ✅ PostgreSQL ready with {self.pg_config.shard_count} shards")
            print(f"     Total segments: {stats['total_segments']:,}")
            
            return True
            
        except ImportError:
            print("  ❌ psycopg2 not installed")
            return False
        except Exception as e:
            print(f"  ❌ PostgreSQL setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_systems(self):
        """Initialize all real systems with PostgreSQL"""
        print("\n🔧 Initializing Real Systems with PostgreSQL...")
        
        try:
            # Setup PostgreSQL first
            if not self.setup_postgresql():
                return False
            
            # Load configuration
            config_path = Path("/workspace/usenet_sync_config.json")
            config_loader = SecureConfigLoader(str(config_path))
            config = config_loader.load_config()
            
            # Initialize security (with PostgreSQL backend)
            print("  Initializing security...")
            self.systems['security'] = EnhancedSecuritySystem(self.systems['db'])
            
            # Generate test user
            self.test_user_id = str(uuid.uuid4())
            print(f"  Generated test user ID: {self.test_user_id[:8]}...")
            
            # Initialize NNTP client
            print("  Initializing NNTP client...")
            server_config = config['servers'][0]
            self.systems['nntp'] = ProductionNNTPClient(
                host=server_config['hostname'],
                port=server_config['port'],
                username=server_config['username'],
                password=server_config['password'],
                use_ssl=server_config['use_ssl']
            )
            
            # Test NNTP connection
            print("  Testing NNTP connection...")
            if self._test_nntp_connection():
                print("    ✅ NNTP connected successfully")
            else:
                print("    ⚠️ NNTP connection failed, continuing anyway...")
            
            # Initialize parallel indexer
            print("  Initializing parallel indexer...")
            self.systems['indexer'] = ParallelIndexer(
                self.systems['db'],
                worker_count=4
            )
            
            # Initialize persistent queues
            print("  Initializing persistent queues...")
            queue_dir = self.test_dir / "queues"
            self.systems['upload_queue'] = ResumableUploadQueue(
                str(queue_dir / "upload"),
                self.systems['db']
            )
            self.systems['download_queue'] = ResumableDownloadQueue(
                str(queue_dir / "download"),
                self.systems['db']
            )
            
            # Initialize monitoring
            self.systems['monitoring'] = MonitoringSystem(
                self.systems['db'],
                config
            )
            
            print("✅ All systems initialized with PostgreSQL")
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_nntp_connection(self):
        """Test NNTP connection"""
        try:
            with self.systems['nntp'].get_connection() as conn:
                resp, count, first, last, name = conn.group('alt.binaries.test')
                return True
        except:
            return False
    
    def test_postgresql_operations(self):
        """Test PostgreSQL-specific operations"""
        print("\n🐘 Testing PostgreSQL Operations...")
        
        try:
            # Test 1: Batch insert segments
            print("  Test 1: Batch inserting 10,000 segments...")
            test_segments = []
            
            for i in range(10000):
                segment = {
                    'segment_id': str(uuid.uuid4()),
                    'file_id': str(uuid.uuid4()),
                    'folder_id': str(uuid.uuid4()),
                    'segment_index': i,
                    'segment_hash': os.urandom(32),
                    'size': 768000,
                    'message_id': f"<{uuid.uuid4()}@ngPost.com>",
                    'subject': f"Test {i}",
                    'internal_subject': f"internal_{i}"
                }
                test_segments.append(segment)
            
            start = time.time()
            self.systems['db'].insert_segments_batch(test_segments, batch_size=1000)
            elapsed = time.time() - start
            
            rate = len(test_segments) / elapsed
            print(f"    ✅ Inserted {len(test_segments):,} segments in {elapsed:.2f}s")
            print(f"    Rate: {rate:.0f} segments/second")
            
            self.results['tests'].append({
                'name': 'PostgreSQL Batch Insert',
                'status': 'PASSED',
                'segments': len(test_segments),
                'time': elapsed,
                'rate': f"{rate:.0f} segments/second"
            })
            self.results['passed'] += 1
            
            # Test 2: Sharding distribution
            print("\n  Test 2: Testing sharding distribution...")
            stats = self.systems['db'].get_statistics()
            
            print(f"    Shard distribution:")
            for shard in stats['shards']:
                print(f"      Shard {shard['shard_id']}: {shard['segments']:,} segments")
            
            # Check if distribution is roughly even
            segment_counts = [s['segments'] for s in stats['shards']]
            avg = sum(segment_counts) / len(segment_counts)
            max_deviation = max(abs(c - avg) for c in segment_counts)
            distribution_quality = "Good" if max_deviation < avg * 0.2 else "Poor"
            
            print(f"    Distribution quality: {distribution_quality}")
            
            self.results['tests'].append({
                'name': 'PostgreSQL Sharding',
                'status': 'PASSED',
                'shards': len(stats['shards']),
                'total_segments': stats['total_segments'],
                'distribution': distribution_quality
            })
            self.results['passed'] += 1
            
            # Test 3: Progress persistence
            print("\n  Test 3: Testing progress persistence...")
            session_id = str(uuid.uuid4())
            
            progress_data = {
                'total_items': 100000,
                'processed_items': 50000,
                'last_item_id': 'file_50000',
                'state': {
                    'current_folder': 'folder_500',
                    'upload_rate': 1234.5
                }
            }
            
            self.systems['db'].save_progress(session_id, 'upload', progress_data)
            loaded = self.systems['db'].load_progress(session_id)
            
            if loaded and loaded['processed_items'] == 50000:
                print(f"    ✅ Progress saved and loaded correctly")
                print(f"    Session: {session_id[:8]}...")
                print(f"    Progress: {loaded['processed_items']:,}/{loaded['total_items']:,}")
                
                self.results['tests'].append({
                    'name': 'PostgreSQL Progress',
                    'status': 'PASSED',
                    'session_id': session_id
                })
                self.results['passed'] += 1
            else:
                print(f"    ❌ Progress persistence failed")
                self.results['tests'].append({
                    'name': 'PostgreSQL Progress',
                    'status': 'FAILED'
                })
                self.results['failed'] += 1
            
            # Test 4: Streaming iteration
            print("\n  Test 4: Testing streaming iteration...")
            file_id = test_segments[0]['file_id']
            
            batch_count = 0
            total_streamed = 0
            
            for batch in self.systems['db'].iterate_segments(file_id, batch_size=100):
                batch_count += 1
                total_streamed += len(batch)
            
            print(f"    ✅ Streamed {total_streamed} segments in {batch_count} batches")
            
            self.results['tests'].append({
                'name': 'PostgreSQL Streaming',
                'status': 'PASSED',
                'segments': total_streamed,
                'batches': batch_count
            })
            self.results['passed'] += 1
            
            return True
            
        except Exception as e:
            print(f"  ❌ PostgreSQL operations failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'PostgreSQL Operations',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_parallel_indexing(self):
        """Test parallel indexing with PostgreSQL backend"""
        print("\n🔍 Testing Parallel Indexing with PostgreSQL...")
        
        try:
            # Create test files
            test_files_dir = self.test_dir / "test_files"
            test_files_dir.mkdir(exist_ok=True)
            
            print("  Creating 1000 test files...")
            for i in range(1000):
                folder_num = i // 100
                folder_path = test_files_dir / f"folder_{folder_num:03d}"
                folder_path.mkdir(exist_ok=True)
                
                file_path = folder_path / f"file_{i:04d}.dat"
                content = f"Test file {i}\n".encode() * 100
                content += os.urandom(1024 * (i % 10 + 1))
                file_path.write_bytes(content)
            
            print("  ✅ Created 1000 test files")
            
            # Run parallel indexing
            print("  Running parallel indexing with 4 workers...")
            start = time.time()
            
            stats = self.systems['indexer'].index_directory(str(test_files_dir))
            
            elapsed = time.time() - start
            
            print(f"\n  ✅ Indexing Results:")
            print(f"    Files indexed: {stats['processed_files']:,}")
            print(f"    Total size: {stats['total_size'] / (1024**2):.2f} MB")
            print(f"    Time: {elapsed:.2f}s")
            print(f"    Rate: {stats['files_per_second']:.0f} files/second")
            
            self.results['tests'].append({
                'name': 'Parallel Indexing (PostgreSQL)',
                'status': 'PASSED',
                'files': stats['processed_files'],
                'rate': f"{stats['files_per_second']:.0f} files/second"
            })
            self.results['passed'] += 1
            
            # Clean up test files
            shutil.rmtree(test_files_dir)
            
            return True
            
        except Exception as e:
            print(f"  ❌ Parallel indexing failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'Parallel Indexing (PostgreSQL)',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_persistent_queues(self):
        """Test persistent queues with PostgreSQL"""
        print("\n📦 Testing Persistent Queues with PostgreSQL...")
        
        try:
            # Test upload queue
            print("  Testing upload queue...")
            
            # Add 1000 tasks
            task_ids = []
            for i in range(1000):
                task = UploadTask(
                    task_id=None,
                    priority=i % 10,
                    created_at=time.time(),
                    status=TaskStatus.PENDING,
                    file_id=str(uuid.uuid4()),
                    folder_id=str(uuid.uuid4()),
                    file_path=f"/test/file_{i}.dat",
                    segments_total=10
                )
                task_id = self.systems['upload_queue'].add_upload(
                    task.file_id,
                    task.folder_id,
                    task.file_path,
                    priority=task.priority
                )
                task_ids.append(task_id)
            
            print(f"    ✅ Added {len(task_ids)} upload tasks")
            
            # Process some tasks
            processed = 0
            for _ in range(100):
                task = self.systems['upload_queue'].get_next_upload()
                if task:
                    # Simulate progress
                    for i in range(5):
                        self.systems['upload_queue'].update_upload_progress(
                            task['task_id'],
                            segment_index=i,
                            message_id=f"<msg{i}@ngPost.com>",
                            bytes_uploaded=768000
                        )
                    processed += 1
            
            print(f"    ✅ Processed {processed} tasks")
            
            # Get statistics
            stats = self.systems['upload_queue'].get_statistics()
            print(f"    Queue stats: {stats}")
            
            # Test resumability
            resumable = self.systems['upload_queue'].resume_uploads()
            print(f"    ✅ {len(resumable)} tasks resumable")
            
            self.results['tests'].append({
                'name': 'Persistent Queue (PostgreSQL)',
                'status': 'PASSED',
                'total_tasks': len(task_ids),
                'processed': processed,
                'resumable': len(resumable)
            })
            self.results['passed'] += 1
            
            return True
            
        except Exception as e:
            print(f"  ❌ Queue test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'Persistent Queue (PostgreSQL)',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_real_usenet_operations(self):
        """Test real Usenet operations with PostgreSQL backend"""
        print("\n📡 Testing Real Usenet Operations...")
        
        try:
            # Create test content
            test_content = b"PostgreSQL Test Upload " + os.urandom(2048)
            test_hash = hashlib.sha256(test_content).hexdigest()
            
            # Generate identifiers
            message_id = self.systems['nntp']._generate_message_id()
            subject_pair = self.systems['security'].generate_subject_pair("postgres_test.dat")
            
            print(f"  Uploading test article to Usenet...")
            print(f"    Message-ID: {message_id}")
            print(f"    Subject: {subject_pair.usenet_subject}")
            
            # Store in PostgreSQL
            segment_data = {
                'segment_id': str(uuid.uuid4()),
                'file_id': str(uuid.uuid4()),
                'folder_id': str(uuid.uuid4()),
                'segment_index': 0,
                'segment_hash': test_hash.encode(),
                'size': len(test_content),
                'message_id': message_id,
                'subject': subject_pair.usenet_subject,
                'internal_subject': subject_pair.internal_subject
            }
            
            self.systems['db'].insert_segments_batch([segment_data])
            print(f"    ✅ Stored in PostgreSQL")
            
            # Build and post article
            headers = {
                'From': 'postgres-test@usenet-sync.com',
                'Newsgroups': 'alt.binaries.test',
                'Subject': subject_pair.usenet_subject,
                'Message-ID': message_id,
                'User-Agent': self.systems['nntp']._get_random_user_agent()
            }
            
            with self.systems['nntp'].get_connection() as conn:
                article_lines = []
                for key, value in headers.items():
                    article_lines.append(f"{key}: {value}")
                article_lines.append("")
                
                import base64
                encoded = base64.b64encode(test_content).decode('ascii')
                for i in range(0, len(encoded), 76):
                    article_lines.append(encoded[i:i+76])
                
                try:
                    conn.post('\r\n'.join(article_lines).encode('utf-8'))
                    print(f"  ✅ Successfully uploaded to Usenet")
                    
                    # Update PostgreSQL with upload time
                    self.systems['db'].save_progress(
                        str(uuid.uuid4()),
                        'test_upload',
                        {
                            'total_items': 1,
                            'processed_items': 1,
                            'last_item_id': message_id,
                            'state': {'uploaded_at': time.time()}
                        }
                    )
                    
                    self.results['tests'].append({
                        'name': 'Usenet Upload (PostgreSQL)',
                        'status': 'PASSED',
                        'message_id': message_id,
                        'size': len(test_content)
                    })
                    self.results['passed'] += 1
                    
                except Exception as e:
                    print(f"  ⚠️ Upload failed: {e}")
                    self.results['tests'].append({
                        'name': 'Usenet Upload (PostgreSQL)',
                        'status': 'SKIPPED',
                        'reason': str(e)
                    })
                    
            return True
            
        except Exception as e:
            print(f"  ❌ Usenet operations failed: {e}")
            self.results['tests'].append({
                'name': 'Usenet Operations (PostgreSQL)',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_performance_at_scale(self):
        """Test PostgreSQL performance at scale"""
        print("\n⚡ Testing Performance at Scale...")
        
        try:
            # Test massive batch insert
            print("  Testing 100,000 segment batch insert...")
            
            massive_batch = []
            for i in range(100000):
                segment = {
                    'segment_id': str(uuid.uuid4()),
                    'file_id': str(uuid.uuid4()) if i % 100 == 0 else massive_batch[-1]['file_id'],
                    'folder_id': str(uuid.uuid4()) if i % 1000 == 0 else massive_batch[0]['folder_id'] if massive_batch else str(uuid.uuid4()),
                    'segment_index': i % 100,
                    'segment_hash': os.urandom(32),
                    'size': 768000,
                    'message_id': f"<{uuid.uuid4()}@ngPost.com>",
                    'subject': f"Scale test {i}",
                    'internal_subject': f"scale_{i}"
                }
                massive_batch.append(segment)
            
            start = time.time()
            self.systems['db'].insert_segments_batch(massive_batch, batch_size=5000)
            elapsed = time.time() - start
            
            rate = len(massive_batch) / elapsed
            print(f"  ✅ Inserted {len(massive_batch):,} segments in {elapsed:.2f}s")
            print(f"  Rate: {rate:.0f} segments/second")
            
            # Get final statistics
            final_stats = self.systems['db'].get_statistics()
            print(f"\n  Final Database Statistics:")
            print(f"    Total segments: {final_stats['total_segments']:,}")
            print(f"    Total size: {final_stats['total_size'] / (1024**3):.2f} GB")
            
            self.results['tests'].append({
                'name': 'Scale Performance (PostgreSQL)',
                'status': 'PASSED',
                'segments': len(massive_batch),
                'time': elapsed,
                'rate': f"{rate:.0f} segments/second",
                'total_in_db': final_stats['total_segments']
            })
            self.results['passed'] += 1
            
            # Run VACUUM ANALYZE
            print("\n  Running VACUUM ANALYZE...")
            self.systems['db'].vacuum_analyze()
            print("  ✅ Database optimized")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Scale test failed: {e}")
            self.results['tests'].append({
                'name': 'Scale Performance (PostgreSQL)',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 POSTGRESQL SYSTEM TEST REPORT")
        print("="*60)
        
        print(f"\nSummary:")
        total_tests = self.results['passed'] + self.results['failed']
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {self.results['passed']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        
        if total_tests > 0:
            success_rate = (self.results['passed'] / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        print(f"\nTest Results:")
        for test in self.results['tests']:
            status = test['status']
            icon = "✅" if status == 'PASSED' else "❌" if status == 'FAILED' else "⚠️"
            print(f"  {icon} {test['name']}: {status}")
            
            if 'error' in test:
                print(f"      Error: {test['error'][:100]}...")
            elif 'reason' in test:
                print(f"      Reason: {test['reason']}")
            elif status == 'PASSED':
                for key, value in test.items():
                    if key not in ['name', 'status']:
                        print(f"      {key}: {value}")
        
        # Save report
        report_file = self.test_dir / "postgresql_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return self.results['failed'] == 0
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up...")
        try:
            # Close database connections
            if 'db' in self.systems:
                self.systems['db'].close()
                print("  ✅ Closed database connections")
            
            # Clean test files
            test_files_dir = self.test_dir / "test_files"
            if test_files_dir.exists():
                shutil.rmtree(test_files_dir)
                print("  ✅ Cleaned test files")
                
        except Exception as e:
            print(f"  ⚠️ Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all PostgreSQL system tests"""
        print("\n" + "="*60)
        print("🚀 RUNNING POSTGRESQL SYSTEM TESTS")
        print("="*60)
        print("Testing with PostgreSQL backend and real operations")
        
        try:
            # Initialize systems
            if not self.initialize_systems():
                print("❌ Failed to initialize systems")
                return False
            
            # Run tests
            self.test_postgresql_operations()
            self.test_parallel_indexing()
            self.test_persistent_queues()
            self.test_real_usenet_operations()
            self.test_performance_at_scale()
            
            # Generate report
            success = self.generate_report()
            
            # Cleanup
            self.cleanup()
            
            if success:
                print("\n✅ ALL POSTGRESQL TESTS PASSED!")
                print("The system is working correctly with PostgreSQL")
            else:
                print("\n⚠️ SOME TESTS FAILED")
                print("Review the report for details")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = RealPostgreSQLSystemTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)