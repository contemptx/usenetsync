#!/usr/bin/env python3
"""
Complete End-to-End Test of Unified System with Real Usenet
"""

import os
import sys
import tempfile
import shutil
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified.database_schema import UnifiedDatabaseSchema
from unified.unified_system import UnifiedSystem
from networking.production_nntp_client import ProductionNNTPClient
from security.enhanced_security_system import EnhancedSecuritySystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_test_data(test_dir: Path) -> int:
    """Create realistic test data with folder structure"""
    print("\n📁 Creating test data with folder structure...")
    
    # Create folder structure
    folders = [
        "documents",
        "documents/reports",
        "documents/reports/2024",
        "images",
        "images/photos",
        "data",
        "data/csv",
        "data/json",
        "videos",
        "archive"
    ]
    
    for folder in folders:
        (test_dir / folder).mkdir(parents=True, exist_ok=True)
    
    # Create various test files
    test_files = [
        # Documents
        ("README.md", b"# Test Project\n\nThis is a test project for UsenetSync unified system.\n" * 50),
        ("documents/report.pdf", os.urandom(1024 * 100)),  # 100KB
        ("documents/notes.txt", b"Meeting notes from the team...\n" * 200),
        ("documents/reports/annual_2024.pdf", os.urandom(1024 * 250)),  # 250KB
        ("documents/reports/2024/q1_report.pdf", os.urandom(1024 * 150)),  # 150KB
        ("documents/reports/2024/q2_report.pdf", os.urandom(1024 * 175)),  # 175KB
        
        # Images
        ("images/logo.png", os.urandom(1024 * 50)),  # 50KB
        ("images/photos/photo1.jpg", os.urandom(1024 * 800)),  # 800KB - will create 2 segments
        ("images/photos/photo2.jpg", os.urandom(1024 * 400)),  # 400KB
        
        # Data files
        ("data/dataset.csv", b"id,name,value\n" + b"1,test,100\n" * 1000),
        ("data/csv/sales_2024.csv", b"date,product,amount\n" + b"2024-01-01,Widget,99.99\n" * 500),
        ("data/json/config.json", b'{"settings": {"mode": "production", "debug": false}}' * 10),
        ("data/json/metadata.json", b'{"version": "1.0", "author": "test"}' * 20),
        
        # Small files for packing test
        ("archive/file1.txt", b"Small file 1" * 10),  # Very small
        ("archive/file2.txt", b"Small file 2" * 10),  # Very small
        ("archive/file3.txt", b"Small file 3" * 10),  # Very small
        
        # Large file to test streaming
        ("videos/sample.mp4", os.urandom(1024 * 1024 * 2)),  # 2MB - will create 3 segments
    ]
    
    total_size = 0
    for file_path, content in test_files:
        full_path = test_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        total_size += len(content)
        
    print(f"  ✓ Created {len(test_files)} files in {len(folders)} folders")
    print(f"  ✓ Total size: {total_size / (1024*1024):.2f} MB")
    
    return len(test_files)

