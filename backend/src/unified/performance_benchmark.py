#!/usr/bin/env python3
"""
Performance Benchmark System for Unified UsenetSync
Measures and compares performance metrics across different operations
"""

import os
import sys
import time
import psutil
import hashlib
import tempfile
import shutil
import statistics
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, asdict
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.unified_system import UnifiedSystem
from unified.database_schema import UnifiedDatabaseSchema
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise during benchmarks

@dataclass
class BenchmarkResult:
    """Results from a benchmark run"""
    operation: str
    duration: float
    throughput: float
    memory_peak: float
    cpu_percent: float
    items_processed: int
    errors: int
    metadata: Dict[str, Any] = None

class PerformanceBenchmark:
    """Comprehensive performance benchmarking system"""
    
    def __init__(self):
        self.results = []
        self.test_dir = None
        self.process = psutil.Process()
        
    def setup(self):
        """Setup benchmark environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="benchmark_"))
        
    def teardown(self):
        """Cleanup benchmark environment"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks"""
        print("\n" + "="*70)
        print(" "*20 + "PERFORMANCE BENCHMARK SUITE")
        print("="*70 + "\n")
        
        self.setup()
        
        try:
            # Benchmark 1: Indexing Performance
            self.benchmark_indexing_performance()
            
            # Benchmark 2: Database Operations
            self.benchmark_database_operations()
            
            # Benchmark 3: Segment Processing
            self.benchmark_segment_processing()
            
            # Benchmark 4: Concurrent Operations
            self.benchmark_concurrent_operations()
            
            # Benchmark 5: Memory Efficiency
            self.benchmark_memory_efficiency()
            
            # Benchmark 6: Large Dataset Handling
            self.benchmark_large_dataset()
            
            # Generate report
            report = self.generate_report()
            
            return report
            
        finally:
            self.teardown()
            
    def benchmark_indexing_performance(self):
        """Benchmark file indexing performance"""
        print("📊 BENCHMARK 1: Indexing Performance")
        print("-" * 50)
        
        # Test different file sizes
        test_cases = [
            ("Small files (100 x 1KB)", 100, 1024),
            ("Medium files (50 x 100KB)", 50, 100 * 1024),
            ("Large files (10 x 1MB)", 10, 1024 * 1024),
            ("Very large file (1 x 10MB)", 1, 10 * 1024 * 1024),
        ]
        
        for test_name, file_count, file_size in test_cases:
            # Create test files
            test_folder = self.test_dir / f"index_test_{file_count}_{file_size}"
            test_folder.mkdir()
            
            total_size = 0
            for i in range(file_count):
                file_path = test_folder / f"file_{i}.dat"
                data = os.urandom(file_size)
                file_path.write_bytes(data)
                total_size += file_size
                
            # Benchmark indexing
            system = UnifiedSystem('sqlite', path=str(self.test_dir / 'index.db'))
            
            start_time = time.time()
            start_memory = self.process.memory_info().rss
            
            stats = system.indexer.index_folder(str(test_folder))
            
            duration = time.time() - start_time
            memory_peak = (self.process.memory_info().rss - start_memory) / (1024 * 1024)
            throughput = (total_size / (1024 * 1024)) / duration if duration > 0 else 0
            
            result = BenchmarkResult(
                operation=f"Indexing: {test_name}",
                duration=duration,
                throughput=throughput,
                memory_peak=memory_peak,
                cpu_percent=self.process.cpu_percent(),
                items_processed=stats['files_indexed'],
                errors=stats.get('errors', 0),
                metadata={
                    'segments_created': stats['segments_created'],
                    'total_size_mb': total_size / (1024 * 1024)
                }
            )
            
            self.results.append(result)
            
            print(f"  {test_name}:")
            print(f"    Duration: {duration:.3f}s")
            print(f"    Throughput: {throughput:.2f} MB/s")
            print(f"    Memory: {memory_peak:.1f} MB")
            print(f"    Files: {stats['files_indexed']}, Segments: {stats['segments_created']}")
            
    def benchmark_database_operations(self):
        """Benchmark database operations"""
        print("\n📊 BENCHMARK 2: Database Operations")
        print("-" * 50)
        
        # Test both SQLite and PostgreSQL
        db_configs = [
            ("SQLite", 'sqlite', {'path': str(self.test_dir / 'bench.db')}),
        ]
        
        # Add PostgreSQL if available
        try:
            import psycopg2
            db_configs.append(
                ("PostgreSQL", 'postgresql', {
                    'host': 'localhost',
                    'database': 'usenetsync',
                    'user': 'usenetsync',
                    'password': 'usenetsync123'
                })
            )
        except:
            print("  (PostgreSQL not available for benchmarking)")
            
        operations = [
            ("Insert 1000 files", self._benchmark_insert_files, 1000),
            ("Query by hash", self._benchmark_query_hash, 100),
            ("Update status", self._benchmark_update_status, 500),
            ("Complex join", self._benchmark_complex_join, 50),
        ]
        
        for db_name, db_type, db_params in db_configs:
            print(f"\n  Testing {db_name}:")
            
            # Create schema
            schema = UnifiedDatabaseSchema(db_type, **db_params)
            schema.create_schema()
            
            from unified.unified_system import UnifiedDatabaseManager
            db_manager = UnifiedDatabaseManager(db_type, **db_params)
            db_manager.connect()
            
            for op_name, op_func, count in operations:
                start_time = time.time()
                
                op_func(db_manager, count)
                
                duration = time.time() - start_time
                ops_per_sec = count / duration if duration > 0 else 0
                
                result = BenchmarkResult(
                    operation=f"DB {db_name}: {op_name}",
                    duration=duration,
                    throughput=ops_per_sec,
                    memory_peak=0,
                    cpu_percent=self.process.cpu_percent(),
                    items_processed=count,
                    errors=0
                )
                
                self.results.append(result)
                
                print(f"    {op_name}: {duration:.3f}s ({ops_per_sec:.0f} ops/s)")
                
    def benchmark_segment_processing(self):
        """Benchmark segment creation and packing"""
        print("\n📊 BENCHMARK 3: Segment Processing")
        print("-" * 50)
        
        # Create test file
        test_file = self.test_dir / "segment_test.dat"
        file_sizes = [
            ("1MB file", 1024 * 1024),
            ("10MB file", 10 * 1024 * 1024),
            ("50MB file", 50 * 1024 * 1024),
        ]
        
        for test_name, file_size in file_sizes:
            test_file.write_bytes(os.urandom(file_size))
            
            # Benchmark segment creation
            segment_size = 768 * 1024  # 768KB segments
            
            start_time = time.time()
            start_memory = self.process.memory_info().rss
            
            segments = []
            with open(test_file, 'rb') as f:
                while True:
                    chunk = f.read(segment_size)
                    if not chunk:
                        break
                    segment_hash = hashlib.sha256(chunk).hexdigest()
                    segments.append(segment_hash)
                    
            duration = time.time() - start_time
            memory_used = (self.process.memory_info().rss - start_memory) / (1024 * 1024)
            throughput = (file_size / (1024 * 1024)) / duration if duration > 0 else 0
            
            result = BenchmarkResult(
                operation=f"Segmentation: {test_name}",
                duration=duration,
                throughput=throughput,
                memory_peak=memory_used,
                cpu_percent=self.process.cpu_percent(),
                items_processed=len(segments),
                errors=0
            )
            
            self.results.append(result)
            
            print(f"  {test_name}:")
            print(f"    Duration: {duration:.3f}s")
            print(f"    Throughput: {throughput:.2f} MB/s")
            print(f"    Segments: {len(segments)}")
            print(f"    Memory: {memory_used:.1f} MB")
            
    def benchmark_concurrent_operations(self):
        """Benchmark concurrent processing capabilities"""
        print("\n📊 BENCHMARK 4: Concurrent Operations")
        print("-" * 50)
        
        # Test different concurrency levels
        test_cases = [
            ("Sequential (1 thread)", 1),
            ("Low concurrency (2 threads)", 2),
            ("Medium concurrency (4 threads)", 4),
            ("High concurrency (8 threads)", 8),
            ("Max concurrency (CPU count)", os.cpu_count()),
        ]
        
        def process_file(file_path):
            """Simulate file processing"""
            data = file_path.read_bytes()
            hash_result = hashlib.sha256(data).hexdigest()
            time.sleep(0.01)  # Simulate I/O
            return hash_result
            
        # Create test files
        test_files = []
        for i in range(50):
            file_path = self.test_dir / f"concurrent_{i}.dat"
            file_path.write_bytes(os.urandom(10 * 1024))  # 10KB files
            test_files.append(file_path)
            
        for test_name, thread_count in test_cases:
            start_time = time.time()
            
            if thread_count == 1:
                # Sequential processing
                results = [process_file(f) for f in test_files]
            else:
                # Parallel processing
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    results = list(executor.map(process_file, test_files))
                    
            duration = time.time() - start_time
            throughput = len(test_files) / duration if duration > 0 else 0
            
            result = BenchmarkResult(
                operation=f"Concurrent: {test_name}",
                duration=duration,
                throughput=throughput,
                memory_peak=0,
                cpu_percent=self.process.cpu_percent(),
                items_processed=len(test_files),
                errors=0,
                metadata={'thread_count': thread_count}
            )
            
            self.results.append(result)
            
            print(f"  {test_name}:")
            print(f"    Duration: {duration:.3f}s")
            print(f"    Throughput: {throughput:.1f} files/s")
            
    def benchmark_memory_efficiency(self):
        """Benchmark memory efficiency with large files"""
        print("\n📊 BENCHMARK 5: Memory Efficiency")
        print("-" * 50)
        
        # Test memory-mapped vs regular file processing
        file_sizes = [
            ("10MB", 10 * 1024 * 1024),
            ("50MB", 50 * 1024 * 1024),
            ("100MB", 100 * 1024 * 1024),
        ]
        
        for size_name, file_size in file_sizes:
            test_file = self.test_dir / f"memory_test_{size_name}.dat"
            test_file.write_bytes(os.urandom(file_size))
            
            # Test regular reading
            start_memory = self.process.memory_info().rss
            start_time = time.time()
            
            with open(test_file, 'rb') as f:
                data = f.read()
                hash_result = hashlib.sha256(data).hexdigest()
                
            regular_duration = time.time() - start_time
            regular_memory = (self.process.memory_info().rss - start_memory) / (1024 * 1024)
            
            # Force garbage collection
            del data
            import gc
            gc.collect()
            
            # Test memory-mapped reading
            import mmap
            start_memory = self.process.memory_info().rss
            start_time = time.time()
            
            with open(test_file, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                    hash_result = hashlib.sha256(mmapped).hexdigest()
                    
            mmap_duration = time.time() - start_time
            mmap_memory = (self.process.memory_info().rss - start_memory) / (1024 * 1024)
            
            print(f"  {size_name} file:")
            print(f"    Regular: {regular_duration:.3f}s, {regular_memory:.1f} MB")
            print(f"    Memory-mapped: {mmap_duration:.3f}s, {mmap_memory:.1f} MB")
            print(f"    Memory saved: {regular_memory - mmap_memory:.1f} MB")
            
            result = BenchmarkResult(
                operation=f"Memory efficiency: {size_name}",
                duration=mmap_duration,
                throughput=(file_size / (1024 * 1024)) / mmap_duration if mmap_duration > 0 else 0,
                memory_peak=mmap_memory,
                cpu_percent=self.process.cpu_percent(),
                items_processed=1,
                errors=0,
                metadata={
                    'regular_memory_mb': regular_memory,
                    'mmap_memory_mb': mmap_memory,
                    'memory_saved_mb': regular_memory - mmap_memory
                }
            )
            
            self.results.append(result)
            
    def benchmark_large_dataset(self):
        """Benchmark handling of large datasets"""
        print("\n📊 BENCHMARK 6: Large Dataset Handling")
        print("-" * 50)
        
        # Simulate large dataset
        print("  Creating simulated large dataset...")
        
        dataset_folder = self.test_dir / "large_dataset"
        dataset_folder.mkdir()
        
        # Create folder structure
        folders = ['documents', 'images', 'videos', 'archives', 'data']
        total_files = 0
        total_size = 0
        
        for folder in folders:
            folder_path = dataset_folder / folder
            folder_path.mkdir()
            
            # Create files in each folder
            for i in range(20):  # 20 files per folder
                file_path = folder_path / f"{folder}_{i}.dat"
                file_size = 1024 * 1024  # 1MB each
                file_path.write_bytes(os.urandom(file_size))
                total_files += 1
                total_size += file_size
                
        print(f"  Created {total_files} files, {total_size / (1024*1024):.1f} MB total")
        
        # Benchmark indexing large dataset
        system = UnifiedSystem('sqlite', path=str(self.test_dir / 'large.db'))
        
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        stats = system.indexer.index_folder(str(dataset_folder))
        
        duration = time.time() - start_time
        memory_peak = (self.process.memory_info().rss - start_memory) / (1024 * 1024)
        throughput = (total_size / (1024 * 1024)) / duration if duration > 0 else 0
        files_per_sec = total_files / duration if duration > 0 else 0
        
        result = BenchmarkResult(
            operation="Large dataset indexing",
            duration=duration,
            throughput=throughput,
            memory_peak=memory_peak,
            cpu_percent=self.process.cpu_percent(),
            items_processed=stats['files_indexed'],
            errors=stats.get('errors', 0),
            metadata={
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'files_per_second': files_per_sec,
                'segments_created': stats['segments_created']
            }
        )
        
        self.results.append(result)
        
        print(f"  Results:")
        print(f"    Duration: {duration:.3f}s")
        print(f"    Throughput: {throughput:.2f} MB/s")
        print(f"    Files/sec: {files_per_sec:.1f}")
        print(f"    Memory peak: {memory_peak:.1f} MB")
        print(f"    Segments: {stats['segments_created']}")
        
    def _benchmark_insert_files(self, db_manager, count):
        """Benchmark file insertions"""
        for i in range(count):
            db_manager.execute("""
                INSERT INTO files 
                (folder_id, file_path, file_hash, file_size, modified_time,
                 version, segment_count, state)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, 1, 1, 'indexed')
            """, (
                f"folder_{i % 10}",
                f"path/to/file_{i}.txt",
                hashlib.sha256(f"file_{i}".encode()).hexdigest(),
                1024 * (i % 100 + 1)
            ))
            
    def _benchmark_query_hash(self, db_manager, count):
        """Benchmark hash queries"""
        for i in range(count):
            hash_value = hashlib.sha256(f"file_{i}".encode()).hexdigest()
            db_manager.fetchall(
                "SELECT * FROM files WHERE file_hash = %s",
                (hash_value,)
            )
            
    def _benchmark_update_status(self, db_manager, count):
        """Benchmark status updates"""
        for i in range(count):
            db_manager.execute(
                "UPDATE files SET state = %s WHERE file_id = %s",
                ('uploaded', i + 1)
            )
            
    def _benchmark_complex_join(self, db_manager, count):
        """Benchmark complex join operations"""
        for i in range(count):
            db_manager.fetchall("""
                SELECT f.*, COUNT(s.segment_id) as segment_count
                FROM files f
                LEFT JOIN segments s ON f.file_id = s.file_id
                WHERE f.folder_id = %s
                GROUP BY f.file_id
                LIMIT 10
            """, (f"folder_{i % 10}",))
            
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        print("\n" + "="*70)
        print(" "*25 + "BENCHMARK REPORT")
        print("="*70)
        
        # Group results by operation type
        operation_groups = {}
        for result in self.results:
            op_type = result.operation.split(':')[0]
            if op_type not in operation_groups:
                operation_groups[op_type] = []
            operation_groups[op_type].append(result)
            
        # Calculate statistics
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_benchmarks': len(self.results),
            'groups': {}
        }
        
        for group_name, group_results in operation_groups.items():
            durations = [r.duration for r in group_results]
            throughputs = [r.throughput for r in group_results if r.throughput > 0]
            memory_peaks = [r.memory_peak for r in group_results if r.memory_peak > 0]
            
            group_stats = {
                'count': len(group_results),
                'avg_duration': statistics.mean(durations) if durations else 0,
                'avg_throughput': statistics.mean(throughputs) if throughputs else 0,
                'avg_memory': statistics.mean(memory_peaks) if memory_peaks else 0,
                'total_items': sum(r.items_processed for r in group_results),
                'total_errors': sum(r.errors for r in group_results)
            }
            
            report['groups'][group_name] = group_stats
            
            print(f"\n{group_name}:")
            print(f"  Benchmarks run: {group_stats['count']}")
            print(f"  Avg duration: {group_stats['avg_duration']:.3f}s")
            if group_stats['avg_throughput'] > 0:
                print(f"  Avg throughput: {group_stats['avg_throughput']:.2f} units/s")
            if group_stats['avg_memory'] > 0:
                print(f"  Avg memory: {group_stats['avg_memory']:.1f} MB")
                
        # Performance summary
        print("\n" + "-"*70)
        print("PERFORMANCE SUMMARY:")
        
        # Find best performers
        if self.results:
            fastest = min(self.results, key=lambda r: r.duration)
            print(f"  Fastest operation: {fastest.operation} ({fastest.duration:.3f}s)")
            
            highest_throughput = max(self.results, key=lambda r: r.throughput)
            print(f"  Highest throughput: {highest_throughput.operation} "
                  f"({highest_throughput.throughput:.2f} units/s)")
            
            most_efficient = min([r for r in self.results if r.memory_peak > 0], 
                                key=lambda r: r.memory_peak, default=None)
            if most_efficient:
                print(f"  Most memory efficient: {most_efficient.operation} "
                      f"({most_efficient.memory_peak:.1f} MB)")
                
        print("="*70)
        
        # Save detailed results
        report['detailed_results'] = [asdict(r) for r in self.results]
        
        # Save to file
        report_file = self.test_dir.parent / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        return report


def run_benchmarks():
    """Run complete benchmark suite"""
    benchmark = PerformanceBenchmark()
    report = benchmark.run_all_benchmarks()
    
    # Return success if no errors
    total_errors = sum(r.errors for r in benchmark.results)
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    exit_code = run_benchmarks()
    sys.exit(exit_code)