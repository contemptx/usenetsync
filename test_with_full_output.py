#!/usr/bin/env python3
"""
Complete System Test with FULL Data Output
Shows ALL responses, data, and details at every step
"""

import os
import sys
import time
import uuid
import json
import hashlib
import secrets
import base64
import traceback
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, '/workspace')

from src.config.secure_config import SecureConfigLoader
from src.indexing.share_id_generator import ShareIDGenerator


class DetailedSystemTest:
    """Test with complete data capture and display"""
    
    def __init__(self):
        self.test_dir = Path("/workspace/detailed_test")
        self.test_dir.mkdir(exist_ok=True)
        self.log_file = open(self.test_dir / "full_test_log.txt", "w")
        self.data_file = open(self.test_dir / "test_data.json", "w")
        self.all_data = {
            "test_start": datetime.now().isoformat(),
            "configuration": {},
            "database": {},
            "files": {},
            "segments": {},
            "shares": {},
            "uploads": {},
            "downloads": {},
            "responses": []
        }
        
    def log(self, message, data=None):
        """Log with timestamp and optional data"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {message}")
        self.log_file.write(f"[{timestamp}] {message}\n")
        
        if data:
            formatted = json.dumps(data, indent=2, default=str)
            print(f"DATA: {formatted}")
            self.log_file.write(f"DATA: {formatted}\n")
            
        self.log_file.flush()
        
    def capture_response(self, operation, response):
        """Capture all responses"""
        self.all_data["responses"].append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "response": response
        })
        
    def test_1_configuration(self):
        """Test 1: Load and display full configuration"""
        self.log("\n" + "="*80)
        self.log("TEST 1: CONFIGURATION LOADING")
        self.log("="*80)
        
        try:
            # Load configuration
            config_path = "/workspace/usenet_sync_config.json"
            self.log(f"Loading configuration from: {config_path}")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.log("FULL CONFIGURATION:", config)
            self.all_data["configuration"] = config
            
            # Extract server details
            server = config['servers'][0]
            self.log("SERVER DETAILS:", {
                "hostname": server['hostname'],
                "port": server['port'],
                "username": server['username'],
                "password": server['password'][:3] + "***",  # Partially hide password
                "use_ssl": server['use_ssl'],
                "max_connections": server['max_connections']
            })
            
            # Extract settings
            self.log("SECURITY SETTINGS:", config.get('security', {}))
            self.log("PERFORMANCE SETTINGS:", config.get('performance', {}))
            
            return config
            
        except Exception as e:
            self.log(f"ERROR loading configuration: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return None
    
    def test_2_database_setup(self):
        """Test 2: Setup PostgreSQL and show all operations"""
        self.log("\n" + "="*80)
        self.log("TEST 2: POSTGRESQL DATABASE SETUP")
        self.log("="*80)
        
        try:
            # Connect as postgres to create database
            self.log("Connecting to PostgreSQL as postgres user...")
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="postgres"
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Check existing databases
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = cur.fetchall()
            self.log("EXISTING DATABASES:", [db[0] for db in databases])
            
            # Create test database
            db_name = "detailed_test_db"
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
            if cur.fetchone():
                self.log(f"Database {db_name} exists, dropping...")
                cur.execute(f"DROP DATABASE {db_name}")
            
            self.log(f"Creating database: {db_name}")
            cur.execute(f"CREATE DATABASE {db_name}")
            
            # Grant permissions
            self.log("Granting permissions to usenet user...")
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO usenet")
            cur.execute(f"ALTER DATABASE {db_name} OWNER TO usenet")
            
            conn.close()
            
            # Connect to new database
            self.log(f"Connecting to {db_name} as usenet...")
            db = psycopg2.connect(
                host="localhost",
                port=5432,
                database=db_name,
                user="usenet",
                password="usenet_secure_2024"
            )
            
            # Create schema
            with db.cursor() as cur:
                schema_sql = """
                CREATE TABLE folders (
                    folder_id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    total_size BIGINT DEFAULT 0,
                    file_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE files (
                    file_id UUID PRIMARY KEY,
                    folder_id UUID REFERENCES folders(folder_id),
                    filename TEXT NOT NULL,
                    size BIGINT NOT NULL,
                    hash TEXT NOT NULL,
                    content_preview TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE segments (
                    segment_id UUID PRIMARY KEY,
                    file_id UUID REFERENCES files(file_id),
                    segment_index INTEGER NOT NULL,
                    size BIGINT NOT NULL,
                    hash TEXT NOT NULL,
                    message_id TEXT UNIQUE,
                    subject TEXT,
                    internal_subject TEXT,
                    segment_data TEXT,
                    uploaded BOOLEAN DEFAULT FALSE,
                    upload_response TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE shares (
                    share_id TEXT PRIMARY KEY,
                    folder_id UUID REFERENCES folders(folder_id),
                    share_type TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
                
                self.log("Creating database schema...")
                cur.execute(schema_sql)
                db.commit()
                
                # Verify tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cur.fetchall()
                self.log("CREATED TABLES:", [t[0] for t in tables])
            
            self.all_data["database"] = {
                "name": db_name,
                "host": "localhost",
                "port": 5432,
                "user": "usenet",
                "tables": [t[0] for t in tables]
            }
            
            return db
            
        except Exception as e:
            self.log(f"ERROR in database setup: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return None
    
    def test_3_file_creation(self, db):
        """Test 3: Create files and show all data"""
        self.log("\n" + "="*80)
        self.log("TEST 3: FILE CREATION WITH FULL DATA")
        self.log("="*80)
        
        try:
            test_data_dir = self.test_dir / "test_files"
            test_data_dir.mkdir(exist_ok=True)
            
            # Create test files with specific content
            files_to_create = {
                "readme.txt": b"This is a test readme file.\nIt contains multiple lines.\nVersion 1.0\n",
                "data.json": json.dumps({"test": "data", "version": 1, "items": [1,2,3]}, indent=2).encode(),
                "binary.dat": secrets.token_bytes(1024),  # 1KB random data
                "large.bin": secrets.token_bytes(1024 * 1024),  # 1MB random data
            }
            
            folder_id = str(uuid.uuid4())
            self.log(f"Creating folder with ID: {folder_id}")
            
            with db.cursor() as cur:
                # Create folder
                cur.execute("""
                    INSERT INTO folders (folder_id, name, path)
                    VALUES (%s, %s, %s)
                    RETURNING *
                """, (folder_id, "test_files", str(test_data_dir)))
                
                folder_record = cur.fetchone()
                self.log("FOLDER CREATED:", {
                    "folder_id": folder_record[0],
                    "name": folder_record[1],
                    "path": folder_record[2],
                    "created_at": str(folder_record[5])
                })
                
                # Create each file
                total_size = 0
                file_records = []
                
                for filename, content in files_to_create.items():
                    filepath = test_data_dir / filename
                    filepath.write_bytes(content)
                    
                    file_id = str(uuid.uuid4())
                    file_hash = hashlib.sha256(content).hexdigest()
                    file_size = len(content)
                    total_size += file_size
                    
                    # Get content preview
                    if filename.endswith('.txt') or filename.endswith('.json'):
                        preview = content[:200].decode('utf-8', errors='ignore')
                    else:
                        preview = f"Binary file: {file_size} bytes"
                    
                    self.log(f"\nCreating file: {filename}")
                    self.log("FILE DETAILS:", {
                        "file_id": file_id,
                        "filename": filename,
                        "size": file_size,
                        "hash": file_hash,
                        "preview": preview[:100] + "..." if len(preview) > 100 else preview
                    })
                    
                    # Insert into database
                    cur.execute("""
                        INSERT INTO files (file_id, folder_id, filename, size, hash, content_preview)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (file_id, folder_id, filename, file_size, file_hash, preview))
                    
                    file_record = cur.fetchone()
                    file_records.append({
                        "file_id": file_record[0],
                        "filename": file_record[2],
                        "size": file_record[3],
                        "hash": file_record[4],
                        "preview": file_record[5][:50] if file_record[5] else None
                    })
                    
                    # Store in all_data
                    self.all_data["files"][filename] = {
                        "file_id": file_id,
                        "size": file_size,
                        "hash": file_hash,
                        "content_sample": preview[:100]
                    }
                
                # Update folder stats
                cur.execute("""
                    UPDATE folders 
                    SET total_size = %s, file_count = %s
                    WHERE folder_id = %s
                    RETURNING *
                """, (total_size, len(files_to_create), folder_id))
                
                updated_folder = cur.fetchone()
                self.log("\nFOLDER UPDATED:", {
                    "total_size": updated_folder[3],
                    "file_count": updated_folder[4]
                })
                
                db.commit()
                
            self.log("\nFILES CREATED SUMMARY:", file_records)
            return folder_id, file_records
            
        except Exception as e:
            self.log(f"ERROR in file creation: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return None, None
    
    def test_4_segmentation(self, db, folder_id, file_records):
        """Test 4: Segment files and show all segment data"""
        self.log("\n" + "="*80)
        self.log("TEST 4: FILE SEGMENTATION WITH FULL DATA")
        self.log("="*80)
        
        try:
            segment_size = 768000  # 750KB
            all_segments = []
            
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                for file_rec in file_records:
                    self.log(f"\nSegmenting file: {file_rec['filename']}")
                    self.log(f"File size: {file_rec['size']:,} bytes")
                    
                    num_segments = (file_rec['size'] + segment_size - 1) // segment_size
                    self.log(f"Segments needed: {num_segments}")
                    
                    file_segments = []
                    
                    for i in range(num_segments):
                        segment_id = str(uuid.uuid4())
                        seg_size = min(segment_size, file_rec['size'] - i * segment_size)
                        seg_hash = hashlib.sha256(f"{file_rec['file_id']}:{i}:{secrets.token_hex(8)}".encode()).hexdigest()
                        
                        # Generate obfuscated headers
                        message_id = f"<{secrets.token_hex(16)}@{secrets.choice(['ngPost.com', 'yenc.org', 'newsreader.com'])}>"
                        subject = base64.b32encode(secrets.token_bytes(10)).decode().rstrip('=')
                        internal_subject = f"{file_rec['filename']}.part{i+1:03d}of{num_segments:03d}"
                        
                        # Simulate segment data
                        segment_data = base64.b64encode(secrets.token_bytes(min(100, seg_size))).decode()[:200]
                        
                        segment_info = {
                            "segment_id": segment_id,
                            "file_id": file_rec['file_id'],
                            "segment_index": i,
                            "size": seg_size,
                            "hash": seg_hash,
                            "message_id": message_id,
                            "subject": subject,
                            "internal_subject": internal_subject,
                            "data_preview": segment_data[:50] + "..."
                        }
                        
                        self.log(f"  Segment {i+1}/{num_segments}:", segment_info)
                        
                        # Insert into database
                        cur.execute("""
                            INSERT INTO segments 
                            (segment_id, file_id, segment_index, size, hash, 
                             message_id, subject, internal_subject, segment_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING *
                        """, (segment_id, file_rec['file_id'], i, seg_size, seg_hash,
                              message_id, subject, internal_subject, segment_data))
                        
                        segment_record = dict(cur.fetchone())
                        file_segments.append(segment_record)
                        all_segments.append(segment_record)
                    
                    self.all_data["segments"][file_rec['filename']] = {
                        "num_segments": num_segments,
                        "segments": [{
                            "index": s['segment_index'],
                            "size": s['size'],
                            "message_id": s['message_id'],
                            "subject": s['subject']
                        } for s in file_segments]
                    }
                    
                    self.log(f"  Created {num_segments} segments for {file_rec['filename']}")
                
                db.commit()
                
            self.log(f"\nTOTAL SEGMENTS CREATED: {len(all_segments)}")
            return all_segments
            
        except Exception as e:
            self.log(f"ERROR in segmentation: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return None
    
    def test_5_share_creation(self, db, folder_id):
        """Test 5: Create shares and show all details"""
        self.log("\n" + "="*80)
        self.log("TEST 5: SHARE CREATION WITH FULL DETAILS")
        self.log("="*80)
        
        try:
            share_gen = ShareIDGenerator()
            shares_created = []
            
            with db.cursor() as cur:
                for share_type in ['public', 'private', 'protected']:
                    self.log(f"\nCreating {share_type} share:")
                    
                    # Generate share ID
                    share_id = share_gen.generate_share_id(folder_id, share_type)
                    
                    # Create metadata
                    metadata = {
                        "type": share_type,
                        "created_by": "test_user",
                        "version": 1
                    }
                    
                    if share_type == 'private':
                        metadata['authorized_users'] = ['user1', 'user2', 'user3']
                        metadata['access_level'] = 'read-only'
                    elif share_type == 'protected':
                        metadata['password_required'] = True
                        metadata['password_hint'] = 'test password'
                        metadata['expiry_days'] = 30
                    
                    self.log("SHARE DETAILS:", {
                        "share_id": share_id,
                        "share_type": share_type,
                        "folder_id": folder_id,
                        "metadata": metadata
                    })
                    
                    # Analyze share ID
                    self.log("SHARE ID ANALYSIS:", {
                        "length": len(share_id),
                        "has_underscore": '_' in share_id,
                        "has_dash": '-' in share_id,
                        "starts_with_type": share_id[0] in ['P', 'R', 'O'],
                        "is_alphanumeric": share_id.replace('_', '').replace('-', '').isalnum(),
                        "character_set": set(share_id)
                    })
                    
                    # Validate share ID
                    is_valid, detected_type = share_gen.validate_share_id(share_id)
                    self.log("VALIDATION RESULT:", {
                        "is_valid": is_valid,
                        "detected_type": detected_type,
                        "type_detectable": detected_type is not None
                    })
                    
                    # Insert into database
                    cur.execute("""
                        INSERT INTO shares (share_id, folder_id, share_type, metadata)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *
                    """, (share_id, folder_id, share_type, json.dumps(metadata)))
                    
                    share_record = cur.fetchone()
                    shares_created.append({
                        "share_id": share_record[0],
                        "share_type": share_record[2],
                        "metadata": share_record[3],
                        "created_at": str(share_record[4])
                    })
                    
                    self.all_data["shares"][share_type] = {
                        "share_id": share_id,
                        "metadata": metadata,
                        "analysis": {
                            "has_patterns": '_' in share_id or share_id[0] in ['P', 'R', 'O'],
                            "length": len(share_id)
                        }
                    }
                
                db.commit()
                
            self.log("\nALL SHARES CREATED:", shares_created)
            return shares_created
            
        except Exception as e:
            self.log(f"ERROR in share creation: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return None
    
    def test_6_usenet_connection(self, config):
        """Test 6: Test Usenet connection and show responses"""
        self.log("\n" + "="*80)
        self.log("TEST 6: USENET CONNECTION TEST")
        self.log("="*80)
        
        try:
            server = config['servers'][0]
            
            self.log("CONNECTING TO USENET:", {
                "server": server['hostname'],
                "port": server['port'],
                "username": server['username'],
                "ssl": server['use_ssl']
            })
            
            # Try different connection methods
            import socket
            import ssl
            
            # Test raw socket connection
            self.log("\nTesting raw socket connection...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            if server['use_ssl']:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=server['hostname'])
            
            try:
                sock.connect((server['hostname'], server['port']))
                self.log("Socket connected successfully")
                
                # Read greeting
                greeting = sock.recv(1024).decode('utf-8', errors='ignore')
                self.log("SERVER GREETING:", greeting)
                
                # Send AUTHINFO USER
                user_cmd = f"AUTHINFO USER {server['username']}\r\n"
                sock.send(user_cmd.encode())
                user_response = sock.recv(1024).decode('utf-8', errors='ignore')
                self.log("AUTHINFO USER RESPONSE:", user_response)
                
                # Send AUTHINFO PASS
                pass_cmd = f"AUTHINFO PASS {server['password']}\r\n"
                sock.send(pass_cmd.encode())
                pass_response = sock.recv(1024).decode('utf-8', errors='ignore')
                self.log("AUTHINFO PASS RESPONSE:", pass_response)
                
                # Get server capabilities
                sock.send(b"CAPABILITIES\r\n")
                cap_response = sock.recv(4096).decode('utf-8', errors='ignore')
                self.log("CAPABILITIES:", cap_response)
                
                # List newsgroups
                sock.send(b"LIST\r\n")
                list_response = sock.recv(4096).decode('utf-8', errors='ignore')[:500]  # First 500 chars
                self.log("LIST RESPONSE (first 500 chars):", list_response)
                
                sock.close()
                
                self.all_data["uploads"]["connection_test"] = {
                    "status": "success",
                    "greeting": greeting[:100],
                    "authenticated": "281" in pass_response
                }
                
                return True
                
            except Exception as e:
                self.log(f"Socket connection failed: {e}")
                sock.close()
                return False
                
        except Exception as e:
            self.log(f"ERROR in Usenet connection: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return False
    
    def test_7_data_verification(self, db):
        """Test 7: Verify all data and show complete database state"""
        self.log("\n" + "="*80)
        self.log("TEST 7: DATA VERIFICATION")
        self.log("="*80)
        
        try:
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                # Get folder stats
                cur.execute("SELECT * FROM folders")
                folders = cur.fetchall()
                self.log("FOLDERS IN DATABASE:", folders)
                
                # Get file stats
                cur.execute("SELECT COUNT(*) as count, SUM(size) as total_size FROM files")
                file_stats = cur.fetchone()
                self.log("FILE STATISTICS:", file_stats)
                
                # Get all files
                cur.execute("SELECT file_id, filename, size, hash FROM files")
                files = cur.fetchall()
                self.log("ALL FILES:", files)
                
                # Get segment stats
                cur.execute("SELECT COUNT(*) as count, SUM(size) as total_size FROM segments")
                segment_stats = cur.fetchone()
                self.log("SEGMENT STATISTICS:", segment_stats)
                
                # Get segments by file
                cur.execute("""
                    SELECT f.filename, COUNT(s.*) as segment_count, SUM(s.size) as total_size
                    FROM files f
                    LEFT JOIN segments s ON f.file_id = s.file_id
                    GROUP BY f.filename
                """)
                segments_by_file = cur.fetchall()
                self.log("SEGMENTS BY FILE:", segments_by_file)
                
                # Get all shares
                cur.execute("SELECT * FROM shares")
                shares = cur.fetchall()
                self.log("ALL SHARES:", shares)
                
                # Sample segments
                cur.execute("""
                    SELECT s.segment_index, s.message_id, s.subject, s.internal_subject, f.filename
                    FROM segments s
                    JOIN files f ON s.file_id = f.file_id
                    ORDER BY f.filename, s.segment_index
                    LIMIT 10
                """)
                sample_segments = cur.fetchall()
                self.log("SAMPLE SEGMENTS (first 10):", sample_segments)
                
            return True
            
        except Exception as e:
            self.log(f"ERROR in data verification: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
            return False
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        self.log("\n" + "="*80)
        self.log("FINAL COMPREHENSIVE REPORT")
        self.log("="*80)
        
        # Save all data to JSON
        self.all_data["test_end"] = datetime.now().isoformat()
        json.dump(self.all_data, self.data_file, indent=2, default=str)
        self.data_file.close()
        
        self.log("\nALL TEST DATA SAVED TO:", str(self.test_dir / "test_data.json"))
        self.log("FULL LOG SAVED TO:", str(self.test_dir / "full_test_log.txt"))
        
        # Summary
        self.log("\nTEST SUMMARY:")
        self.log(f"  Files created: {len(self.all_data['files'])}")
        self.log(f"  Total segments: {sum(len(s['segments']) for s in self.all_data['segments'].values()) if self.all_data['segments'] else 0}")
        self.log(f"  Shares created: {len(self.all_data['shares'])}")
        self.log(f"  Total responses captured: {len(self.all_data['responses'])}")
        
        self.log_file.close()
    
    def run_all_tests(self):
        """Run all tests with full data capture"""
        db = None
        try:
            # Test 1: Configuration
            config = self.test_1_configuration()
            if not config:
                self.log("Configuration test failed, stopping")
                return
            
            # Test 2: Database
            db = self.test_2_database_setup()
            if not db:
                self.log("Database setup failed, stopping")
                return
            
            # Test 3: Files
            folder_id, file_records = self.test_3_file_creation(db)
            if not folder_id:
                self.log("File creation failed, stopping")
                return
            
            # Test 4: Segmentation
            segments = self.test_4_segmentation(db, folder_id, file_records)
            if not segments:
                self.log("Segmentation failed, continuing...")
            
            # Test 5: Shares
            shares = self.test_5_share_creation(db, folder_id)
            if not shares:
                self.log("Share creation failed, continuing...")
            
            # Test 6: Usenet
            usenet_ok = self.test_6_usenet_connection(config)
            if not usenet_ok:
                self.log("Usenet connection failed, continuing...")
            
            # Test 7: Verification
            self.test_7_data_verification(db)
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            self.log(f"Traceback: {traceback.format_exc()}")
        finally:
            if db:
                db.close()
            self.generate_final_report()


if __name__ == "__main__":
    test = DetailedSystemTest()
    test.run_all_tests()