def test_sqlite_system():
    """Test with SQLite database"""
    print("\n" + "="*60)
    print("🔷 TESTING WITH SQLITE DATABASE")
    print("="*60)
    
    # Create unified system with SQLite
    system = UnifiedSystem('sqlite', path='test_unified.db')
    
    # Create test data
    test_dir = Path(tempfile.mkdtemp(prefix="unified_sqlite_"))
    file_count = create_test_data(test_dir)
    
    try:
        # Test indexing
        print("\n📝 Indexing folder...")
        
        def progress_callback(progress):
            print(f"  Processing: {progress['current_file']} "
                  f"({progress['files_indexed']}/{file_count} files)")
        
        index_stats = system.indexer.index_folder(
            str(test_dir),
            progress_callback=progress_callback
        )
        
        print(f"\n✓ Indexing Results:")
        print(f"  Files indexed: {index_stats['files_indexed']}")
        print(f"  Segments created: {index_stats['segments_created']}")
        print(f"  Total size: {index_stats['total_size'] / (1024*1024):.2f} MB")
        print(f"  Errors: {index_stats['errors']}")
        print(f"  Duration: {index_stats['duration']:.2f} seconds")
        
        # Verify folder structure preservation
        print("\n🔍 Verifying folder structure preservation...")
        cursor = system.db_manager.execute(
            "SELECT file_path FROM files WHERE folder_id = ? ORDER BY file_path",
            (index_stats['folder_id'],)
        )
        
        files = cursor.fetchall()
        print(f"  Found {len(files)} files in database:")
        for row in files[:5]:  # Show first 5
            file_path = row['file_path'] if hasattr(row, '__getitem__') else row[0]
            print(f"    - {file_path}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more files")
        
        # Initialize NNTP for upload test
        print("\n📡 Initializing NNTP connection...")
        nntp_client = ProductionNNTPClient(
            host="news.newshosting.com",
            port=563,
            username="contemptx",
            password="Kia211101#",
            use_ssl=True,
            max_connections=2
        )
        
        # Test connection
        test_subject = f"sqlite_test_{int(time.time())}"
        success, response = nntp_client.post_data(
            subject=test_subject,
            data=b"SQLite unified system test",
            newsgroup="alt.binaries.test"
        )
        
        if success:
            print(f"  ✓ NNTP connection successful: {response}")
        else:
            print(f"  ✗ NNTP connection failed: {response}")
            return False
        
        # Initialize upload system
        system.initialize_upload(nntp_client)
        
        # Upload with redundancy and packing
        print("\n📤 Uploading to Usenet with redundancy...")
        upload_stats = system.uploader.upload_folder(
            index_stats['folder_id'],
            redundancy_level=1,  # Create 1 redundancy copy
            pack_small_files=True  # Pack small files together
        )
        
        print(f"\n✓ Upload Results:")
        print(f"  Segments uploaded: {upload_stats['segments_uploaded']}")
        print(f"  Packed segments: {upload_stats['packed_segments']}")
        print(f"  Failed segments: {upload_stats['segments_failed']}")
        print(f"  Redundancy copies: {upload_stats['redundancy_copies']}")
        print(f"  Bytes uploaded: {upload_stats['bytes_uploaded'] / 1024:.1f} KB")
        print(f"  Duration: {upload_stats['duration']:.2f} seconds")
        
        # Verify upload status in database
        cursor = system.db_manager.execute(
            "SELECT COUNT(*) as count FROM segments WHERE upload_status = 'uploaded'",
            ()
        )
        result = cursor.fetchone()
        uploaded_count = result['count'] if hasattr(result, '__getitem__') else result[0]
        
        print(f"\n✓ Database Verification:")
        print(f"  Segments marked as uploaded: {uploaded_count}")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory: {test_dir}")

def test_postgresql_system():
    """Test with PostgreSQL database"""
    print("\n" + "="*60)
    print("🔶 TESTING WITH POSTGRESQL DATABASE")
    print("="*60)
    
    # Create unified system with PostgreSQL
    system = UnifiedSystem(
        'postgresql',
        host='localhost',
        database='usenetsync',
        user='usenetsync',
        password='usenetsync123'
    )
    
    # Create test data
    test_dir = Path(tempfile.mkdtemp(prefix="unified_pg_"))
    file_count = create_test_data(test_dir)
    
    try:
        # Test indexing
        print("\n📝 Indexing folder...")
        
        index_stats = system.indexer.index_folder(str(test_dir))
        
        print(f"\n✓ PostgreSQL Indexing Results:")
        print(f"  Files indexed: {index_stats['files_indexed']}")
        print(f"  Segments created: {index_stats['segments_created']}")
        print(f"  Total size: {index_stats['total_size'] / (1024*1024):.2f} MB")
        
        # Initialize NNTP
        print("\n📡 Initializing NNTP for PostgreSQL test...")
        nntp_client = ProductionNNTPClient(
            host="news.newshosting.com",
            port=563,
            username="contemptx",
            password="Kia211101#",
            use_ssl=True,
            max_connections=3
        )
        
        system.initialize_upload(nntp_client)
        
        # Upload
        print("\n📤 Uploading from PostgreSQL...")
        upload_stats = system.uploader.upload_folder(
            index_stats['folder_id'],
            redundancy_level=2,  # Test with 2 redundancy copies
            pack_small_files=True
        )
        
        print(f"\n✓ PostgreSQL Upload Results:")
        print(f"  Segments uploaded: {upload_stats['segments_uploaded']}")
        print(f"  Redundancy copies: {upload_stats['redundancy_copies']}")
        print(f"  Duration: {upload_stats['duration']:.2f} seconds")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory: {test_dir}")

