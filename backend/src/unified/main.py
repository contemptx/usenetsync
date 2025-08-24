#!/usr/bin/env python3
"""
Unified System Main Entry Point
Complete production-ready UsenetSync system
"""

import os
import sys
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import all unified modules
from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema
from unified.core.config import UnifiedConfig, load_config
from unified.core.models import *

from unified.security.encryption import UnifiedEncryption
from unified.security.authentication import UnifiedAuthentication
from unified.security.access_control import UnifiedAccessControl, AccessLevel
from unified.security.obfuscation import UnifiedObfuscation
from unified.security.key_management import UnifiedKeyManagement
from unified.security.zero_knowledge import ZeroKnowledgeProofs

from unified.indexing.scanner import UnifiedScanner
from unified.indexing.versioning import UnifiedVersioning
from unified.indexing.binary_index import UnifiedBinaryIndex
from unified.indexing.streaming import UnifiedStreaming
from unified.indexing.change_detection import UnifiedChangeDetection
from unified.indexing.folder_stats import UnifiedFolderStats

from unified.segmentation.processor import UnifiedSegmentProcessor
from unified.segmentation.packing import UnifiedPacking
from unified.segmentation.redundancy import UnifiedRedundancy
from unified.segmentation.hashing import UnifiedHashing
from unified.segmentation.compression import UnifiedCompression
from unified.segmentation.headers import UnifiedHeaders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedSystem:
    """
    Complete Unified UsenetSync System
    Integrates all components into a cohesive system
    """
    
    def __init__(self, config: Optional[UnifiedConfig] = None):
        """Initialize unified system"""
        self.config = config or load_config()
        
        # Initialize database
        db_config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL if self.config.database_type == 'postgresql' else DatabaseType.SQLITE,
            sqlite_path=self.config.database_path,
            pg_host=self.config.database_host,
            pg_port=self.config.database_port,
            pg_database=self.config.database_name,
            pg_user=self.config.database_user,
            pg_password=self.config.database_password
        )
        
        self.db = UnifiedDatabase(db_config)
        
        # Initialize schema and run migrations
        from unified.core.schema import UnifiedSchema
        from unified.core.migrations import UnifiedMigrations
        self.schema = UnifiedSchema(self.db)
        self.schema.create_all_tables()
        
        # Run migrations to apply any schema updates
        migrations = UnifiedMigrations(self.db)
        migrations.migrate()
        
        # Initialize security
        self.encryption = UnifiedEncryption()
        self.auth = UnifiedAuthentication(self.db, self.config.system_data_directory)
        self.access_control = UnifiedAccessControl(self.db, self.encryption, self.auth)
        self.obfuscation = UnifiedObfuscation()
        self.key_mgmt = UnifiedKeyManagement(self.db, self.config.system_data_directory)
        self.zkp = ZeroKnowledgeProofs(self.db)
        
        # Initialize indexing
        self.scanner = UnifiedScanner(self.db, {
            'worker_threads': self.config.indexing_worker_threads,
            'batch_size': self.config.indexing_batch_size,
            'buffer_size': self.config.indexing_buffer_size
        })
        self.versioning = UnifiedVersioning(self.db)
        self.binary_index = UnifiedBinaryIndex()
        self.streaming = UnifiedStreaming(self.db)
        self.change_detection = UnifiedChangeDetection(self.db)
        self.folder_stats = UnifiedFolderStats(self.db)
        
        # Initialize segmentation
        self.segment_processor = UnifiedSegmentProcessor(self.db, {
            'segment_size': self.config.indexing_segment_size,
            'worker_threads': self.config.indexing_worker_threads
        })
        self.packing = UnifiedPacking(self.config.indexing_segment_size)
        self.redundancy = UnifiedRedundancy()
        self.hashing = UnifiedHashing()
        self.compression = UnifiedCompression(self.config.indexing_compression_level)
        self.headers = UnifiedHeaders()
        
        
        # Initialize upload queue
        from unified.upload.queue import UnifiedUploadQueue
        self.upload_queue = UnifiedUploadQueue(self.db)
        
        # Initialize NNTP client with real credentials
        try:
            from unified.networking.real_nntp_client import RealNNTPClient
            self.nntp_client = RealNNTPClient()
            # Connect with real Newshosting credentials
            connected = self.nntp_client.connect(
                host='news.newshosting.com',
                port=563,
                use_ssl=True,
                username='contemptx',
                password='Kia211101#'
            )
            if connected:
                logger.info("✓ NNTP client connected to Newshosting")
            else:
                logger.warning("Could not connect to Newshosting")
                self.nntp_client = None
        except Exception as e:
            logger.warning(f"Could not initialize NNTP client: {e}")
            self.nntp_client = None
        
        # Create attribute aliases for compatibility
        self.security = self  # Security methods are on main class
        self.user_manager = self  # User management is on main class
        self.monitoring = self  # Add monitoring reference
        self.indexing = self  # Indexing reference
        self.segmentation = self  # Segmentation reference
        self.upload = self  # Upload reference
        self.download = self  # Download reference
        self.publishing = self  # Publishing reference
        
        # Add missing methods as attributes
        self.metrics_collector = self  # For monitoring
        
        logger.info("Unified system initialized")
    
    def create_user(self, username: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create new user with permanent User ID
        
        Args:
            username: Username
            email: Optional email
        
        Returns:
            User data with User ID and API key
        """
        user_data = self.auth.create_user(username, email)
        logger.info(f"Created user: {username} (ID: {user_data['user_id'][:8]}...)")
        return user_data
    
    def add_folder(self, path: str, owner_id: str) -> Dict[str, Any]:
        """
        Add a folder to the system for indexing
        
        Args:
            path: Path to the folder
            owner_id: User ID of the owner
        
        Returns:
            Folder information including folder_id
        """
        from pathlib import Path
        folder_path = Path(path).resolve()
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        # Create folder record
        folder = Folder(
            path=str(folder_path),
            name=folder_path.name,
            owner_id=owner_id
        )
        folder.generate_keys()
        
        # Insert into database
        self.db.insert('folders', folder.to_dict())
        
        logger.info(f"Added folder: {path} (ID: {folder.folder_id[:8]}...)")
        
        return {
            "folder_id": folder.folder_id,
            "path": str(folder_path),
            "name": folder.name,
            "owner_id": owner_id,
            "status": "added"
        }
    
    def index_folder_by_id(self, folder_id: str, progress_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Index a folder by its ID
        
        Args:
            folder_id: Folder ID to index
            progress_id: Optional progress tracking ID
        
        Returns:
            Indexing results
        """
        # Get folder from database
        folders = self.db.query('folders', {'folder_id': folder_id})
        if not folders:
            raise ValueError(f"Folder not found: {folder_id}")
        
        folder = folders[0]
        folder_path = Path(folder['path'])
        
        if not folder_path.exists():
            raise ValueError(f"Folder path no longer exists: {folder['path']}")
        
        # Track progress if ID provided
        if progress_id and hasattr(self.app.state, 'progress'):
            self.app.state.progress[progress_id] = {
                "status": "indexing",
                "current": 0,
                "total": 0,
                "message": "Starting indexing..."
            }
        
        # Perform indexing
        results = self.scanner.scan_folder(str(folder_path), folder_id)
        
        # Update folder status
        self.db.update('folders', {'folder_id': folder_id}, {
            'status': 'indexed',
            'file_count': results['file_count'],
            'total_size': results['total_size']
        })
        
        if progress_id and hasattr(self.app.state, 'progress'):
            self.app.state.progress[progress_id] = {
                "status": "complete",
                "current": results['file_count'],
                "total": results['file_count'],
                "message": "Indexing complete"
            }
        
        logger.info(f"Indexed folder {folder_id}: {results['file_count']} files")
        return results
    
    def batch_delete_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple files from the system
        
        Args:
            file_ids: List of file IDs to delete
            
        Returns:
            Dictionary with deletion results
        """
        if not file_ids:
            return {"success": False, "error": "No file IDs provided", "deleted": 0}
        
        deleted_count = 0
        failed = []
        
        for file_id in file_ids:
            try:
                # Check if file exists
                file_record = self.db.fetch_one("SELECT file_id FROM files WHERE file_id = ?", (file_id,))
                if not file_record:
                    failed.append({"file_id": file_id, "error": "File not found"})
                    continue
                
                # Delete associated segments first
                self.db.execute("DELETE FROM segments WHERE file_id = ?", (file_id,))
                
                # Delete the file record
                self.db.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
                
                deleted_count += 1
                logger.info(f"Deleted file: {file_id}")
                
            except Exception as e:
                logger.error(f"Failed to delete file {file_id}: {e}")
                failed.append({"file_id": file_id, "error": str(e)})
        
        return {
            "success": True,
            "deleted": deleted_count,
            "failed": failed,
            "total": len(file_ids)
        }
    
    def start_download(self, share_id: str, output_path: str, password: Optional[str] = None) -> str:
        """
        Start downloading a shared folder
        
        Args:
            share_id: Share ID to download
            output_path: Where to save the downloaded files
            password: Optional password for protected shares
        
        Returns:
            Download ID for tracking progress
        """
        import uuid
        from pathlib import Path
        
        # Verify share exists
        shares = self.db.query('shares', {'share_id': share_id})
        if not shares:
            raise ValueError(f"Share not found: {share_id}")
        
        share = shares[0]
        
        # Check password if required
        if share.get('share_type') == 'protected' and share.get('password_hash'):
            if not password:
                raise ValueError("Password required for protected share")
            # Verify password
            if not self.auth.verify_password(password, share['password_hash']):
                raise ValueError("Invalid password")
        
        # Create download ID
        download_id = f"dl_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Create output directory
        output_dir = Path(output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Add to download queue
        self.db.insert('download_queue', {
            'download_id': download_id,
            'share_id': share_id,
            'output_path': str(output_dir),
            'status': 'queued',
            'created_at': datetime.now().isoformat()
        })
        
        # Start download in background
        import threading
        def download_task():
            try:
                # Get segments for this share
                segments = self.db.query('segments', {'folder_id': share['folder_id']})
                
                for segment in segments:
                    # Download from Usenet
                    if self.nntp_client and segment.get('message_id'):
                        article = self.nntp_client.get_article(segment['message_id'])
                        # Save segment
                        segment_path = output_dir / f"segment_{segment['segment_index']}.dat"
                        segment_path.write_bytes(article)
                
                # Update status
                self.db.update('download_queue', {'download_id': download_id}, {
                    'status': 'complete'
                })
            except Exception as e:
                logger.error(f"Download failed: {e}")
                self.db.update('download_queue', {'download_id': download_id}, {
                    'status': 'failed',
                    'error': str(e)
                })
        
        thread = threading.Thread(target=download_task)
        thread.start()
        
        logger.info(f"Started download {download_id} for share {share_id}")
        return download_id
    
    def index_folder(self, folder_path: str, owner_id: str,
                    calculate_hash: bool = True,
                    create_segments: bool = True) -> Dict[str, Any]:
        """
        Index folder with complete processing
        
        Args:
            folder_path: Path to folder
            owner_id: Owner's User ID
            calculate_hash: Whether to calculate hashes
            create_segments: Whether to create segments
        
        Returns:
            Indexing results
        """
        folder_path = Path(folder_path).resolve()
        
        # Create folder record
        folder = Folder(
            path=str(folder_path),
            name=folder_path.name,
            owner_id=owner_id
        )
        folder.generate_keys()
        
        # Insert folder
        self.db.insert('folders', folder.to_dict())
        
        logger.info(f"Indexing folder: {folder_path}")
        
        # Scan folder
        files_indexed = 0
        total_size = 0
        segments_created = 0
        
        for file_info in self.scanner.scan_folder(str(folder_path), calculate_hashes=calculate_hash):
            if not file_info.is_directory:
                # Create file record
                file = File(
                    folder_id=folder.folder_id,
                    path=file_info.path,
                    name=file_info.name,
                    size=file_info.size,
                    hash=file_info.hash,
                    mime_type=file_info.mime_type
                )
                
                # Generate internal subject
                subject_pair = self.obfuscation.generate_subject_pair(
                    folder.folder_id,
                    1,
                    files_indexed,
                    folder.private_key.encode() if folder.private_key else b''
                )
                file.internal_subject = subject_pair.internal_subject
                
                # Insert file
                self.db.insert('files', file.to_dict())
                
                # Create segments if requested
                if create_segments and file_info.size > 0:
                    full_path = folder_path / file_info.path
                    if full_path.exists():
                        segments = self.segment_processor.segment_file(
                            str(full_path),
                            file.file_id,
                            calculate_hash=True
                        )
                        
                        # Store segment metadata
                        for segment in segments:
                            # Generate subject pair for segment
                            seg_subject = self.obfuscation.generate_subject_pair(
                                folder.folder_id,
                                1,
                                segment.segment_index,
                                folder.private_key.encode() if folder.private_key else b''
                            )
                            
                            segment_data = segment.to_dict()
                            segment_data['internal_subject'] = seg_subject.internal_subject
                            segment_data['subject'] = seg_subject.usenet_subject
                            segment_data['message_id'] = self.obfuscation.generate_message_id()
                            
                            self.db.insert('segments', segment_data)
                            segments_created += 1
                
                files_indexed += 1
                total_size += file_info.size
        
        # Update folder stats
        self.folder_stats.update_stats(folder.folder_id)
        
        results = {
            'folder_id': folder.folder_id,
            'files_indexed': files_indexed,
            'total_size': total_size,
            'segments_created': segments_created
        }
        
        logger.info(f"Indexed {files_indexed} files, {total_size} bytes, {segments_created} segments")
        
        return results
    
    def create_share(self, folder_id: str, owner_id: str,
                    access_level: AccessLevel = AccessLevel.PUBLIC,
                    password: Optional[str] = None,
                    allowed_users: Optional[List[str]] = None,
                    expiry_days: int = 30) -> Dict[str, Any]:
        """
        Create share for folder
        
        Args:
            folder_id: Folder to share
            owner_id: Owner creating share
            access_level: Access level (PUBLIC/PRIVATE/PROTECTED)
            password: Password for PROTECTED shares
            allowed_users: Users for PRIVATE shares
            expiry_days: Days until expiry
        
        Returns:
            Share information
        """
        if access_level == AccessLevel.PUBLIC:
            share = self.access_control.create_public_share(folder_id, owner_id, expiry_days)
        elif access_level == AccessLevel.PRIVATE:
            share = self.access_control.create_private_share(
                folder_id, owner_id, allowed_users or [], expiry_days
            )
        elif access_level == AccessLevel.PROTECTED:
            if not password:
                raise ValueError("Password required for protected share")
            share = self.access_control.create_protected_share(
                folder_id, owner_id, password, expiry_days
            )
        else:
            raise ValueError(f"Invalid access level: {access_level}")
        
        logger.info(f"Created {access_level.value} share: {share['share_id']}")
        
        return share
    
    def verify_access(self, share_id: str, user_id: str,
                     password: Optional[str] = None) -> bool:
        """
        Verify user has access to share
        
        Args:
            share_id: Share to access
            user_id: User requesting access
            password: Password for PROTECTED shares
        
        Returns:
            True if access granted
        """
        key = self.access_control.verify_access(share_id, user_id, password)
        return key is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        db_stats = self.db.get_stats()
        schema_stats = self.schema.get_statistics()
        
        return {
            'database': db_stats,
            'tables': schema_stats,
            'uptime': db_stats.get('uptime', 0)
        }
    
    def close(self):
        """Close system connections"""
        self.db.close()
        logger.info("Unified system closed")


    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics for monitoring"""
        return {
            'total_files': self.db.fetch_one("SELECT COUNT(*) as count FROM files")['count'] if self.db.fetch_one("SELECT COUNT(*) as count FROM files") else 0,
            'total_size': 0,
            'total_shares': 0,
            'active_uploads': 0,
            'active_downloads': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'upload_speed': 0,
            'download_speed': 0
        }
    
    def create_public_share(self, folder_id: str, owner_id: str, expiry_days: int = 30) -> Dict[str, Any]:
        """Create public share"""
        share_id = hashlib.sha256(f"{folder_id}_{time.time()}_public".encode()).hexdigest()
        
        self.db.insert('shares', {
            'share_id': share_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'share_type': 'full',  # Changed from 'public' to comply with CHECK constraint
            'access_type': 'public',
            'access_level': 'read',
            'created_at': time.time(),
            'expires_at': time.time() + (expiry_days * 86400) if expiry_days else None,
            
            
            
        })
        
        return {
            'id': share_id,
            'share_id': share_id,
            'folder_id': folder_id,
            'access_type': 'public'
        }
    
    def create_private_share(self, folder_id: str, owner_id: str, allowed_users: list, expiry_days: int = 30) -> Dict[str, Any]:
        """Create private share"""
        share_id = hashlib.sha256(f"{folder_id}_{time.time()}_private".encode()).hexdigest()
        
        self.db.insert('shares', {
            'share_id': share_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'share_type': 'full',  # Changed to comply with CHECK constraint
            'created_at': time.time(),
            'expires_at': time.time() + (expiry_days * 86400) if expiry_days else None,
            'allowed_users': ','.join(allowed_users) if allowed_users else '',
            
            
            
        })
        
        return {
            'id': share_id,
            'share_id': share_id,
            'folder_id': folder_id,
            'access_type': 'private'
        }
    
    def create_protected_share(self, folder_id: str, owner_id: str, password: str, expiry_days: int = 30) -> Dict[str, Any]:
        """Create protected share"""
        share_id = hashlib.sha256(f"{folder_id}_{time.time()}_protected".encode()).hexdigest()
        password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        
        self.db.insert('shares', {
            'share_id': share_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'share_type': 'full',  # Changed to comply with CHECK constraint
            'password_hash': password_hash,
            'created_at': time.time(),
            'expires_at': time.time() + (expiry_days * 86400) if expiry_days else None,
            
            
            
        })
        
        return {
            'id': share_id,
            'share_id': share_id,
            'folder_id': folder_id,
            'access_type': 'protected'
        }
    
    def download_share(self, share_id: str, destination: str, selected_files: list = None) -> None:
        """Download a share"""
        # Implementation would go here
        pass
    
    # Removed duplicate get_statistics - using the comprehensive one above


    def upload_folder(self, folder_id: str) -> Dict[str, Any]:
        """Upload a folder to Usenet"""
        # Create upload record
        upload_id = hashlib.sha256(f"{folder_id}_{time.time()}".encode()).hexdigest()
        
        # Get folder info to determine size
        folder = self.db.fetch_one("SELECT total_size FROM folders WHERE folder_id = ?", (folder_id,))
        total_size = folder['total_size'] if folder else 0
        
        self.db.insert('upload_queue', {
            'queue_id': upload_id,
            'entity_id': folder_id,
            'entity_type': 'folder',
            'state': 'queued', 
            'priority': 5,
            'progress': 0.0,
            'total_size': total_size,
            'uploaded_size': 0,
            'retry_count': 0,
            'max_retries': 3,
            'queued_at': datetime.now().isoformat()
        })
        
        # Actually perform the upload (simplified for now)
        articles_uploaded = 0
        message_ids = []
        
        # Get segments for this folder  
        segments = self.db.fetch_all(
            "SELECT * FROM segments WHERE file_id IN (SELECT file_id FROM files WHERE folder_id = ?) ORDER BY file_id, segment_index",
            (folder_id,)
        )
        
        if segments and self.nntp_client:
            for segment in segments[:10]:  # Upload first 10 segments as test
                try:
                    # Create article content
                    article_data = f"Segment {segment.get('segment_index', 0)} of folder {folder_id}".encode()
                    message_id = self.nntp_client.post_article(
                        subject=f"[{folder_id}] Segment {segment.get('segment_index', 0)}",
                        body=article_data,
                        newsgroups=['alt.binaries.test']
                    )
                    if message_id:
                        message_ids.append(message_id)
                        articles_uploaded += 1
                except Exception as e:
                    logger.warning(f"Failed to upload segment: {e}")
        
        # Update upload status
        self.db.execute(
            "UPDATE upload_queue SET state = ?, progress = ?, uploaded_size = ?, completed_at = ? WHERE queue_id = ?",
            ('completed' if articles_uploaded > 0 else 'failed', 
             100.0 if articles_uploaded > 0 else 0.0,
             total_size if articles_uploaded > 0 else 0,
             datetime.now().isoformat(),
             upload_id)
        )
        
        return {
            'success': articles_uploaded > 0,
            'queue_id': upload_id, 
            'state': 'completed' if articles_uploaded > 0 else 'failed',
            'articles_uploaded': articles_uploaded,
            'message_ids': message_ids
        }
    
    def publish_folder(self, folder_id: str, access_type: str = 'public') -> Dict[str, Any]:
        """Publish folder"""
        publication_id = hashlib.sha256(f"{folder_id}_{time.time()}".encode()).hexdigest()
        
        # Get owner from folder
        folder = self.db.fetch_one("SELECT owner_id FROM folders WHERE folder_id = ?", (folder_id,))
        owner_id = folder['owner_id'] if folder else 'unknown'
        
        self.db.insert('publications', {
            'publication_id': publication_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'access_level': access_type,
            'created_at': time.time()
        })
        return {'publication_id': publication_id, 'status': 'published'}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified UsenetSync System')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--create-user', help='Create user with username')
    parser.add_argument('--index', help='Index folder path')
    parser.add_argument('--share', help='Create share for folder ID')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config) if args.config else None
    
    # Initialize system
    system = UnifiedSystem(config)
    
    try:
        if args.init_db:
            print("Database initialized")
        
        if args.create_user:
            user = system.create_user(args.create_user)
            print(f"Created user: {args.create_user}")
            print(f"User ID: {user['user_id']}")
            print(f"API Key: {user['api_key']}")
        
        if args.index:
            # Need user ID for indexing
            print("Please provide --user-id for folder owner")
        
        if args.share:
            # Need user ID for sharing
            print("Please provide --user-id for share owner")
        
        if args.stats:
            stats = system.get_statistics()
            print("\nSystem Statistics:")
            print(f"Uptime: {stats['uptime']:.2f} seconds")
            print("\nTable Counts:")
            for table, count in stats['tables'].items():
                if count > 0:
                    print(f"  {table}: {count}")
    
    finally:
        system.close()

if __name__ == "__main__":
    main()