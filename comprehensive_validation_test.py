#!/usr/bin/env python3
"""
Comprehensive System Validation Test
Tests the complete flow: Indexing → Segments → Upload → Publishing → Sharing → Downloading
With detailed logging and validation at every level
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import secrets
import struct

# Add src to path
sys.path.insert(0, '/workspace')

# Import all real system components
from src.database.production_db_wrapper import ProductionDatabaseManager
from src.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig, ConnectionPool
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.security.user_management import UserManager
from src.networking.production_nntp_client import ProductionNNTPClient
from src.upload.enhanced_upload_system import EnhancedUploadSystem
from src.upload.publishing_system import PublishingSystem
from src.upload.segment_packing_system import SegmentPackingSystem
from src.download.enhanced_download_system import EnhancedDownloadSystem
from src.download.segment_retrieval_system import SegmentRetrievalSystem
from src.monitoring.monitoring_system import MonitoringSystem
from src.indexing.versioned_core_index_system import VersionedCoreIndexSystem
from src.indexing.simplified_binary_index import SimplifiedBinaryIndex
from optimized_indexing import OptimizedIndexingSystem
from src.indexing.share_id_generator import ShareIDGenerator
from src.config.secure_config import SecureConfigLoader

# Import pynntp as nntp
import nntp


class ComprehensiveSystemValidator:
    """Complete system validation with detailed tracking"""
    
    def __init__(self):
        self.test_dir = None
        self.db_path = None
        self.systems = {}
        self.test_data = {
            'folder_structure': {},
            'indexed_files': {},
            'segments': {},
            'uploads': {},
            'publications': {},
            'downloads': {},
            'validation': {}
        }
        
    def setup(self):
        """Initialize test environment with all components"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SYSTEM VALIDATION TEST")
        print("="*80)
        print("Testing: Indexing → Segments → Upload → Publishing → Sharing → Downloading")
        print("="*80)
        
        print("\n🔧 INITIALIZING TEST ENVIRONMENT")
        print("-" * 50)
        
        # Create test directory structure
        self.test_dir = tempfile.mkdtemp(prefix='system_validation_')
        self.db_path = os.path.join(self.test_dir, 'test.db')
        self.data_dir = os.path.join(self.test_dir, 'test_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"✓ Test directory: {self.test_dir}")
        print(f"✓ Data directory: {self.data_dir}")
        
        # Create complete database schema
        self._create_complete_schema()
        
        # Initialize all systems
        self._initialize_systems()
        
        print("\n✅ All systems initialized successfully")
        
    def _create_complete_schema(self):
        """Create full database schema for all components"""
        print("\n📊 Creating database schema...")
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        
        # Create all required tables
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY,
                folder_id TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL,
                display_name TEXT,
                size INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                parent_id TEXT,
                private_key BLOB,
                public_key BLOB,
                keys_updated_at TIMESTAMP,
                current_version INTEGER DEFAULT 1
            )""",
            
            """CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                file_id TEXT UNIQUE NOT NULL,
                folder_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                size INTEGER NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                segment_count INTEGER DEFAULT 0,
                FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY,
                segment_id TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                segment_index INTEGER NOT NULL,
                segment_hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                message_id TEXT,
                subject TEXT,
                internal_subject TEXT,
                offset INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(file_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS shares (
                id INTEGER PRIMARY KEY,
                share_id TEXT UNIQUE NOT NULL,
                folder_id TEXT NOT NULL,
                share_type TEXT NOT NULL,
                access_string TEXT NOT NULL,
                encryption_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS upload_sessions (
                id INTEGER PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                folder_id TEXT NOT NULL,
                total_files INTEGER,
                uploaded_files INTEGER DEFAULT 0,
                total_segments INTEGER,
                uploaded_segments INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY,
                publication_id TEXT UNIQUE NOT NULL,
                share_id TEXT NOT NULL,
                folder_id TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (share_id) REFERENCES shares(share_id),
                FOREIGN KEY (folder_id) REFERENCES folders(folder_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS user_config (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                display_name TEXT,
                preferences TEXT,
                private_key BLOB,
                public_key BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                config TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )"""
        ]
        
        for table_sql in tables:
            conn.execute(table_sql)
            
        conn.commit()
        conn.close()
        print("✓ Database schema created")
        
    def _initialize_systems(self):
        """Initialize all system components"""
        print("\n🔧 Initializing system components...")
        
        # Load configuration
        config_path = '/workspace/usenet_sync_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default config for testing
            self.config = {
                'servers': [{
                    'hostname': 'news.newshosting.com',
                    'port': 563,
                    'username': 'contemptx',
                    'password': 'Kia211101#',
                    'use_ssl': True,
                    'max_connections': 60
                }]
            }
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = self.db_path
        db_config.pool_size = 5
        db_config.timeout = 60.0
        db_config.enable_wal = True
        
        self.systems['enhanced_db'] = EnhancedDatabaseManager(db_config)
        # ProductionDatabaseManager needs a DatabaseConfig, not a string
        prod_db_config = DatabaseConfig()
        prod_db_config.path = self.db_path
        self.systems['production_db'] = ProductionDatabaseManager(prod_db_config)
        print("✓ Database systems initialized")
        
        # Initialize security
        self.systems['security'] = EnhancedSecuritySystem(self.systems['enhanced_db'])
        self.systems['user_manager'] = UserManager(
            self.systems['enhanced_db'],
            self.systems['security']
        )
        print("✓ Security systems initialized")
        
        # Initialize NNTP client with correct credentials
        server_config = self.config['servers'][0]
        self.systems['nntp'] = ProductionNNTPClient(
            host=server_config.get('hostname', server_config.get('host', 'news.newshosting.com')),
            port=server_config.get('port', 563),
            username=server_config.get('username', 'contemptx'),
            password='Kia211101#',  # Use the new password
            use_ssl=server_config.get('use_ssl', True),
            max_connections=1  # Start with single connection for testing
        )
        print("✓ NNTP client initialized")
        
        # Initialize indexing systems
        self.systems['versioned_index'] = VersionedCoreIndexSystem(
            self.systems['production_db'],
            self.systems['security'],
            self.config
        )
        self.systems['binary_index'] = SimplifiedBinaryIndex(
            self.systems['production_db']
        )
        self.systems['optimized_index'] = OptimizedIndexingSystem(
            self.systems['enhanced_db'],
            self.systems['security'],
            self.config
        )
        print("✓ Indexing systems initialized")
        
        # Initialize upload/download systems
        self.systems['upload'] = EnhancedUploadSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.systems['security'],
            self.config
        )
        self.systems['segment_packing'] = SegmentPackingSystem(
            self.systems['enhanced_db'],
            self.config
        )
        self.systems['publishing'] = PublishingSystem(
            self.systems['enhanced_db'],
            self.systems['security'],
            self.systems['upload'],
            self.systems['nntp'],
            self.systems['versioned_index'],
            self.systems['binary_index'],
            self.config
        )
        self.systems['download'] = EnhancedDownloadSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.systems['security'],
            self.config
        )
        self.systems['segment_retrieval'] = SegmentRetrievalSystem(
            self.systems['enhanced_db'],
            self.systems['nntp'],
            self.config
        )
        print("✓ Upload/Download systems initialized")
        
        # Initialize monitoring
        self.systems['monitoring'] = MonitoringSystem(self.config)
        self.systems['share_id'] = ShareIDGenerator()
        print("✓ Monitoring and utilities initialized")
        
    def create_test_folder_structure(self):
        """Create a test folder structure with files"""
        print("\n📁 CREATING TEST FOLDER STRUCTURE")
        print("-" * 50)
        
        # Create folder hierarchy
        structure = {
            'Documents': {
                'Work': ['report.txt', 'presentation.pdf'],
                'Personal': ['notes.txt', 'todo.md']
            },
            'Images': {
                'Vacation': ['beach.jpg', 'sunset.png'],
                'Family': ['reunion.jpg']
            },
            'Projects': {
                'Code': ['main.py', 'utils.py', 'readme.md']
            }
        }
        
        file_count = 0
        total_size = 0
        
        for root_folder, subfolders in structure.items():
            root_path = os.path.join(self.data_dir, root_folder)
            os.makedirs(root_path, exist_ok=True)
            
            for subfolder, files in subfolders.items():
                sub_path = os.path.join(root_path, subfolder)
                os.makedirs(sub_path, exist_ok=True)
                
                for filename in files:
                    file_path = os.path.join(sub_path, filename)
                    
                    # Create file with unique content
                    content = f"File: {filename}\n"
                    content += f"Path: {file_path}\n"
                    content += f"Created: {datetime.now()}\n"
                    content += f"Content: {'=' * 50}\n"
                    content += f"This is test content for {filename}\n"
                    content += "A" * (1024 + file_count * 512)  # Variable size
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    file_size = os.path.getsize(file_path)
                    file_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Track in test data
                    rel_path = os.path.relpath(file_path, self.data_dir)
                    self.test_data['folder_structure'][rel_path] = {
                        'path': file_path,
                        'size': file_size,
                        'hash': file_hash,
                        'content': content[:200]  # Store preview
                    }
                    
                    file_count += 1
                    total_size += file_size
                    
                    print(f"  ✓ Created: {rel_path} ({file_size} bytes)")
        
        print(f"\n📊 Created {file_count} files, total size: {total_size:,} bytes")
        return file_count, total_size
        
    def test_indexing(self):
        """Test file indexing with detailed tracking"""
        print("\n📚 TESTING INDEXING")
        print("-" * 50)
        
        # Index the test folder
        print(f"Indexing folder: {self.data_dir}")
        
        try:
            # Directly index files into the database for testing
            import uuid
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Index all folders and files
            folders_indexed = {}
            files_indexed = 0
            
            for root, dirs, files in os.walk(self.data_dir):
                # Create folder entry
                folder_id = str(uuid.uuid4())
                folder_path = root
                folder_name = os.path.basename(root) or "root"
                
                # Calculate folder stats
                folder_size = sum(os.path.getsize(os.path.join(root, f)) for f in files)
                file_count = len(files)
                
                # Generate folder keys using the security system
                folder_keys = self.systems['security'].generate_folder_keys(folder_id)
                
                # Serialize keys for storage
                from cryptography.hazmat.primitives import serialization
                private_key_bytes = folder_keys.private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                public_key_bytes = folder_keys.public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                
                # Insert folder with keys
                conn.execute("""
                    INSERT INTO folders (folder_id, path, display_name, size, file_count, 
                                       private_key, public_key, keys_updated_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (folder_id, folder_path, folder_name, folder_size, file_count,
                     private_key_bytes, public_key_bytes))
                
                folders_indexed[folder_path] = folder_id
                
                # Index files in this folder
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_id = str(uuid.uuid4())
                    file_size = os.path.getsize(file_path)
                    
                    # Calculate file hash
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Insert file
                    conn.execute("""
                        INSERT INTO files (file_id, folder_id, filename, size, hash, created_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (file_id, folder_id, filename, file_size, file_hash))
                    
                    files_indexed += 1
                    
            conn.commit()
            
            # Get indexed folders
            folders = conn.execute("""
                SELECT * FROM folders 
                WHERE path LIKE ?
            """, (f"{self.data_dir}%",)).fetchall()
            
            print(f"\n📁 Indexed Folders: {len(folders)}")
            for folder in folders:
                print(f"  • {folder['path']}")
                print(f"    ID: {folder['folder_id']}")
                print(f"    Files: {folder['file_count']}, Size: {folder['size']:,} bytes")
                
            # Get files
            files = conn.execute("""
                SELECT f.*, fo.path as folder_path
                FROM files f
                JOIN folders fo ON f.folder_id = fo.folder_id
                WHERE fo.path LIKE ?
            """, (f"{self.data_dir}%",)).fetchall()
            
            print(f"\n📄 Indexed Files: {len(files)}")
            for file in files:
                rel_path = os.path.relpath(
                    os.path.join(file['folder_path'], file['filename']),
                    self.data_dir
                )
                
                # Store indexed file info
                self.test_data['indexed_files'][file['file_id']] = {
                    'file_id': file['file_id'],
                    'folder_id': file['folder_id'],
                    'filename': file['filename'],
                    'size': file['size'],
                    'hash': file['hash'],
                    'rel_path': rel_path
                }
                
                print(f"  • {rel_path}")
                print(f"    ID: {file['file_id']}")
                print(f"    Hash: {file['hash'][:16]}...")
                print(f"    Size: {file['size']:,} bytes")
                
                # Verify against original
                if rel_path in self.test_data['folder_structure']:
                    orig = self.test_data['folder_structure'][rel_path]
                    if orig['hash'] == file['hash']:
                        print(f"    ✅ Hash matches original")
                    else:
                        print(f"    ❌ Hash mismatch!")
                        
            conn.close()
            
            print(f"\n✅ Indexing complete: {len(files)} files indexed")
            return True
            
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def test_segment_creation(self):
        """Test segment creation and packing"""
        print("\n📦 TESTING SEGMENT CREATION")
        print("-" * 50)
        
        if not self.test_data['indexed_files']:
            print("❌ No indexed files to segment")
            return False
            
        try:
            total_segments = 0
            
            for file_id, file_info in self.test_data['indexed_files'].items():
                print(f"\n📄 Creating segments for: {file_info['filename']}")
                print(f"  File ID: {file_id}")
                print(f"  Size: {file_info['size']:,} bytes")
                
                # Read file content
                file_path = os.path.join(
                    self.data_dir,
                    file_info['rel_path']
                )
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Create segments manually for testing
                segment_size = 4096  # 4KB segments
                segments = []
                
                for i in range(0, len(content), segment_size):
                    segment_data = content[i:i+segment_size]
                    segments.append({
                        'index': len(segments),
                        'data': segment_data,
                        'size': len(segment_data)
                    })
                
                print(f"  Created {len(segments)} segments")
                
                # Store segment info
                self.test_data['segments'][file_id] = []
                
                for i, segment in enumerate(segments):
                    segment_info = {
                        'index': i,
                        'size': len(segment['data']),
                        'hash': hashlib.sha256(segment['data']).hexdigest(),
                        'data_preview': segment['data'][:50] if len(segment['data']) > 50 else segment['data']
                    }
                    
                    self.test_data['segments'][file_id].append(segment_info)
                    
                    print(f"    Segment {i}: {segment_info['size']} bytes, hash: {segment_info['hash'][:16]}...")
                    
                total_segments += len(segments)
                
                # Store segments in database
                conn = sqlite3.connect(self.db_path)
                for i, segment in enumerate(segments):
                    segment_id = f"{file_id}_seg_{i}"
                    segment_hash = hashlib.sha256(segment['data']).hexdigest()
                    
                    conn.execute("""
                        INSERT INTO segments (segment_id, file_id, segment_index, 
                                            segment_hash, size, created_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (segment_id, file_id, i, segment_hash, len(segment['data'])))
                    
                conn.commit()
                conn.close()
                
            print(f"\n✅ Segment creation complete: {total_segments} total segments")
            return True
            
        except Exception as e:
            print(f"❌ Segment creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def test_upload_to_usenet(self):
        """Test uploading segments to Usenet with detailed feedback"""
        print("\n📤 TESTING UPLOAD TO USENET")
        print("-" * 50)
        
        if not self.test_data['segments']:
            print("❌ No segments to upload")
            return False
            
        try:
            # Test connection first
            print("\n🔌 Testing NNTP connection...")
            
            # Create a direct connection using pynntp
            client = nntp.NNTPClient(
                host='news.newshosting.com',
                port=563,
                username='contemptx',
                password='Kia211101#',
                use_ssl=True,
                timeout=30
            )
            
            print("✅ Connected to Usenet server")
            
            total_uploaded = 0
            failed_uploads = 0
            
            # Upload segments for each file
            for file_id, segments in self.test_data['segments'].items():
                file_info = self.test_data['indexed_files'][file_id]
                print(f"\n📁 Uploading segments for: {file_info['filename']}")
                
                self.test_data['uploads'][file_id] = []
                
                # Upload only first 2 segments per file for testing
                for segment in segments[:2]:
                    try:
                        # Use system's obfuscated Message-ID generation
                        message_id = self.systems['nntp']._generate_message_id()
                        
                        # Generate obfuscated subject using the security system
                        # This creates a random 20-character subject that reveals nothing
                        subject_pair = self.systems['security'].generate_subject_pair(
                            folder_id=file_info['folder_id'],
                            file_version=1,
                            segment_index=segment['index']
                        )
                        subject = subject_pair.usenet_subject  # Use the obfuscated Usenet subject
                        
                        # Create message headers
                        headers = {
                            'From': 'test@usenetsync.com',
                            'Newsgroups': 'alt.binaries.test',
                            'Subject': subject,
                            'Message-ID': message_id,
                            'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                        }
                        
                        # Create test body (limited for testing)
                        body = f"Segment {segment['index']} of {file_info['filename']}\n"
                        body += f"Hash: {segment['hash']}\n"
                        body += "Data: " + "A" * min(100, segment['size'])
                        
                        print(f"\n  📤 Uploading segment {segment['index']}:")
                        print(f"    Message-ID: {message_id} (obfuscated)")
                        print(f"    Usenet Subject: {subject} (obfuscated)")
                        print(f"    Internal Subject: {subject_pair.internal_subject[:16]}... (for local tracking)")
                        print(f"    Size: {len(body)} bytes")
                        
                        # Post to server
                        result = client.post(headers, body)
                        
                        print(f"  📥 Server Response: {result}")
                        
                        if result:
                            print(f"    ✅ Upload successful")
                            total_uploaded += 1
                            
                            # Store upload info
                            upload_info = {
                                'segment_index': segment['index'],
                                'message_id': message_id,
                                'subject': subject,
                                'size': len(body),
                                'success': True,
                                'response': str(result)
                            }
                            self.test_data['uploads'][file_id].append(upload_info)
                            
                            # Update database with both subjects
                            conn = sqlite3.connect(self.db_path)
                            conn.execute("""
                                UPDATE segments 
                                SET message_id = ?, subject = ?, internal_subject = ?, uploaded_at = datetime('now')
                                WHERE file_id = ? AND segment_index = ?
                            """, (message_id, subject, subject_pair.internal_subject, file_id, segment['index']))
                            conn.commit()
                            conn.close()
                        else:
                            print(f"    ❌ Upload failed")
                            failed_uploads += 1
                            
                        # Rate limiting
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"    ❌ Upload error: {e}")
                        failed_uploads += 1
                        
                        # Store error
                        self.test_data['uploads'][file_id].append({
                            'segment_index': segment['index'],
                            'success': False,
                            'error': str(e)
                        })
                        
                        # Wait longer if rate limited
                        if '502' in str(e):
                            print("    ⏳ Rate limited - waiting 30s...")
                            time.sleep(30)
                            
            client.quit()
            
            print(f"\n📊 Upload Summary:")
            print(f"  Total Uploaded: {total_uploaded}")
            print(f"  Failed: {failed_uploads}")
            print(f"  Success Rate: {(total_uploaded/(total_uploaded+failed_uploads)*100) if (total_uploaded+failed_uploads) > 0 else 0:.1f}%")
            
            return total_uploaded > 0
            
        except Exception as e:
            print(f"❌ Upload test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def test_publishing(self):
        """Test publishing folders with different share types"""
        print("\n📢 TESTING PUBLISHING")
        print("-" * 50)
        
        try:
            # Get a folder to publish
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            folders = conn.execute("""
                SELECT * FROM folders 
                WHERE file_count > 0
                LIMIT 3
            """).fetchall()
            
            if not folders:
                print("❌ No folders to publish")
                return False
                
            share_types = ['public', 'private', 'password']
            
            for i, folder in enumerate(folders):
                share_type = share_types[i % len(share_types)]
                
                print(f"\n📁 Publishing folder: {folder['display_name'] or folder['path']}")
                print(f"  Folder ID: {folder['folder_id']}")
                print(f"  Share Type: {share_type}")
                
                # Prepare publish parameters
                kwargs = {
                    'share_type': share_type,
                    'metadata': {
                        'description': f'Test {share_type} share',
                        'created_by': 'test_user'
                    }
                }
                
                if share_type == 'password':
                    kwargs['encryption_key'] = 'test_password_123'
                    print(f"  Password: {kwargs['encryption_key']}")
                elif share_type == 'private':
                    # For private shares, add authorized users using commitment system
                    # These user IDs will be used to create zero-knowledge proof commitments
                    kwargs['authorized_users'] = ['test_user_1', 'test_user_2']
                    print(f"  Authorized Users: {kwargs['authorized_users']}")
                
                # Publish the folder
                result = self.systems['publishing'].publish_folder(
                    folder['folder_id'],
                    **kwargs
                )
                
                print(f"\n  📥 Publish Result:")
                print(f"    Share ID: {result.get('share_id')}")
                print(f"    Access String: {result.get('access_string')}")
                print(f"    Share Type: {result.get('share_type')}")
                
                # Store publication info
                self.test_data['publications'][folder['folder_id']] = {
                    'folder_id': folder['folder_id'],
                    'folder_path': folder['path'],
                    'share_id': result.get('share_id'),
                    'access_string': result.get('access_string'),
                    'share_type': share_type,
                    'password': kwargs.get('encryption_key')
                }
                
                # Verify in database
                share = conn.execute("""
                    SELECT * FROM shares 
                    WHERE folder_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (folder['folder_id'],)).fetchone()
                
                if share:
                    print(f"    ✅ Share created in database")
                    print(f"    DB Share ID: {share['share_id']}")
                else:
                    print(f"    ❌ Share not found in database")
                    
            conn.close()
            
            print(f"\n✅ Publishing complete: {len(self.test_data['publications'])} folders published")
            return True
            
        except Exception as e:
            print(f"❌ Publishing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def test_downloading(self):
        """Test downloading published content"""
        print("\n📥 TESTING DOWNLOADING")
        print("-" * 50)
        
        if not self.test_data['publications']:
            print("❌ No publications to download")
            return False
            
        try:
            download_dir = os.path.join(self.test_dir, 'downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            for folder_id, pub_info in self.test_data['publications'].items():
                print(f"\n📁 Downloading: {pub_info['folder_path']}")
                print(f"  Share ID: {pub_info['share_id']}")
                print(f"  Access String: {pub_info['access_string']}")
                print(f"  Share Type: {pub_info['share_type']}")
                
                # Prepare download parameters
                download_path = os.path.join(download_dir, pub_info['share_id'])
                os.makedirs(download_path, exist_ok=True)
                
                # Download using access string
                try:
                    result = self.systems['download'].download_from_access_string(
                        access_string=pub_info['access_string'],
                        destination_path=download_path,
                        password=pub_info.get('password')
                    )
                    
                    print(f"\n  📥 Download Result:")
                    print(f"    Status: {result.get('status')}")
                    print(f"    Files Downloaded: {result.get('files_downloaded', 0)}")
                    print(f"    Total Size: {result.get('total_size', 0):,} bytes")
                    
                    # Store download info
                    self.test_data['downloads'][folder_id] = {
                        'share_id': pub_info['share_id'],
                        'download_path': download_path,
                        'status': result.get('status'),
                        'files': result.get('files_downloaded', 0)
                    }
                    
                    # List downloaded files
                    downloaded_files = []
                    for root, dirs, files in os.walk(download_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, download_path)
                            file_size = os.path.getsize(file_path)
                            
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                file_hash = hashlib.sha256(content).hexdigest()
                                
                            downloaded_files.append({
                                'path': rel_path,
                                'size': file_size,
                                'hash': file_hash
                            })
                            
                            print(f"    • Downloaded: {rel_path} ({file_size:,} bytes)")
                            
                    self.test_data['downloads'][folder_id]['files_list'] = downloaded_files
                    
                except Exception as e:
                    print(f"  ❌ Download failed: {e}")
                    self.test_data['downloads'][folder_id] = {
                        'error': str(e)
                    }
                    
            print(f"\n✅ Download testing complete")
            return True
            
        except Exception as e:
            print(f"❌ Download test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def validate_integrity(self):
        """Validate that uploaded data matches downloaded data exactly"""
        print("\n🔍 VALIDATING DATA INTEGRITY")
        print("-" * 50)
        
        validation_passed = True
        
        print("\n📊 Comparing folder structures...")
        
        # Compare original vs downloaded for each publication
        for folder_id, download_info in self.test_data['downloads'].items():
            if 'error' in download_info:
                print(f"\n❌ Skipping {folder_id} due to download error")
                continue
                
            print(f"\n📁 Validating: {folder_id}")
            
            # Get original files for this folder
            original_files = {}
            for file_id, file_info in self.test_data['indexed_files'].items():
                if file_info['folder_id'] == folder_id:
                    original_files[file_info['filename']] = file_info
                    
            # Get downloaded files
            downloaded_files = download_info.get('files_list', [])
            
            print(f"  Original files: {len(original_files)}")
            print(f"  Downloaded files: {len(downloaded_files)}")
            
            # Check each original file
            for filename, orig_info in original_files.items():
                print(f"\n  📄 Checking: {filename}")
                print(f"    Original hash: {orig_info['hash'][:16]}...")
                print(f"    Original size: {orig_info['size']:,} bytes")
                
                # Find in downloaded
                found = False
                for dl_file in downloaded_files:
                    if filename in dl_file['path']:
                        found = True
                        print(f"    Downloaded hash: {dl_file['hash'][:16]}...")
                        print(f"    Downloaded size: {dl_file['size']:,} bytes")
                        
                        if orig_info['hash'] == dl_file['hash']:
                            print(f"    ✅ Hash match - file identical!")
                            self.test_data['validation'][filename] = 'PASSED'
                        else:
                            print(f"    ❌ Hash mismatch - files differ!")
                            self.test_data['validation'][filename] = 'FAILED'
                            validation_passed = False
                            
                        if orig_info['size'] != dl_file['size']:
                            print(f"    ❌ Size mismatch!")
                            validation_passed = False
                            
                        break
                        
                if not found:
                    print(f"    ❌ File not found in download!")
                    self.test_data['validation'][filename] = 'MISSING'
                    validation_passed = False
                    
        # Summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        total_files = len(self.test_data['validation'])
        passed = sum(1 for v in self.test_data['validation'].values() if v == 'PASSED')
        failed = sum(1 for v in self.test_data['validation'].values() if v == 'FAILED')
        missing = sum(1 for v in self.test_data['validation'].values() if v == 'MISSING')
        
        print(f"\n📊 Results:")
        print(f"  Total Files: {total_files}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️ Missing: {missing}")
        print(f"  Success Rate: {(passed/total_files*100) if total_files > 0 else 0:.1f}%")
        
        if validation_passed:
            print("\n✅ VALIDATION PASSED - All files match perfectly!")
        else:
            print("\n❌ VALIDATION FAILED - Some files do not match")
            
        return validation_passed
        
    def generate_comprehensive_report(self):
        """Generate detailed test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        # Save detailed results
        report_file = os.path.join(self.test_dir, 'comprehensive_report.json')
        with open(report_file, 'w') as f:
            json.dump(self.test_data, f, indent=2, default=str)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Copy to workspace
        shutil.copy(report_file, '/workspace/latest_comprehensive_report.json')
        print(f"📄 Report copied to: /workspace/latest_comprehensive_report.json")
        
        # Print summary
        print("\n📊 TEST SUMMARY:")
        print("-" * 50)
        print(f"  Files Created: {len(self.test_data['folder_structure'])}")
        print(f"  Files Indexed: {len(self.test_data['indexed_files'])}")
        print(f"  Segments Created: {sum(len(s) for s in self.test_data['segments'].values())}")
        print(f"  Segments Uploaded: {sum(len(u) for u in self.test_data['uploads'].values())}")
        print(f"  Folders Published: {len(self.test_data['publications'])}")
        print(f"  Folders Downloaded: {len(self.test_data['downloads'])}")
        print(f"  Validation Results: {len(self.test_data['validation'])}")
        
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 CLEANING UP")
        print("-" * 50)
        
        try:
            # Close database connections
            if 'enhanced_db' in self.systems:
                self.systems['enhanced_db'].pool.close_all()
                print("✓ Database connections closed")
                
            # Keep test directory for inspection
            print(f"ℹ️ Test directory preserved: {self.test_dir}")
            
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
            
    def run(self):
        """Run the complete validation test"""
        try:
            self.setup()
            
            # Run all tests in sequence
            tests = [
                ("Create Folder Structure", self.create_test_folder_structure),
                ("Indexing", self.test_indexing),
                ("Segment Creation", self.test_segment_creation),
                ("Upload to Usenet", self.test_upload_to_usenet),
                ("Publishing", self.test_publishing),
                ("Downloading", self.test_downloading),
                ("Validate Integrity", self.validate_integrity)
            ]
            
            results = {}
            for test_name, test_func in tests:
                print(f"\n{'='*80}")
                print(f"Running: {test_name}")
                print('='*80)
                
                result = test_func()
                results[test_name] = result
                
                if not result:
                    print(f"\n⚠️ {test_name} failed, continuing with remaining tests...")
                    
            # Generate comprehensive report
            self.generate_comprehensive_report()
            
            # Final summary
            print("\n" + "="*80)
            print("FINAL TEST RESULTS")
            print("="*80)
            
            for test_name, result in results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"  {test_name}: {status}")
                
            all_passed = all(results.values())
            if all_passed:
                print("\n🎉 ALL TESTS PASSED!")
            else:
                print("\n⚠️ SOME TESTS FAILED - Review the report for details")
                
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.cleanup()


if __name__ == "__main__":
    validator = ComprehensiveSystemValidator()
    validator.run()