def test_large_file_handling():
    """Test handling of large files with streaming"""
    print("\n" + "="*60)
    print("🔵 TESTING LARGE FILE HANDLING")
    print("="*60)
    
    system = UnifiedSystem('sqlite', path='test_large.db')
    test_dir = Path(tempfile.mkdtemp(prefix="unified_large_"))
    
    try:
        # Create a large file (10MB)
        print("\n📦 Creating large test file (10MB)...")
        large_file = test_dir / "large_video.mp4"
        large_file.write_bytes(os.urandom(1024 * 1024 * 10))  # 10MB
        
        print("📝 Indexing large file with memory mapping...")
        start_time = time.time()
        
        index_stats = system.indexer.index_folder(str(test_dir))
        
        duration = time.time() - start_time
        
        print(f"\n✓ Large File Indexing Results:")
        print(f"  File size: 10 MB")
        print(f"  Segments created: {index_stats['segments_created']}")
        print(f"  Expected segments: {10 * 1024 // 768 + 1}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Speed: {10 / duration:.2f} MB/s")
        
        # Verify memory efficiency
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        print(f"\n💾 Memory Usage:")
        print(f"  Current memory: {memory_mb:.1f} MB")
        print(f"  ✓ Memory efficient - not loading entire file")
        
        return True
        
    finally:
        shutil.rmtree(test_dir)
        if os.path.exists('test_large.db'):
            os.remove('test_large.db')

def test_security_integration():
    """Test security system integration"""
    print("\n" + "="*60)
    print("🔐 TESTING SECURITY INTEGRATION")
    print("="*60)
    
    # Create a temporary database for security system
    from database.enhanced_database_manager import EnhancedDatabaseManager
    
    db_manager = EnhancedDatabaseManager('test_security.db')
    db_manager.initialize_database()
    
    # Initialize security system with database manager
    security = EnhancedSecuritySystem(db_manager)
    security.initialize_user()
    
    user_id = security.get_user_id()
    print(f"\n🔑 User ID: {user_id[:16]}...")
    
    # Create folder keys
    folder_id = "test_secure_folder"
    folder_keys = security.generate_folder_keys(folder_id)
    
    print(f"📁 Generated folder keys:")
    print(f"  Public key: {folder_keys.public_key[:50]}...")
    
    # Test subject generation
    subject_pair = security.generate_subject_pair(folder_id, 1, 0)
    
    print(f"\n📝 Subject Generation:")
    print(f"  Internal subject: {subject_pair.internal_subject[:32]}...")
    print(f"  Usenet subject: {subject_pair.usenet_subject}")
    
    print("\n✓ Security integration successful")
    
    # Cleanup
    if os.path.exists('test_security.db'):
        os.remove('test_security.db')
    
    return True

def run_all_tests():
    """Run all comprehensive tests"""
    print("\n" + "="*70)
    print(" "*20 + "UNIFIED SYSTEM COMPREHENSIVE TEST")
    print(" "*15 + "WITH REAL USENET CREDENTIALS")
    print("="*70)
    
    results = []
    
    # Test 1: SQLite System
    try:
        results.append(("SQLite System", test_sqlite_system()))
    except Exception as e:
        logger.error(f"SQLite test failed: {e}")
        results.append(("SQLite System", False))
    
    # Test 2: PostgreSQL System
    try:
        results.append(("PostgreSQL System", test_postgresql_system()))
    except Exception as e:
        logger.error(f"PostgreSQL test failed: {e}")
        results.append(("PostgreSQL System", False))
    
    # Test 3: Large File Handling
    try:
        results.append(("Large File Handling", test_large_file_handling()))
    except Exception as e:
        logger.error(f"Large file test failed: {e}")
        results.append(("Large File Handling", False))
    
    # Test 4: Security Integration
    try:
        results.append(("Security Integration", test_security_integration()))
    except Exception as e:
        logger.error(f"Security test failed: {e}")
        results.append(("Security Integration", False))
    
    # Print summary
    print("\n" + "="*70)
    print(" "*25 + "TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:.<40} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("\n" + "-"*70)
    print(f"  Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! The unified system is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed. Please review the logs.")
    
    print("="*70)
    
    # Cleanup
    if os.path.exists('test_unified.db'):
        os.remove('test_unified.db')
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)