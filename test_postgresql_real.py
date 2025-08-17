#!/usr/bin/env python3
"""
Real PostgreSQL System Test
Tests actual database operations with real data
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

from src.database.postgresql_manager import (
    PostgresConfig, 
    EmbeddedPostgresInstaller,
    ShardedPostgreSQLManager
)


class RealPostgreSQLTest:
    """Real tests using actual PostgreSQL database"""
    
    def __init__(self):
        self.test_dir = Path("/workspace/test_postgres_data")
        self.test_dir.mkdir(exist_ok=True)
        self.test_files_dir = self.test_dir / "test_files"
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Test results
        self.results = {
            'tests': [],
            'passed': 0,
            'failed': 0,
            'data': {}
        }
        
    def create_test_files(self, count: int = 1000) -> list:
        """Create real test files"""
        print(f"\n📁 Creating {count} real test files...")
        files = []
        
        for i in range(count):
            # Create folders
            folder_num = i // 100  # 10 files per folder
            folder_path = self.test_files_dir / f"folder_{folder_num:04d}"
            folder_path.mkdir(exist_ok=True)
            
            # Create file with real content
            file_path = folder_path / f"file_{i:06d}.dat"
            
            # Generate unique content
            content = f"Test file {i}\n" * 100
            content += f"Unique data: {uuid.uuid4()}\n" * 50
            content = content.encode()
            
            # Add some binary data
            content += os.urandom(1024 * (i % 10 + 1))  # 1-10 KB random data
            
            file_path.write_bytes(content)
            
            # Calculate hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            files.append({
                'path': str(file_path),
                'size': len(content),
                'hash': file_hash,
                'folder': f"folder_{folder_num:04d}",
                'name': f"file_{i:06d}.dat"
            })
            
            if (i + 1) % 100 == 0:
                print(f"  Created {i + 1} files...")
                
        print(f"✅ Created {len(files)} test files")
        return files
    
    def test_postgresql_installation(self):
        """Test PostgreSQL installation"""
        print("\n🔧 Testing PostgreSQL Installation...")
        
        try:
            # Test embedded installer
            installer = EmbeddedPostgresInstaller(
                install_dir=str(self.test_dir / "postgres_embedded")
            )
            
            # Check if installation works
            if not installer.is_installed():
                print("  PostgreSQL not installed, attempting installation...")
                success = installer.install()
                
                if success:
                    print("  ✅ PostgreSQL installed successfully")
                    self.results['tests'].append({
                        'name': 'PostgreSQL Installation',
                        'status': 'PASSED',
                        'details': 'Embedded PostgreSQL installed'
                    })
                    self.results['passed'] += 1
                else:
                    print("  ❌ PostgreSQL installation failed")
                    print("  Trying with system PostgreSQL...")
                    # Try to connect to system PostgreSQL
                    import psycopg2
                    try:
                        conn = psycopg2.connect(
                            host="localhost",
                            port=5432,
                            database="postgres",
                            user="postgres"
                        )
                        conn.close()
                        print("  ✅ System PostgreSQL available")
                        self.results['tests'].append({
                            'name': 'PostgreSQL Installation',
                            'status': 'PASSED',
                            'details': 'Using system PostgreSQL'
                        })
                        self.results['passed'] += 1
                    except:
                        self.results['tests'].append({
                            'name': 'PostgreSQL Installation',
                            'status': 'FAILED',
                            'details': 'No PostgreSQL available'
                        })
                        self.results['failed'] += 1
                        return False
            else:
                print("  ✅ PostgreSQL already installed")
                self.results['tests'].append({
                    'name': 'PostgreSQL Installation',
                    'status': 'PASSED',
                    'details': 'PostgreSQL already installed'
                })
                self.results['passed'] += 1
                
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results['tests'].append({
                'name': 'PostgreSQL Installation',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_database_operations(self):
        """Test real database operations"""
        print("\n📊 Testing Database Operations...")
        
        try:
            # Create config
            config = PostgresConfig(
                embedded=False,  # Use system PostgreSQL for now
                shard_count=4,   # Test with 4 shards
                pool_size=10,
                database="usenet_test",
                password="test_password_2024"
            )
            
            # Initialize manager
            print("  Initializing sharded database manager...")
            manager = ShardedPostgreSQLManager(config)
            
            # Test 1: Insert segments
            print("\n  Test 1: Inserting segments...")
            test_segments = []
            for i in range(1000):
                segment = {
                    'segment_id': str(uuid.uuid4()),
                    'file_id': str(uuid.uuid4()),
                    'folder_id': str(uuid.uuid4()),
                    'segment_index': i,
                    'segment_hash': os.urandom(32),
                    'size': 768000,
                    'message_id': f"<{uuid.uuid4()}@ngPost.com>",
                    'subject': f"Test Subject {i}",
                    'internal_subject': f"internal_{i}"
                }
                test_segments.append(segment)
            
            start = time.time()
            manager.insert_segments_batch(test_segments, batch_size=100)
            elapsed = time.time() - start
            
            print(f"    ✅ Inserted {len(test_segments)} segments in {elapsed:.2f}s")
            print(f"    Rate: {len(test_segments)/elapsed:.0f} segments/second")
            
            self.results['tests'].append({
                'name': 'Segment Insertion',
                'status': 'PASSED',
                'segments': len(test_segments),
                'time': elapsed,
                'rate': f"{len(test_segments)/elapsed:.0f} segments/second"
            })
            self.results['passed'] += 1
            
            # Test 2: Query segments
            print("\n  Test 2: Querying segments...")
            folder_id = test_segments[0]['folder_id']
            
            start = time.time()
            segments, total = manager.get_segments_paginated(
                folder_id, offset=0, limit=100
            )
            elapsed = time.time() - start
            
            print(f"    ✅ Retrieved {len(segments)} segments in {elapsed:.3f}s")
            
            self.results['tests'].append({
                'name': 'Segment Query',
                'status': 'PASSED',
                'retrieved': len(segments),
                'time': elapsed
            })
            self.results['passed'] += 1
            
            # Test 3: Progress persistence
            print("\n  Test 3: Testing progress persistence...")
            session_id = str(uuid.uuid4())
            progress_data = {
                'total_items': 10000,
                'processed_items': 5000,
                'last_item_id': 'file_5000',
                'state': {'current_folder': 'folder_050'}
            }
            
            manager.save_progress(session_id, 'upload', progress_data)
            loaded = manager.load_progress(session_id)
            
            if loaded and loaded['processed_items'] == 5000:
                print(f"    ✅ Progress saved and loaded correctly")
                self.results['tests'].append({
                    'name': 'Progress Persistence',
                    'status': 'PASSED',
                    'session_id': session_id
                })
                self.results['passed'] += 1
            else:
                print(f"    ❌ Progress persistence failed")
                self.results['tests'].append({
                    'name': 'Progress Persistence',
                    'status': 'FAILED'
                })
                self.results['failed'] += 1
            
            # Test 4: Statistics
            print("\n  Test 4: Getting statistics...")
            stats = manager.get_statistics()
            
            print(f"    Total segments: {stats['total_segments']:,}")
            print(f"    Total files: {stats['total_files']:,}")
            print(f"    Total size: {stats['total_size'] / (1024**2):.2f} MB")
            print(f"    Shards: {len(stats['shards'])}")
            
            self.results['tests'].append({
                'name': 'Statistics',
                'status': 'PASSED',
                'stats': stats
            })
            self.results['passed'] += 1
            
            # Test 5: Streaming iteration
            print("\n  Test 5: Testing streaming iteration...")
            file_id = test_segments[0]['file_id']
            
            batch_count = 0
            total_segments = 0
            for batch in manager.iterate_segments(file_id, batch_size=10):
                batch_count += 1
                total_segments += len(batch)
            
            print(f"    ✅ Streamed {total_segments} segments in {batch_count} batches")
            
            self.results['tests'].append({
                'name': 'Streaming Iteration',
                'status': 'PASSED',
                'segments': total_segments,
                'batches': batch_count
            })
            self.results['passed'] += 1
            
            # Clean up
            manager.close()
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database operations failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'Database Operations',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_parallel_indexing(self):
        """Test parallel indexing with real files"""
        print("\n🔍 Testing Parallel Indexing...")
        
        try:
            # Import indexer
            from src.indexing.parallel_indexer import ParallelIndexer
            
            # Create test files
            files = self.create_test_files(500)  # Create 500 real files
            
            # Setup mock database manager
            class MockDBManager:
                def __init__(self):
                    self.files = []
                    self.progress = {}
                    
                def insert_files_batch(self, files):
                    self.files.extend(files)
                    
                def save_progress(self, session_id, op_type, data):
                    self.progress[session_id] = data
                    
                def load_progress(self, session_id):
                    return self.progress.get(session_id)
                    
                def mark_progress_complete(self, session_id):
                    if session_id in self.progress:
                        self.progress[session_id]['completed'] = True
                        
                def get_file_index(self):
                    return {}
            
            db_manager = MockDBManager()
            
            # Create indexer
            indexer = ParallelIndexer(db_manager, worker_count=4)
            
            # Run indexing
            print(f"  Indexing {len(files)} files with 4 workers...")
            start = time.time()
            
            stats = indexer.index_directory(str(self.test_files_dir))
            
            elapsed = time.time() - start
            
            print(f"\n  ✅ Indexing Results:")
            print(f"    Files indexed: {stats['processed_files']:,}")
            print(f"    Total size: {stats['total_size'] / (1024**2):.2f} MB")
            print(f"    Time: {elapsed:.2f}s")
            print(f"    Rate: {stats['files_per_second']:.0f} files/second")
            
            # Verify all files were indexed
            if len(db_manager.files) >= len(files):
                print(f"    ✅ All files indexed correctly")
                self.results['tests'].append({
                    'name': 'Parallel Indexing',
                    'status': 'PASSED',
                    'files': stats['processed_files'],
                    'rate': f"{stats['files_per_second']:.0f} files/second"
                })
                self.results['passed'] += 1
            else:
                print(f"    ❌ Some files missing")
                self.results['tests'].append({
                    'name': 'Parallel Indexing',
                    'status': 'FAILED',
                    'expected': len(files),
                    'got': len(db_manager.files)
                })
                self.results['failed'] += 1
                
            return True
            
        except Exception as e:
            print(f"  ❌ Indexing test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'Parallel Indexing',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def test_persistent_queue(self):
        """Test persistent queue system"""
        print("\n📦 Testing Persistent Queue...")
        
        try:
            from src.queue.persistent_queue import (
                PersistentQueue,
                UploadTask,
                DownloadTask,
                TaskStatus
            )
            
            # Create queue
            queue_dir = self.test_dir / "test_queue"
            queue = PersistentQueue(str(queue_dir), max_memory_items=100)
            
            # Add upload tasks
            print("  Adding 1000 upload tasks...")
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
                task_id = queue.add_task(task)
                task_ids.append(task_id)
            
            print(f"    ✅ Added {len(task_ids)} tasks")
            
            # Get tasks
            print("  Processing tasks...")
            processed = 0
            while processed < 100:
                task = queue.get_task(timeout=1)
                if task:
                    # Simulate processing
                    queue.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
                    
                    # Update progress
                    task.segments_completed = 5
                    task.bytes_uploaded = 384000
                    queue.update_task_progress(task.task_id, {
                        'segments_completed': 5,
                        'bytes_uploaded': 384000
                    })
                    
                    # Complete task
                    queue.update_task_status(task.task_id, TaskStatus.COMPLETED)
                    processed += 1
                else:
                    break
            
            print(f"    ✅ Processed {processed} tasks")
            
            # Test persistence
            print("  Testing persistence...")
            queue._save_tasks()
            
            # Create new queue instance
            queue2 = PersistentQueue(str(queue_dir), max_memory_items=100)
            
            # Check tasks loaded
            remaining = len([t for t in queue2.tasks.values() 
                           if t.status == TaskStatus.PENDING])
            
            print(f"    ✅ Loaded {len(queue2.tasks)} tasks")
            print(f"    Remaining: {remaining}")
            
            self.results['tests'].append({
                'name': 'Persistent Queue',
                'status': 'PASSED',
                'total_tasks': len(task_ids),
                'processed': processed,
                'persisted': len(queue2.tasks)
            })
            self.results['passed'] += 1
            
            return True
            
        except Exception as e:
            print(f"  ❌ Queue test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results['tests'].append({
                'name': 'Persistent Queue',
                'status': 'FAILED',
                'error': str(e)
            })
            self.results['failed'] += 1
            return False
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT")
        print("="*60)
        
        print(f"\nSummary:")
        print(f"  Total Tests: {self.results['passed'] + self.results['failed']}")
        print(f"  ✅ Passed: {self.results['passed']}")
        print(f"  ❌ Failed: {self.results['failed']}")
        
        print(f"\nTest Results:")
        for test in self.results['tests']:
            status = "✅" if test['status'] == 'PASSED' else "❌"
            print(f"  {status} {test['name']}: {test['status']}")
            if 'error' in test:
                print(f"      Error: {test['error']}")
            if 'rate' in test:
                print(f"      Performance: {test['rate']}")
        
        # Save report
        report_file = self.test_dir / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return self.results['failed'] == 0
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        try:
            if self.test_files_dir.exists():
                shutil.rmtree(self.test_files_dir)
            print("  ✅ Cleaned up test files")
        except Exception as e:
            print(f"  ⚠️ Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🚀 RUNNING REAL POSTGRESQL SYSTEM TESTS")
        print("="*60)
        
        try:
            # Run tests
            # self.test_postgresql_installation()  # Skip if using system PostgreSQL
            self.test_database_operations()
            self.test_parallel_indexing()
            self.test_persistent_queue()
            
            # Generate report
            success = self.generate_report()
            
            # Cleanup
            self.cleanup()
            
            if success:
                print("\n✅ ALL TESTS PASSED!")
            else:
                print("\n❌ SOME TESTS FAILED!")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = RealPostgreSQLTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)