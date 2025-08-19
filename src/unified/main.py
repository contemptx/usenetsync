#!/usr/bin/env python3
"""
Unified System Main Entry Point
Complete production-ready UsenetSync system
"""

import os
import sys
import logging
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
        self.schema = UnifiedSchema(self.db)
        
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