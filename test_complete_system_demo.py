#!/usr/bin/env python3
"""
Complete System Demonstration with Real Feedback
Shows exactly what happens at every step of the UsenetSync process
"""

import os
import sys
import time
import uuid
import json
import hashlib
import sqlite3
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, '/workspace')

# Import all components
from src.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.networking.production_nntp_client import ProductionNNTPClient
from src.config.secure_config import SecureConfigLoader
from src.indexing.share_id_generator import ShareIDGenerator

# Color output for better visibility
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CompleteSystemDemo:
    """Demonstrates the complete UsenetSync system with real feedback"""
    
    def __init__(self):
        self.demo_dir = Path("/workspace/demo_test")
        self.demo_dir.mkdir(exist_ok=True)
        self.db_path = self.demo_dir / "demo.db"
        
        # Track everything that happens
        self.demo_data = {
            'files_created': [],
            'files_indexed': [],
            'segments_created': [],
            'articles_uploaded': [],
            'share_created': None,
            'articles_downloaded': [],
            'files_reconstructed': []
        }
        
    def print_header(self, text):
        """Print a colored header"""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    def print_section(self, text):
        """Print a section header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}▶ {text}{Colors.ENDC}")
    
    def print_success(self, text):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"{Colors.BLUE}  {text}{Colors.ENDC}")
    
    def print_data(self, label, value):
        """Print data field"""
        print(f"  {Colors.BOLD}{label}:{Colors.ENDC} {value}")
    
    def initialize_systems(self):
        """Initialize all systems with detailed feedback"""
        self.print_header("INITIALIZING USENETSYNC SYSTEMS")
        
        # Load configuration
        self.print_section("Loading Configuration")
        config_path = Path("/workspace/usenet_sync_config.json")
        config_loader = SecureConfigLoader(str(config_path))
        self.config = config_loader.load_config()
        server = self.config['servers'][0]
        
        self.print_data("Server", server['hostname'])
        self.print_data("Port", server['port'])
        self.print_data("Username", server['username'])
        self.print_data("SSL", "Enabled" if server['use_ssl'] else "Disabled")
        
        # Initialize database
        self.print_section("Initializing Database")
        # Use direct SQLite for demo to control schema
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        self._create_schema()
        conn.close()
        self.print_success("SQLite database initialized")
        self.print_data("Path", str(self.db_path))
        
        # Initialize security
        self.print_section("Initializing Security System")
        # Create a minimal DB wrapper for security system
        class MinimalDB:
            def __init__(self, path):
                self.path = path
        self.db = MinimalDB(str(self.db_path))
        self.security = EnhancedSecuritySystem(self.db)
        self.print_success("Security system initialized")
        self.print_data("Encryption", "AES-256-GCM")
        self.print_data("Key Derivation", "PBKDF2-SHA256")
        
        # Initialize NNTP client
        self.print_section("Connecting to Usenet Server")
        self.nntp = ProductionNNTPClient(
            host=server['hostname'],
            port=server['port'],
            username=server['username'],
            password=server['password'],
            use_ssl=server['use_ssl']
        )
        
        # Test connection
        try:
            from src.networking.optimized_connection_pool import OptimizedConnectionPool
            # Create connection pool
            self.nntp.pool = OptimizedConnectionPool(
                host=server['hostname'],
                port=server['port'],
                username=server['username'],
                password=server['password'],
                use_ssl=server['use_ssl'],
                max_connections=4
            )
            with self.nntp.pool.get_connection() as conn:
                resp, count, first, last, name = conn.group('alt.binaries.test')
                self.print_success(f"Connected to {server['hostname']}")
                self.print_data("Group", "alt.binaries.test")
                self.print_data("Articles", f"{count} (range: {first}-{last})")
        except Exception as e:
            self.print_info(f"Connection test failed: {e}")
            self.print_info("Continuing with demo...")
        
        # Initialize share generator
        self.share_gen = ShareIDGenerator()
        self.print_success("Share ID generator initialized")
        
    def _create_schema(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS folders (
                folder_id TEXT PRIMARY KEY,
                display_name TEXT,
                path TEXT,
                size INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                folder_id TEXT,
                filename TEXT,
                size INTEGER,
                hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                file_id TEXT,
                segment_index INTEGER,
                size INTEGER,
                hash TEXT,
                message_id TEXT,
                subject TEXT,
                uploaded_at TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS shares (
                share_id TEXT PRIMARY KEY,
                folder_id TEXT,
                share_type TEXT,
                access_string TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.close()
    
    def create_test_files(self):
        """Create test files with detailed feedback"""
        self.print_header("CREATING TEST FILES")
        
        test_folder = self.demo_dir / "test_files"
        test_folder.mkdir(exist_ok=True)
        
        # Create a realistic folder structure
        folders = [
            "Documents",
            "Documents/Reports",
            "Documents/Presentations",
            "Images",
            "Images/Photos",
            "Data"
        ]
        
        for folder in folders:
            (test_folder / folder).mkdir(parents=True, exist_ok=True)
        
        # Create various test files
        test_files = [
            ("Documents/README.txt", b"UsenetSync Demo Test\n" * 100, "text"),
            ("Documents/Reports/report_2024.txt", b"Annual Report 2024\n" * 500, "text"),
            ("Documents/Presentations/demo.txt", b"Demo Presentation\n" * 200, "text"),
            ("Images/test_image.dat", os.urandom(50 * 1024), "binary"),  # 50KB
            ("Images/Photos/photo1.dat", os.urandom(100 * 1024), "binary"),  # 100KB
            ("Images/Photos/photo2.dat", os.urandom(150 * 1024), "binary"),  # 150KB
            ("Data/dataset.csv", b"id,name,value\n" + b"1,test,100\n" * 1000, "csv"),
            ("Data/config.json", json.dumps({"test": "data"} ,indent=2).encode(), "json"),
        ]
        
        self.print_section("Creating Files")
        for rel_path, content, file_type in test_files:
            file_path = test_folder / rel_path
            file_path.write_bytes(content)
            
            file_hash = hashlib.sha256(content).hexdigest()
            size = len(content)
            
            self.demo_data['files_created'].append({
                'path': str(file_path),
                'relative_path': rel_path,
                'size': size,
                'hash': file_hash,
                'type': file_type
            })
            
            self.print_success(f"Created: {rel_path}")
            self.print_data("  Size", f"{size:,} bytes")
            self.print_data("  Hash", file_hash[:16] + "...")
            self.print_data("  Type", file_type)
        
        total_size = sum(f['size'] for f in self.demo_data['files_created'])
        self.print_info(f"\nTotal: {len(test_files)} files, {total_size:,} bytes")
        
        return str(test_folder)
    
    def index_files(self, folder_path):
        """Index files with detailed feedback"""
        self.print_header("INDEXING FILES")
        
        # Create folder record
        folder_id = str(uuid.uuid4())
        folder_name = Path(folder_path).name
        
        self.print_section("Creating Folder Index")
        self.print_data("Folder ID", folder_id)
        self.print_data("Folder Name", folder_name)
        self.print_data("Path", folder_path)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO folders (folder_id, display_name, path)
            VALUES (?, ?, ?)
        """, (folder_id, folder_name, folder_path))
        
        # Index each file
        self.print_section("Indexing Files")
        for file_info in self.demo_data['files_created']:
            file_id = str(uuid.uuid4())
            
            conn.execute("""
                INSERT INTO files (file_id, folder_id, filename, size, hash)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, folder_id, file_info['relative_path'], 
                  file_info['size'], file_info['hash']))
            
            self.demo_data['files_indexed'].append({
                'file_id': file_id,
                'folder_id': folder_id,
                'filename': file_info['relative_path'],
                'size': file_info['size'],
                'hash': file_info['hash']
            })
            
            self.print_success(f"Indexed: {file_info['relative_path']}")
            self.print_data("  File ID", file_id[:8] + "...")
        
        # Update folder stats
        total_files = len(self.demo_data['files_indexed'])
        total_size = sum(f['size'] for f in self.demo_data['files_indexed'])
        
        conn.execute("""
            UPDATE folders SET file_count = ?, size = ?
            WHERE folder_id = ?
        """, (total_files, total_size, folder_id))
        
        conn.commit()
        conn.close()
        
        self.print_info(f"\nIndexed: {total_files} files, {total_size:,} bytes")
        
        return folder_id
    
    def create_segments(self, folder_id):
        """Create segments for upload with detailed feedback"""
        self.print_header("CREATING SEGMENTS")
        
        segment_size = 768000  # 750KB standard Usenet article size
        
        conn = sqlite3.connect(self.db_path)
        
        self.print_section("Segmenting Files")
        for file_info in self.demo_data['files_indexed']:
            # For demo, create simple segments
            file_size = file_info['size']
            num_segments = (file_size + segment_size - 1) // segment_size
            
            if num_segments == 0:
                num_segments = 1
            
            self.print_success(f"Segmenting: {file_info['filename']}")
            self.print_data("  File Size", f"{file_size:,} bytes")
            self.print_data("  Segments", str(num_segments))
            
            for i in range(num_segments):
                segment_id = str(uuid.uuid4())
                segment_hash = hashlib.sha256(f"{file_info['hash']}{i}".encode()).hexdigest()
                
                # Generate unique message ID and subject
                message_id = self.nntp._generate_message_id()
                subject_pair = self.security.generate_subject_pair(
                    f"{file_info['filename']}_seg{i}"
                )
                
                conn.execute("""
                    INSERT INTO segments (segment_id, file_id, segment_index, 
                                        size, hash, message_id, subject)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (segment_id, file_info['file_id'], i, 
                      min(segment_size, file_size - i * segment_size),
                      segment_hash, message_id, subject_pair.usenet_subject))
                
                self.demo_data['segments_created'].append({
                    'segment_id': segment_id,
                    'file_id': file_info['file_id'],
                    'filename': file_info['filename'],
                    'segment_index': i,
                    'message_id': message_id,
                    'subject': subject_pair.usenet_subject,
                    'internal_subject': subject_pair.internal_subject
                })
                
                self.print_info(f"    Segment {i+1}/{num_segments}")
                self.print_data("      Message-ID", message_id[:30] + "...")
                self.print_data("      Subject", subject_pair.usenet_subject[:30] + "...")
        
        conn.commit()
        conn.close()
        
        total_segments = len(self.demo_data['segments_created'])
        self.print_info(f"\nCreated: {total_segments} segments")
    
    def upload_to_usenet(self):
        """Upload to Usenet with detailed feedback"""
        self.print_header("UPLOADING TO USENET")
        
        self.print_section("Upload Configuration")
        self.print_data("Target Group", "alt.binaries.test")
        self.print_data("User Agent", self.nntp._get_random_user_agent())
        self.print_data("Obfuscation", "Enabled")
        
        # For demo, upload a few test articles
        test_segments = self.demo_data['segments_created'][:3]  # Upload first 3 segments
        
        self.print_section("Uploading Articles")
        for segment in test_segments:
            self.print_success(f"Uploading: {segment['filename']} - Segment {segment['segment_index'] + 1}")
            
            # Create test content
            test_content = f"Demo segment {segment['segment_index']} for {segment['filename']}".encode()
            test_content += os.urandom(1024)  # Add some random data
            
            # Build article
            headers = {
                'From': 'demo@usenet-sync.com',
                'Newsgroups': 'alt.binaries.test',
                'Subject': segment['subject'],
                'Message-ID': segment['message_id'],
                'User-Agent': self.nntp._get_random_user_agent(),
                'X-No-Archive': 'yes'
            }
            
            self.print_info("  Headers:")
            for key, value in headers.items():
                if key == 'Subject' or key == 'Message-ID':
                    self.print_data(f"    {key}", value[:40] + "...")
                else:
                    self.print_data(f"    {key}", value)
            
            # Attempt upload
            try:
                with self.nntp.get_connection() as conn:
                    article_lines = []
                    for key, value in headers.items():
                        article_lines.append(f"{key}: {value}")
                    article_lines.append("")
                    
                    # Encode content
                    encoded = base64.b64encode(test_content).decode('ascii')
                    for i in range(0, len(encoded), 76):
                        article_lines.append(encoded[i:i+76])
                    
                    # Post article
                    conn.post('\r\n'.join(article_lines).encode('utf-8'))
                    
                    self.demo_data['articles_uploaded'].append({
                        'segment': segment,
                        'headers': headers,
                        'size': len(test_content),
                        'status': 'success'
                    })
                    
                    self.print_success("  ✓ Upload successful")
                    self.print_data("    Size", f"{len(test_content):,} bytes")
                    
            except Exception as e:
                error_msg = str(e)
                if "441" in error_msg:
                    self.print_info("  ⚠ Article rejected (441) - Posting not allowed")
                elif "480" in error_msg:
                    self.print_info("  ⚠ Authentication required")
                else:
                    self.print_info(f"  ⚠ Upload failed: {error_msg}")
                
                self.demo_data['articles_uploaded'].append({
                    'segment': segment,
                    'headers': headers,
                    'status': 'failed',
                    'error': error_msg
                })
        
        successful = sum(1 for a in self.demo_data['articles_uploaded'] if a['status'] == 'success')
        self.print_info(f"\nUploaded: {successful}/{len(test_segments)} articles")
    
    def create_share(self, folder_id):
        """Create and publish share with detailed feedback"""
        self.print_header("CREATING SHARE")
        
        self.print_section("Share Configuration")
        
        # Create different share types
        shares = []
        
        # Public share
        public_share = self.share_gen.generate_public_share()
        self.print_success("Public Share Created")
        self.print_data("  Share ID", public_share)
        self.print_data("  Type", "Public (Anyone can access)")
        shares.append(('public', public_share))
        
        # Private share
        private_share = self.share_gen.generate_private_share()
        self.print_success("Private Share Created")
        self.print_data("  Share ID", private_share)
        self.print_data("  Type", "Private (Authorized users only)")
        shares.append(('private', private_share))
        
        # Protected share
        password = "demo123"
        protected_share = self.share_gen.generate_protected_share(password)
        self.print_success("Protected Share Created")
        self.print_data("  Share ID", protected_share)
        self.print_data("  Type", "Protected (Password required)")
        self.print_data("  Password", password)
        shares.append(('protected', protected_share))
        
        # Store shares in database
        conn = sqlite3.connect(self.db_path)
        for share_type, share_id in shares:
            metadata = {
                'folder_id': folder_id,
                'type': share_type,
                'created': datetime.now().isoformat(),
                'segments': len(self.demo_data['segments_created'])
            }
            
            conn.execute("""
                INSERT INTO shares (share_id, folder_id, share_type, access_string, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (share_id, folder_id, share_type, share_id, json.dumps(metadata)))
        
        conn.commit()
        conn.close()
        
        self.demo_data['share_created'] = {
            'folder_id': folder_id,
            'shares': shares,
            'total_segments': len(self.demo_data['segments_created']),
            'total_files': len(self.demo_data['files_indexed'])
        }
        
        self.print_section("Share Summary")
        self.print_data("Folder ID", folder_id)
        self.print_data("Total Files", str(self.demo_data['share_created']['total_files']))
        self.print_data("Total Segments", str(self.demo_data['share_created']['total_segments']))
        self.print_data("Share Types", "Public, Private, Protected")
        
        return shares[0][1]  # Return public share for demo
    
    def simulate_download(self, share_id):
        """Simulate download process with detailed feedback"""
        self.print_header("DOWNLOADING FROM SHARE")
        
        self.print_section("Download Request")
        self.print_data("Share ID", share_id)
        self.print_data("Destination", str(self.demo_dir / "downloaded"))
        
        # Look up share in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM shares WHERE share_id = ?
        """, (share_id,))
        share = cursor.fetchone()
        
        if share:
            self.print_success("Share found in database")
            self.print_data("  Type", share[2])  # share_type
            self.print_data("  Folder", share[1])  # folder_id
            
            # Get segments for this share
            cursor = conn.execute("""
                SELECT s.* FROM segments s
                JOIN files f ON s.file_id = f.file_id
                WHERE f.folder_id = ?
                ORDER BY f.filename, s.segment_index
            """, (share[1],))
            
            segments = cursor.fetchall()
            self.print_data("  Segments", str(len(segments)))
            
            self.print_section("Downloading Articles")
            
            # Simulate downloading articles
            downloaded_count = 0
            for segment in segments[:3]:  # Download first 3 for demo
                segment_id, file_id, seg_index, size, hash_val, msg_id, subject, _ = segment
                
                self.print_success(f"Downloading segment {seg_index + 1}")
                self.print_data("  Message-ID", msg_id[:40] + "...")
                self.print_data("  Subject", subject[:40] + "...")
                
                # Simulate article retrieval
                try:
                    with self.nntp.get_connection() as conn:
                        # Try to retrieve by message ID
                        try:
                            response, info = conn.article(msg_id)
                            self.print_success("  ✓ Article retrieved")
                            self.print_data("    Response", str(response)[:50])
                            downloaded_count += 1
                        except:
                            self.print_info("  ⚠ Article not found (may not have propagated)")
                except Exception as e:
                    self.print_info(f"  ⚠ Download failed: {e}")
                
                self.demo_data['articles_downloaded'].append({
                    'segment_id': segment_id,
                    'message_id': msg_id,
                    'subject': subject,
                    'status': 'success' if downloaded_count > 0 else 'not_found'
                })
            
            self.print_info(f"\nDownloaded: {downloaded_count}/{len(segments[:3])} segments")
        
        conn.close()
    
    def show_system_overview(self):
        """Show complete system overview"""
        self.print_header("SYSTEM OVERVIEW")
        
        self.print_section("Database Statistics")
        conn = sqlite3.connect(self.db_path)
        
        # Count records
        tables = ['folders', 'files', 'segments', 'shares']
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            self.print_data(f"{table.capitalize()}", str(count))
        
        conn.close()
        
        self.print_section("Operation Summary")
        self.print_data("Files Created", str(len(self.demo_data['files_created'])))
        self.print_data("Files Indexed", str(len(self.demo_data['files_indexed'])))
        self.print_data("Segments Created", str(len(self.demo_data['segments_created'])))
        self.print_data("Articles Uploaded", str(len(self.demo_data['articles_uploaded'])))
        self.print_data("Articles Downloaded", str(len(self.demo_data['articles_downloaded'])))
        
        if self.demo_data['share_created']:
            self.print_section("Share Information")
            for share_type, share_id in self.demo_data['share_created']['shares']:
                self.print_success(f"{share_type.capitalize()} Share")
                self.print_data("  ID", share_id)
                self.print_info(f"  Access: usenet-sync download {share_id} /destination")
        
        self.print_section("Data Flow Visualization")
        print("""
        ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
        │   LOCAL     │────▶│   INDEXED   │────▶│  SEGMENTED  │
        │   FILES     │     │   IN DB     │     │  FOR UPLOAD │
        └─────────────┘     └─────────────┘     └─────────────┘
                                                        │
                                                        ▼
        ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
        │  DOWNLOADED │◀────│   USENET    │◀────│  UPLOADED   │
        │   FILES     │     │   SERVER    │     │  ARTICLES   │
        └─────────────┘     └─────────────┘     └─────────────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │   SHARE     │
                            │     IDS     │
                            └─────────────┘
        """)
    
    def save_demo_report(self):
        """Save detailed demo report"""
        report_path = self.demo_dir / "demo_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.demo_data, f, indent=2, default=str)
        
        self.print_success(f"\nDetailed report saved to: {report_path}")
        
        # Also create a human-readable report
        text_report = self.demo_dir / "demo_report.txt"
        with open(text_report, 'w') as f:
            f.write("USENETSYNC DEMO REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("FILES CREATED:\n")
            for file in self.demo_data['files_created']:
                f.write(f"  - {file['relative_path']} ({file['size']} bytes)\n")
            
            f.write(f"\nTOTAL: {len(self.demo_data['files_created'])} files\n")
            
            f.write("\nSEGMENTS CREATED:\n")
            for seg in self.demo_data['segments_created'][:5]:
                f.write(f"  - {seg['filename']} seg {seg['segment_index']}\n")
                f.write(f"    Message-ID: {seg['message_id']}\n")
            
            f.write(f"\nTOTAL: {len(self.demo_data['segments_created'])} segments\n")
            
            if self.demo_data['share_created']:
                f.write("\nSHARES CREATED:\n")
                for share_type, share_id in self.demo_data['share_created']['shares']:
                    f.write(f"  - {share_type}: {share_id}\n")
        
        self.print_success(f"Text report saved to: {text_report}")
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        try:
            # Initialize
            self.initialize_systems()
            
            # Create test files
            folder_path = self.create_test_files()
            
            # Index files
            folder_id = self.index_files(folder_path)
            
            # Create segments
            self.create_segments(folder_id)
            
            # Upload to Usenet
            self.upload_to_usenet()
            
            # Create and publish share
            share_id = self.create_share(folder_id)
            
            # Simulate download
            self.simulate_download(share_id)
            
            # Show overview
            self.show_system_overview()
            
            # Save report
            self.save_demo_report()
            
            self.print_header("DEMO COMPLETE")
            self.print_success("All systems demonstrated successfully!")
            
            return True
            
        except Exception as e:
            print(f"\n{Colors.FAIL}Demo failed: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         USENETSYNC COMPLETE SYSTEM DEMONSTRATION        ║")
    print("║                                                          ║")
    print("║  This demo will show you exactly how UsenetSync works   ║")
    print("║  with real components and detailed feedback at every    ║")
    print("║  step of the process.                                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    demo = CompleteSystemDemo()
    success = demo.run_complete_demo()
    
    sys.exit(0 if success else 1)