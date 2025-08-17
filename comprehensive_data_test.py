#!/usr/bin/env python3
"""
Comprehensive End-to-End Test with Full Data Tracking
Tracks every piece of data through the entire UsenetSync system
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import secrets

# Add src to path
sys.path.insert(0, '/workspace')

# Import all real system components
from src.database.production_db_wrapper import ProductionDatabaseManager
from src.database.enhanced_database_manager import EnhancedDatabaseManager
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.networking.production_nntp_client import ProductionNNTPClient
from src.upload.enhanced_upload_system import EnhancedUploadSystem
from src.upload.publishing_system import PublishingSystem
from src.upload.segment_packing_system import SegmentPackingSystem
from src.download.enhanced_download_system import EnhancedDownloadSystem
from src.download.segment_retrieval_system import SegmentRetrievalSystem
from src.monitoring.monitoring_system import MonitoringSystem
from src.indexing.versioned_core_index_system import VersionedCoreIndexSystem
from src.indexing.simplified_binary_index import SimplifiedBinaryIndex
from src.security.user_management import UserManager
from src.indexing.share_id_generator import ShareIDGenerator
from src.config.secure_config import SecureConfigLoader
from src.config.configuration_manager import ConfigurationManager
from src.database.enhanced_database_manager import ConnectionPool, DatabaseConfig
from database_write_queue import DatabaseWriteQueue
from optimized_indexing import OptimizedIndexingSystem

class DataTracker:
    """Tracks all data throughout the test"""
    
    def __init__(self):
        self.test_data = {
            'original_files': {},
            'indexed_data': {},
            'packed_segments': {},
            'uploaded_articles': {},
            'published_shares': {},
            'retrieved_segments': {},
            'downloaded_files': {},
            'verification_results': {}
        }
        self.recommendations = []
        
    def track_original_file(self, filepath: str, content: bytes, metadata: Dict):
        """Track original test file data"""
        file_hash = hashlib.sha256(content).hexdigest()
        self.test_data['original_files'][filepath] = {
            'path': filepath,
            'size': len(content),
            'hash': file_hash,
            'content_sample': content[:100] if len(content) > 100 else content,
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }
        return file_hash
        
    def track_indexed_file(self, file_id: int, folder_id: int, file_info: Dict):
        """Track indexed file information"""
        self.test_data['indexed_data'][file_id] = {
            'file_id': file_id,
            'folder_id': folder_id,
            'filename': file_info.get('filename'),
            'path': file_info.get('file_path'),
            'size': file_info.get('size'),
            'hash': file_info.get('hash'),
            'indexed_at': datetime.now().isoformat()
        }
        
    def track_segment(self, segment_id: str, segment_data: Dict):
        """Track packed segment data"""
        self.test_data['packed_segments'][segment_id] = {
            'segment_id': segment_id,
            'file_id': segment_data.get('file_id'),
            'segment_index': segment_data.get('segment_index'),
            'size': segment_data.get('size'),
            'hash': segment_data.get('hash'),
            'packed_at': datetime.now().isoformat()
        }
        
    def track_upload(self, message_id: str, subject: str, segment_info: Dict, response: Any):
        """Track uploaded article information"""
        self.test_data['uploaded_articles'][message_id] = {
            'message_id': message_id,
            'subject': subject,
            'segment_info': segment_info,
            'server_response': str(response),
            'uploaded_at': datetime.now().isoformat()
        }
        
    def track_share(self, share_id: str, share_info: Dict):
        """Track published share information"""
        self.test_data['published_shares'][share_id] = {
            'share_id': share_id,
            'share_type': share_info.get('share_type'),
            'folder_id': share_info.get('folder_id'),
            'access_string': share_info.get('access_string'),
            'metadata': share_info.get('metadata'),
            'published_at': datetime.now().isoformat()
        }
        
    def track_retrieval(self, message_id: str, retrieved_data: bytes, metadata: Dict):
        """Track retrieved segment data"""
        self.test_data['retrieved_segments'][message_id] = {
            'message_id': message_id,
            'size': len(retrieved_data),
            'hash': hashlib.sha256(retrieved_data).hexdigest(),
            'metadata': metadata,
            'retrieved_at': datetime.now().isoformat()
        }
        
    def track_download(self, filepath: str, content: bytes, metadata: Dict):
        """Track downloaded file data"""
        file_hash = hashlib.sha256(content).hexdigest()
        self.test_data['downloaded_files'][filepath] = {
            'path': filepath,
            'size': len(content),
            'hash': file_hash,
            'content_sample': content[:100] if len(content) > 100 else content,
            'metadata': metadata,
            'downloaded_at': datetime.now().isoformat()
        }
        return file_hash
        
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify that uploaded data matches downloaded data exactly"""
        results = {
            'success': True,
            'checks': [],
            'mismatches': []
        }
        
        # Compare original files with downloaded files
        for orig_path, orig_data in self.test_data['original_files'].items():
            filename = os.path.basename(orig_path)
            
            # Find corresponding downloaded file
            downloaded = None
            for dl_path, dl_data in self.test_data['downloaded_files'].items():
                if os.path.basename(dl_path) == filename:
                    downloaded = dl_data
                    break
                    
            if not downloaded:
                results['success'] = False
                results['mismatches'].append({
                    'file': filename,
                    'issue': 'File not found in downloads'
                })
                continue
                
            # Compare hashes
            if orig_data['hash'] != downloaded['hash']:
                results['success'] = False
                results['mismatches'].append({
                    'file': filename,
                    'issue': 'Hash mismatch',
                    'original_hash': orig_data['hash'],
                    'downloaded_hash': downloaded['hash']
                })
            else:
                results['checks'].append({
                    'file': filename,
                    'status': 'VERIFIED',
                    'hash': orig_data['hash'],
                    'size': orig_data['size']
                })
                
            # Compare sizes
            if orig_data['size'] != downloaded['size']:
                results['success'] = False
                results['mismatches'].append({
                    'file': filename,
                    'issue': 'Size mismatch',
                    'original_size': orig_data['size'],
                    'downloaded_size': downloaded['size']
                })
                
        self.test_data['verification_results'] = results
        return results
        
    def add_recommendation(self, category: str, issue: str, suggestion: str, priority: str = 'medium'):
        """Add a system recommendation"""
        self.recommendations.append({
            'category': category,
            'issue': issue,
            'suggestion': suggestion,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        })
        
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DATA TRACKING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Original Files
        report.append("📁 ORIGINAL FILES")
        report.append("-" * 40)
        for path, data in self.test_data['original_files'].items():
            report.append(f"  File: {os.path.basename(path)}")
            report.append(f"    Path: {path}")
            report.append(f"    Size: {data['size']} bytes")
            report.append(f"    Hash: {data['hash']}")
            report.append(f"    Created: {data['created_at']}")
            report.append("")
            
        # Indexed Data
        report.append("🗂️  INDEXED DATA")
        report.append("-" * 40)
        for file_id, data in self.test_data['indexed_data'].items():
            report.append(f"  File ID: {file_id}")
            report.append(f"    Filename: {data['filename']}")
            report.append(f"    Folder ID: {data['folder_id']}")
            report.append(f"    Size: {data['size']} bytes")
            report.append(f"    Hash: {data['hash']}")
            report.append(f"    Indexed: {data['indexed_at']}")
            report.append("")
            
        # Packed Segments
        report.append("📦 PACKED SEGMENTS")
        report.append("-" * 40)
        segment_count = len(self.test_data['packed_segments'])
        report.append(f"  Total Segments: {segment_count}")
        if segment_count > 0:
            # Show first few segments
            for i, (seg_id, data) in enumerate(list(self.test_data['packed_segments'].items())[:3]):
                report.append(f"  Segment {i+1}:")
                report.append(f"    ID: {seg_id}")
                report.append(f"    File ID: {data['file_id']}")
                report.append(f"    Index: {data['segment_index']}")
                report.append(f"    Size: {data['size']} bytes")
                report.append(f"    Hash: {data['hash'][:16]}...")
            if segment_count > 3:
                report.append(f"  ... and {segment_count - 3} more segments")
        report.append("")
        
        # Uploaded Articles
        report.append("📤 UPLOADED TO USENET")
        report.append("-" * 40)
        for msg_id, data in self.test_data['uploaded_articles'].items():
            report.append(f"  Message ID: {msg_id}")
            report.append(f"    Subject: {data['subject']}")
            report.append(f"    Segment: {data['segment_info'].get('segment_index', 'N/A')}")
            report.append(f"    Response: {data['server_response']}")
            report.append(f"    Uploaded: {data['uploaded_at']}")
            report.append("")
            
        # Published Shares
        report.append("🔗 PUBLISHED SHARES")
        report.append("-" * 40)
        for share_id, data in self.test_data['published_shares'].items():
            report.append(f"  Share ID: {share_id}")
            report.append(f"    Type: {data['share_type']}")
            report.append(f"    Folder ID: {data['folder_id']}")
            report.append(f"    Access String: {data['access_string'][:50]}...")
            report.append(f"    Published: {data['published_at']}")
            report.append("")
            
        # Retrieved Segments
        report.append("📥 RETRIEVED FROM USENET")
        report.append("-" * 40)
        for msg_id, data in self.test_data['retrieved_segments'].items():
            report.append(f"  Message ID: {msg_id}")
            report.append(f"    Size: {data['size']} bytes")
            report.append(f"    Hash: {data['hash'][:16]}...")
            report.append(f"    Retrieved: {data['retrieved_at']}")
        report.append("")
        
        # Downloaded Files
        report.append("💾 DOWNLOADED FILES")
        report.append("-" * 40)
        for path, data in self.test_data['downloaded_files'].items():
            report.append(f"  File: {os.path.basename(path)}")
            report.append(f"    Path: {path}")
            report.append(f"    Size: {data['size']} bytes")
            report.append(f"    Hash: {data['hash']}")
            report.append(f"    Downloaded: {data['downloaded_at']}")
            report.append("")
            
        # Verification Results
        report.append("✅ DATA INTEGRITY VERIFICATION")
        report.append("-" * 40)
        if 'verification_results' in self.test_data:
            results = self.test_data['verification_results']
            report.append(f"  Overall Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
            report.append(f"  Files Verified: {len(results['checks'])}")
            
            for check in results['checks']:
                report.append(f"    ✅ {check['file']}: {check['status']}")
                report.append(f"       Hash: {check['hash']}")
                report.append(f"       Size: {check['size']} bytes")
                
            if results['mismatches']:
                report.append("  ⚠️  Issues Found:")
                for mismatch in results['mismatches']:
                    report.append(f"    ❌ {mismatch['file']}: {mismatch['issue']}")
                    for key, value in mismatch.items():
                        if key not in ['file', 'issue']:
                            report.append(f"       {key}: {value}")
        report.append("")
        
        # Recommendations
        if self.recommendations:
            report.append("📋 SYSTEM RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in self.recommendations:
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
                report.append(f"  {priority_icon} [{rec['priority'].upper()}] {rec['category']}")
                report.append(f"    Issue: {rec['issue']}")
                report.append(f"    Suggestion: {rec['suggestion']}")
                report.append("")
                
        report.append("=" * 80)
        return "\n".join(report)


class ComprehensiveDataTest:
    """Comprehensive E2E test with full data tracking"""
    
    def __init__(self):
        self.tracker = DataTracker()
        self.test_dir = None
        self.db_path = None
        self.config = None
        self.systems = {}
        
    def setup(self):
        """Initialize all real system components"""
        print("\n🔧 SETTING UP TEST ENVIRONMENT")
        print("-" * 40)
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp(prefix='usenet_data_test_')
        self.db_path = os.path.join(self.test_dir, 'test.db')
        print(f"✓ Test directory: {self.test_dir}")
        
        # Load configuration
        config_loader = SecureConfigLoader('/workspace/usenet_sync_config.json')
        self.config = config_loader.load_config()
        print("✓ Configuration loaded")
        
        # Initialize database with enhanced settings
        db_config = DatabaseConfig()
        db_config.path = self.db_path
        db_config.pool_size = 10
        db_config.timeout = 60.0
        db_config.check_same_thread = False
        db_config.enable_wal = True
        db_config.cache_size = 20000
        
        # Initialize enhanced database with write queue
        self.systems['enhanced_db'] = EnhancedDatabaseManager(db_config)
        self.systems['write_queue'] = DatabaseWriteQueue(self.systems['enhanced_db'])
        self.systems['write_queue'].start()
        print("✓ Enhanced database initialized with write queue")
        
        # Initialize production database
        self.systems['production_db'] = ProductionDatabaseManager(db_config)
        print("✓ Production database initialized")
        
        # Create schema
        self._create_schema()
        
        # Verify schema
        with self.systems['enhanced_db'].pool.get_connection() as conn:
            cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✓ Database schema created ({len(tables)} tables)")
            for table in tables:
                if table[0]:
                    print(f"  - {table[0].split('(')[0].replace('CREATE TABLE', '').strip()}")
        
        # Initialize security system
        self.systems['security'] = EnhancedSecuritySystem(self.systems['enhanced_db'])
        print("✓ Security system initialized")
        
        # Initialize NNTP client with real credentials
        nntp_config = self.config['servers'][0]
        self.systems['nntp'] = ProductionNNTPClient(
            host='news.newshosting.com',
            port=563,
            username='contemptx',
            password='S1983b1986#',
            use_ssl=True
        )
        print("✓ NNTP client initialized")
        
        # Test NNTP connection
        if not self._test_nntp_connection():
            self.tracker.add_recommendation(
                'connectivity',
                'NNTP connection test failed',
                'Check NNTP credentials and server configuration',
                'high'
            )
            
        # Initialize core systems
        self._initialize_core_systems()
        print("✓ All systems initialized")
        print("")
        
    def _create_schema(self):
        """Create complete database schema"""
        with self.systems['enhanced_db'].pool.get_connection() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    public_key BLOB,
                    private_key_encrypted BLOB,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP
                )
            """)
            
            # Folders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_unique_id TEXT UNIQUE NOT NULL,
                    folder_path TEXT NOT NULL,
                    display_name TEXT,
                    share_type TEXT DEFAULT 'private',
                    version INTEGER DEFAULT 1,
                    state TEXT DEFAULT 'active',
                    total_files INTEGER DEFAULT 0,
                    total_size INTEGER DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    private_key BLOB,
                    public_key BLOB,
                    keys_updated_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    file_hash TEXT,
                    size INTEGER,
                    hash TEXT,
                    version INTEGER DEFAULT 1,
                    modified_at TIMESTAMP,
                    change_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
                )
            """)
            
            # Segments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    segment_index INTEGER NOT NULL,
                    size INTEGER,
                    hash TEXT,
                    segment_hash TEXT,
                    offset INTEGER,
                    message_id TEXT,
                    subject TEXT,
                    internal_subject TEXT,
                    newsgroup TEXT,
                    uploaded_at TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(file_id)
                )
            """)
            
            # Shares table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shares (
                    share_id TEXT PRIMARY KEY,
                    folder_id INTEGER NOT NULL,
                    share_type TEXT NOT NULL,
                    access_string TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
                )
            """)
            
            conn.commit()
            
    def _initialize_core_systems(self):
        """Initialize all core system components"""
        # User management
        self.systems['user_mgr'] = UserManager(self.systems['enhanced_db'], self.systems['security'])
        self.systems['user_id'] = self.systems['user_mgr'].initialize("Test User")
        
        # Indexing systems
        self.systems['index_system'] = VersionedCoreIndexSystem(
            self.systems['enhanced_db'],
            self.systems['security'],
            self.config
        )
        self.systems['optimized_index'] = OptimizedIndexingSystem(
            self.systems['enhanced_db'],
            self.systems['security'],
            self.config
        )
        self.systems['binary_index'] = SimplifiedBinaryIndex("test_folder")
        
        # Upload systems
        self.systems['packing'] = SegmentPackingSystem(
            self.systems['enhanced_db'],
            self.config
        )
        self.systems['upload'] = EnhancedUploadSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.systems['packing'],
            self.config
        )
        self.systems['publishing'] = PublishingSystem(
            self.systems['enhanced_db'],
            self.systems['security'],
            self.systems['upload'],  # upload_system
            self.systems['nntp'],
            self.systems['index_system'],
            self.systems['binary_index'],
            self.config
        )
        
        # Download systems
        self.systems['retrieval'] = SegmentRetrievalSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.config
        )
        self.systems['download'] = EnhancedDownloadSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.systems['retrieval'],
            self.config
        )
        
        # Monitoring
        self.systems['monitoring'] = MonitoringSystem({'metrics_retention_hours': 24})
        
        # Share ID generator
        self.systems['share_gen'] = ShareIDGenerator()
        
    def _test_nntp_connection(self) -> bool:
        """Test NNTP connection with a simple post"""
        try:
            with self.systems['nntp'].connection_pool.get_connection() as conn:
                # Create test message
                test_msg_id = self.systems['nntp']._generate_message_id()
                test_message = f"""From: test@usenetsync.com
Newsgroups: alt.binaries.test
Subject: Connection Test {int(time.time())}
Message-ID: {test_msg_id}
Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}

Connection test successful at {datetime.now()}
""".encode('utf-8')
                
                response = conn.post(test_message)
                print(f"✓ NNTP connection verified: {response}")
                return True
        except Exception as e:
            print(f"⚠️  NNTP connection test failed: {e}")
            return False
            
    def create_test_files(self) -> List[Dict]:
        """Create test files with various types of content"""
        print("\n📝 CREATING TEST FILES")
        print("-" * 40)
        
        test_files = []
        test_folder = os.path.join(self.test_dir, 'test_data')
        os.makedirs(test_folder, exist_ok=True)
        
        # Text file
        text_content = b"This is a test text file for UsenetSync comprehensive testing.\n" * 100
        text_path = os.path.join(test_folder, 'test_document.txt')
        with open(text_path, 'wb') as f:
            f.write(text_content)
        text_hash = self.tracker.track_original_file(text_path, text_content, {'type': 'text'})
        test_files.append({'path': text_path, 'content': text_content, 'hash': text_hash})
        print(f"✓ Created text file: {os.path.basename(text_path)} ({len(text_content)} bytes)")
        
        # Binary file (simulated image)
        binary_content = secrets.token_bytes(50000)  # 50KB binary data
        binary_path = os.path.join(test_folder, 'test_image.jpg')
        with open(binary_path, 'wb') as f:
            f.write(binary_content)
        binary_hash = self.tracker.track_original_file(binary_path, binary_content, {'type': 'binary'})
        test_files.append({'path': binary_path, 'content': binary_content, 'hash': binary_hash})
        print(f"✓ Created binary file: {os.path.basename(binary_path)} ({len(binary_content)} bytes)")
        
        # JSON file
        json_data = {
            'test': 'data',
            'timestamp': datetime.now().isoformat(),
            'values': list(range(100))
        }
        json_content = json.dumps(json_data, indent=2).encode('utf-8')
        json_path = os.path.join(test_folder, 'test_data.json')
        with open(json_path, 'wb') as f:
            f.write(json_content)
        json_hash = self.tracker.track_original_file(json_path, json_content, {'type': 'json'})
        test_files.append({'path': json_path, 'content': json_content, 'hash': json_hash})
        print(f"✓ Created JSON file: {os.path.basename(json_path)} ({len(json_content)} bytes)")
        
        print(f"\nTotal test files created: {len(test_files)}")
        return test_files
        
    def test_indexing(self, test_files: List[Dict]) -> int:
        """Test file indexing with data tracking"""
        print("\n🗂️  TESTING INDEXING")
        print("-" * 40)
        
        folder_path = os.path.dirname(test_files[0]['path'])
        
        # Create folder in database
        with self.systems['enhanced_db'].pool.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO folders (folder_unique_id, folder_path, display_name, share_type)
                VALUES (?, ?, ?, ?)
            """, ('test_folder', folder_path, 'Test Folder', 'private'))
            folder_id = cursor.lastrowid
            conn.commit()
            
        print(f"✓ Created folder: ID={folder_id}, Path={folder_path}")
        
        # Index entire folder using optimized indexing system
        indexed_count = 0
        try:
            # Index entire folder
            result = self.systems['optimized_index'].index_folder(
                folder_path,
                str(folder_id),
                progress_callback=lambda p: print(f"    Indexing progress: {p:.1%}")
            )
            
            # Track indexed data for each file
            with self.systems['enhanced_db'].pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT file_id, filename, file_path, size, hash
                    FROM files
                    WHERE folder_id = ?
                """, (folder_id,))
                files = cursor.fetchall()
                
            for file_info in files:
                file_dict = {
                    'file_id': file_info[0],
                    'filename': file_info[1],
                    'file_path': file_info[2],
                    'size': file_info[3],
                    'hash': file_info[4]
                }
                self.tracker.track_indexed_file(file_info[0], folder_id, file_dict)
                indexed_count += 1
                print(f"  ✓ Indexed: {file_info[1]} (ID={file_info[0]}, Size={file_info[3]})")
                    
        except Exception as e:
            print(f"  ⚠️  Failed to index folder: {e}")
            self.tracker.add_recommendation(
                'indexing',
                f'Failed to index folder: {e}',
                'Review indexing error handling and file validation',
                'medium'
            )
                
        print(f"\nIndexing complete: {indexed_count}/{len(test_files)} files indexed")
        return folder_id
        
    def test_segment_packing(self, folder_id: int) -> List[Dict]:
        """Test segment packing with data tracking"""
        print("\n📦 TESTING SEGMENT PACKING")
        print("-" * 40)
        
        packed_files = []
        
        # Get files from database
        with self.systems['enhanced_db'].pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT file_id, filename, file_path, size, hash
                FROM files
                WHERE folder_id = ?
            """, (folder_id,))
            files = cursor.fetchall()
            
        for file_row in files:
            file_id, filename, filepath, size, file_hash = file_row
            print(f"\nPacking file: {filename}")
            
            try:
                # Read file content
                with open(filepath, 'rb') as f:
                    content = f.read()
                    
                # Create segments
                segments = self.systems['packing'].create_segments(
                    file_id=file_id,
                    file_data=content,
                    segment_size=10000  # 10KB segments for testing
                )
                
                print(f"  Created {len(segments)} segments")
                
                # Pack segments
                packed = self.systems['packing'].pack_segments(
                    segments,
                    compression='zlib',
                    redundancy_enabled=True,
                    redundancy_level=0.1
                )
                
                # Track packed segments
                for seg in packed:
                    segment_id = f"{file_id}_{seg.segment_index}"
                    self.tracker.track_segment(segment_id, {
                        'file_id': file_id,
                        'segment_index': seg.segment_index,
                        'size': seg.size,
                        'hash': seg.hash
                    })
                    
                packed_files.append({
                    'file_id': file_id,
                    'filename': filename,
                    'segments': packed
                })
                
                print(f"  ✓ Packed {len(packed)} segments with redundancy")
                
            except Exception as e:
                print(f"  ⚠️  Failed to pack {filename}: {e}")
                self.tracker.add_recommendation(
                    'packing',
                    f'Segment packing failed: {e}',
                    'Review segment size limits and memory usage',
                    'medium'
                )
                
        print(f"\nPacking complete: {len(packed_files)} files packed")
        return packed_files
        
    def test_upload_to_usenet(self, packed_files: List[Dict]) -> List[Dict]:
        """Test uploading to Usenet with detailed tracking"""
        print("\n📤 TESTING UPLOAD TO USENET")
        print("-" * 40)
        
        uploaded_data = []
        
        for file_data in packed_files:
            file_id = file_data['file_id']
            filename = file_data['filename']
            segments = file_data['segments']
            
            print(f"\nUploading: {filename} ({len(segments)} segments)")
            
            for i, segment in enumerate(segments):
                try:
                    # Generate unique identifiers
                    message_id = self.systems['nntp']._generate_message_id()
                    subject_pair = self.systems['security'].generate_subject_pair(
                        1,  # version
                        segment.segment_index
                    )
                    
                    # Prepare segment data
                    segment_data = segment.header + segment.data
                    
                    # Create NNTP message
                    headers = [
                        f"From: test@usenetsync.com",
                        f"Newsgroups: alt.binaries.test",
                        f"Subject: {subject_pair.usenet_subject}",
                        f"Message-ID: {message_id}",
                        f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}",
                        f"X-Newsreader: UsenetSync/1.0",
                        f"Content-Type: application/octet-stream",
                        f"Content-Transfer-Encoding: 8bit"
                    ]
                    
                    message = "\r\n".join(headers) + "\r\n\r\n"
                    message = message.encode('utf-8') + segment_data[:50000]  # Limit size for testing
                    
                    # Post to Usenet
                    with self.systems['nntp'].connection_pool.get_connection() as conn:
                        response = conn.post(message)
                        
                    # Extract actual message ID from response
                    actual_msg_id = response[1] if isinstance(response, tuple) else message_id
                    
                    # Track upload
                    self.tracker.track_upload(
                        actual_msg_id,
                        subject_pair.usenet_subject,
                        {
                            'file_id': file_id,
                            'filename': filename,
                            'segment_index': segment.segment_index,
                            'size': len(segment_data)
                        },
                        response
                    )
                    
                    # Store in database
                    with self.systems['enhanced_db'].pool.get_connection() as conn:
                        conn.execute("""
                            UPDATE segments
                            SET message_id = ?, subject = ?, internal_subject = ?, 
                                newsgroup = ?, uploaded_at = CURRENT_TIMESTAMP
                            WHERE file_id = ? AND segment_index = ?
                        """, (
                            actual_msg_id,
                            subject_pair.usenet_subject,
                            subject_pair.internal_subject,
                            'alt.binaries.test',
                            file_id,
                            segment.segment_index
                        ))
                        conn.commit()
                        
                    uploaded_data.append({
                        'file_id': file_id,
                        'filename': filename,
                        'segment_index': segment.segment_index,
                        'message_id': actual_msg_id,
                        'subject': subject_pair.usenet_subject
                    })
                    
                    print(f"  ✓ Segment {i+1}/{len(segments)}: {actual_msg_id[:30]}...")
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"  ⚠️  Failed segment {i+1}: {e}")
                    self.tracker.add_recommendation(
                        'upload',
                        f'Upload failed: {e}',
                        'Implement better retry logic and error recovery',
                        'high'
                    )
                    
        print(f"\nUpload complete: {len(uploaded_data)} segments uploaded")
        return uploaded_data
        
    def test_publishing(self, folder_id: int) -> Dict:
        """Test share publishing with tracking"""
        print("\n🔗 TESTING PUBLISHING")
        print("-" * 40)
        
        published_shares = {}
        
        # Test different share types
        share_types = [
            ('public', {}),
            ('private', {'authorized_users': [self.systems['user_id']]}),
            ('password', {'password': 'test_password_123'})
        ]
        
        for share_type, extra_params in share_types:
            print(f"\nPublishing {share_type} share...")
            
            try:
                result = self.systems['publishing'].publish_folder(
                    folder_id=folder_id,
                    share_type=share_type,
                    metadata={'test': 'share', 'type': share_type},
                    **extra_params
                )
                
                # Track published share
                self.tracker.track_share(result['share_id'], {
                    'share_type': share_type,
                    'folder_id': folder_id,
                    'access_string': result['access_string'],
                    'metadata': {'test': 'share', 'type': share_type}
                })
                
                published_shares[share_type] = result
                
                print(f"  ✓ Share ID: {result['share_id']}")
                print(f"  ✓ Access String: {result['access_string'][:50]}...")
                
            except Exception as e:
                print(f"  ⚠️  Failed to publish {share_type} share: {e}")
                self.tracker.add_recommendation(
                    'publishing',
                    f'Publishing failed for {share_type}: {e}',
                    'Review access control and share generation',
                    'medium'
                )
                
        print(f"\nPublishing complete: {len(published_shares)} shares created")
        return published_shares
        
    def test_retrieval(self, uploaded_data: List[Dict]) -> List[Dict]:
        """Test segment retrieval from Usenet"""
        print("\n📥 TESTING RETRIEVAL FROM USENET")
        print("-" * 40)
        
        retrieved_segments = []
        
        # Group by file
        files = {}
        for upload in uploaded_data:
            file_id = upload['file_id']
            if file_id not in files:
                files[file_id] = []
            files[file_id].append(upload)
            
        for file_id, segments in files.items():
            filename = segments[0]['filename']
            print(f"\nRetrieving: {filename} ({len(segments)} segments)")
            
            for seg_data in segments[:3]:  # Retrieve first 3 segments for testing
                try:
                    message_id = seg_data['message_id']
                    
                    # Retrieve using retrieval system
                    result = self.systems['retrieval'].retrieve_by_message_id(message_id)
                    
                    if result and result.data:
                        # Track retrieval
                        self.tracker.track_retrieval(
                            message_id,
                            result.data,
                            {
                                'segment_index': seg_data['segment_index'],
                                'file_id': file_id,
                                'filename': filename
                            }
                        )
                        
                        retrieved_segments.append({
                            'file_id': file_id,
                            'filename': filename,
                            'segment_index': seg_data['segment_index'],
                            'data': result.data,
                            'message_id': message_id
                        })
                        
                        print(f"  ✓ Retrieved segment {seg_data['segment_index']}: {len(result.data)} bytes")
                    else:
                        print(f"  ⚠️  No data retrieved for segment {seg_data['segment_index']}")
                        
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ⚠️  Failed to retrieve segment: {e}")
                    self.tracker.add_recommendation(
                        'retrieval',
                        f'Retrieval failed: {e}',
                        'Implement fallback retrieval methods',
                        'high'
                    )
                    
        print(f"\nRetrieval complete: {len(retrieved_segments)} segments retrieved")
        return retrieved_segments
        
    def test_download(self, published_shares: Dict) -> List[str]:
        """Test downloading via share access strings"""
        print("\n💾 TESTING DOWNLOAD")
        print("-" * 40)
        
        downloaded_files = []
        download_dir = os.path.join(self.test_dir, 'downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        for share_type, share_data in published_shares.items():
            print(f"\nDownloading {share_type} share...")
            
            try:
                access_string = share_data['access_string']
                
                # Prepare download parameters
                params = {'output_dir': download_dir}
                if share_type == 'password':
                    params['password'] = 'test_password_123'
                    
                # Download using download system
                result = self.systems['download'].download_from_access_string(
                    access_string,
                    **params
                )
                
                # Track downloaded files
                if result and 'files' in result:
                    for file_info in result['files']:
                        filepath = file_info['path']
                        if os.path.exists(filepath):
                            with open(filepath, 'rb') as f:
                                content = f.read()
                            file_hash = self.tracker.track_download(filepath, content, {
                                'share_type': share_type,
                                'share_id': share_data['share_id']
                            })
                            downloaded_files.append(filepath)
                            print(f"  ✓ Downloaded: {os.path.basename(filepath)} ({len(content)} bytes)")
                            
            except Exception as e:
                print(f"  ⚠️  Failed to download {share_type} share: {e}")
                self.tracker.add_recommendation(
                    'download',
                    f'Download failed for {share_type}: {e}',
                    'Improve error recovery and resume capability',
                    'medium'
                )
                
        print(f"\nDownload complete: {len(downloaded_files)} files downloaded")
        return downloaded_files
        
    def verify_integrity(self):
        """Verify data integrity between upload and download"""
        print("\n✅ VERIFYING DATA INTEGRITY")
        print("-" * 40)
        
        results = self.tracker.verify_integrity()
        
        if results['success']:
            print("✅ ALL DATA VERIFIED SUCCESSFULLY!")
            for check in results['checks']:
                print(f"  ✓ {check['file']}: Hash={check['hash'][:16]}... Size={check['size']}")
        else:
            print("❌ DATA INTEGRITY CHECK FAILED!")
            for mismatch in results['mismatches']:
                print(f"  ✗ {mismatch['file']}: {mismatch['issue']}")
                
        return results['success']
        
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 CLEANING UP")
        print("-" * 40)
        
        try:
            # Stop write queue
            if 'write_queue' in self.systems:
                self.systems['write_queue'].stop()
                print("✓ Write queue stopped")
                
            # Close database connections
            if 'enhanced_db' in self.systems:
                # EnhancedDatabaseManager doesn't have close method, but pool does
                if hasattr(self.systems['enhanced_db'], 'pool'):
                    self.systems['enhanced_db'].pool.close_all()
                print("✓ Database connections closed")
                
            # Remove test directory
            if self.test_dir and os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                print(f"✓ Test directory removed: {self.test_dir}")
                
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
            
    def run(self):
        """Run comprehensive test with full data tracking"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE USENETSYNC DATA TRACKING TEST")
        print("=" * 80)
        
        try:
            # Setup
            self.setup()
            
            # Create test files
            test_files = self.create_test_files()
            
            # Test indexing
            folder_id = self.test_indexing(test_files)
            
            # Test segment packing
            packed_files = self.test_segment_packing(folder_id)
            
            # Test upload to Usenet
            uploaded_data = self.test_upload_to_usenet(packed_files)
            
            # Test publishing
            published_shares = self.test_publishing(folder_id)
            
            # Test retrieval from Usenet
            retrieved_segments = self.test_retrieval(uploaded_data)
            
            # Test download via shares
            downloaded_files = self.test_download(published_shares)
            
            # Verify data integrity
            integrity_verified = self.verify_integrity()
            
            # Generate and print report
            report = self.tracker.generate_report()
            print("\n" + report)
            
            # Overall result
            print("\n" + "=" * 80)
            if integrity_verified:
                print("🎉 TEST PASSED: All data verified successfully!")
            else:
                print("❌ TEST FAILED: Data integrity check failed")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
            self.tracker.add_recommendation(
                'system',
                f'Test execution failed: {e}',
                'Review error handling and system resilience',
                'high'
            )
            
        finally:
            self.cleanup()
            
            # Save recommendations to file
            if self.tracker.recommendations:
                rec_file = '/workspace/test_recommendations.json'
                with open(rec_file, 'w') as f:
                    json.dump(self.tracker.recommendations, f, indent=2)
                print(f"\n📋 Recommendations saved to: {rec_file}")


if __name__ == "__main__":
    test = ComprehensiveDataTest()
    test.run()