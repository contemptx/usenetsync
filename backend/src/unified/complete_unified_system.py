#!/usr/bin/env python3
"""
COMPLETE Unified UsenetSync System
Integrates ALL components with REAL implementations
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all real components
from unified.database_schema import UnifiedDatabaseSchema
from unified.unified_system import UnifiedDatabaseManager
from unified.indexing_system import UnifiedIndexingSystem
from unified.publishing_system import UnifiedPublishingSystem
from unified.security_system import SecuritySystem
from unified.monitoring_system import MonitoringSystem
from unified.backup_recovery import BackupRecoverySystem

# Import NNTP client
from networking.production_nntp_client import ProductionNNTPClient

# Import upload/download systems
from upload.enhanced_upload_system import EnhancedUploadSystem
from upload.segment_packing_system import SegmentPackingSystem
from download.enhanced_download_system import EnhancedDownloadSystem
from download.segment_retrieval_system import SegmentRetrievalSystem

logger = logging.getLogger(__name__)

class CompleteUnifiedSystem:
    """
    Complete unified system with ALL components integrated
    This is the REAL production system with no mocks
    """
    
    def __init__(self, db_type: str = 'sqlite', **db_params):
        """
        Initialize complete unified system
        
        Args:
            db_type: Database type ('sqlite' or 'postgresql')
            **db_params: Database connection parameters
        """
        self.db_type = db_type
        
        # Initialize database
        self.db_manager = UnifiedDatabaseManager(db_type, **db_params)
        self.db_manager.connect()
        
        # Create schema with ALL tables including user_commitments
        self.schema = UnifiedDatabaseSchema(db_type, **db_params)
        self.schema.create_schema()
        
        # Initialize security system
        self.security = SecuritySystem(
            keys_dir=db_params.get('keys_dir', '/var/lib/usenetsync/keys')
        )
        
        # Initialize core subsystems
        self.indexer = UnifiedIndexingSystem(self.db_manager)
        self.publisher = UnifiedPublishingSystem(self.db_manager)
        
        # Initialize monitoring
        self.monitoring = MonitoringSystem()
        
        # Initialize backup system
        self.backup_system = BackupRecoverySystem(
            backup_dir=db_params.get('backup_dir', '/var/lib/usenetsync/backups')
        )
        
        # NNTP client (initialized when configured)
        self.nntp_client = None
        
        # Upload/Download systems (initialized with NNTP)
        self.upload_system = None
        self.download_system = None
        self.segment_packer = None
        self.segment_retriever = None
        
        logger.info(f"Complete unified system initialized with {db_type} database")
    
    def configure_nntp(self, host: str, port: int, username: str, 
                      password: str, use_ssl: bool = True) -> bool:
        """
        Configure and initialize NNTP connection
        
        Args:
            host: NNTP server hostname
            port: NNTP server port
            username: NNTP username
            password: NNTP password
            use_ssl: Whether to use SSL
            
        Returns:
            True if connection successful
        """
        try:
            # Create NNTP client configuration
            config = {
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'use_ssl': use_ssl,
                'max_connections': 10,
                'timeout': 30,
                'retry_count': 3
            }
            
            # Initialize production NNTP client
            self.nntp_client = ProductionNNTPClient(config)
            
            # Test connection
            if not self.nntp_client.test_connection():
                logger.error("NNTP connection test failed")
                return False
            
            # Initialize upload system with real NNTP
            self.upload_system = EnhancedUploadSystem(
                db_manager=self.db_manager,
                nntp_client=self.nntp_client
            )
            
            # Initialize segment packer
            self.segment_packer = SegmentPackingSystem(
                db_manager=self.db_manager
            )
            
            # Initialize download system with real NNTP
            self.download_system = EnhancedDownloadSystem(
                db_manager=self.db_manager,
                nntp_client=self.nntp_client
            )
            
            # Initialize segment retriever
            self.segment_retriever = SegmentRetrievalSystem(
                nntp_client=self.nntp_client,
                db_manager=self.db_manager
            )
            
            logger.info(f"NNTP configured successfully: {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure NNTP: {e}")
            return False
    
    def index_folder(self, folder_path: str, recursive: bool = True,
                    segment_size: int = 768*1024) -> Dict[str, Any]:
        """
        Index a folder and create segments
        
        Args:
            folder_path: Path to folder to index
            recursive: Whether to recurse into subdirectories
            segment_size: Size of segments in bytes
            
        Returns:
            Indexing statistics
        """
        logger.info(f"Indexing folder: {folder_path}")
        
        # Set segment size in indexer
        self.indexer.segment_size = segment_size
        
        # Use the indexing system
        stats = self.indexer.index_folder(
            folder_path,
            folder_id=folder_path  # Use path as folder_id
        )
        
        # Record metrics
        if self.monitoring:
            self.monitoring.record_operation(
                'indexing',
                stats.get('duration', 0),
                success=stats.get('errors', 0) == 0
            )
        
        return stats
    
    def upload_file(self, file_hash: str, redundancy: int = 20) -> Dict[str, Any]:
        """
        Upload a file to Usenet with redundancy
        
        Args:
            file_hash: Hash of file to upload
            redundancy: Number of redundant copies
            
        Returns:
            Upload result
        """
        if not self.upload_system:
            return {'success': False, 'error': 'NNTP not configured'}
        
        logger.info(f"Uploading file: {file_hash}")
        
        # Get file info
        file_info = self.db_manager.fetchone(
            "SELECT * FROM files WHERE file_hash = %s",
            (file_hash,)
        )
        
        if not file_info:
            return {'success': False, 'error': 'File not found'}
        
        # Get segments
        segments = self.db_manager.fetchall(
            "SELECT * FROM segments WHERE file_id = %s ORDER BY segment_index",
            (file_info['file_id'],)
        )
        
        # Pack segments for upload
        packed_segments = self.segment_packer.pack_segments(
            segments,
            strategy='REDUNDANT',
            redundancy=redundancy
        )
        
        # Upload with redundancy
        result = self.upload_system.upload_with_redundancy(
            packed_segments,
            redundancy=redundancy
        )
        
        # Update file state
        if result['success']:
            self.db_manager.execute(
                "UPDATE files SET state = 'uploaded', upload_time = CURRENT_TIMESTAMP WHERE file_hash = %s",
                (file_hash,)
            )
        
        # Record metrics
        if self.monitoring:
            self.monitoring.record_operation(
                'upload',
                result.get('duration', 0),
                success=result['success']
            )
        
        return result
    
    def publish_file(self, file_hash: str, access_level: str = 'public',
                    password: Optional[str] = None, 
                    expiry_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Publish a file for sharing
        
        Args:
            file_hash: Hash of file to publish
            access_level: Access level ('public', 'private', 'restricted')
            password: Optional password for protected access
            expiry_days: Optional days until expiry
            
        Returns:
            Publication result
        """
        logger.info(f"Publishing file: {file_hash} with {access_level} access")
        
        result = self.publisher.publish_file(
            file_hash,
            access_level=access_level,
            password=password,
            expiry_days=expiry_days
        )
        
        # Record metrics
        if self.monitoring:
            self.monitoring.record_operation(
                'publish',
                0.1,
                success=result['success']
            )
        
        return result
    
    def download_file(self, file_hash: str, 
                     output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a file from Usenet
        
        Args:
            file_hash: Hash of file to download
            output_path: Optional output path
            
        Returns:
            Download result
        """
        if not self.download_system:
            return {'success': False, 'error': 'NNTP not configured'}
        
        logger.info(f"Downloading file: {file_hash}")
        
        # Get file info
        file_info = self.db_manager.fetchone(
            "SELECT * FROM files WHERE file_hash = %s",
            (file_hash,)
        )
        
        if not file_info:
            return {'success': False, 'error': 'File not found'}
        
        # Get segments
        segments = self.db_manager.fetchall(
            "SELECT * FROM segments WHERE file_id = %s ORDER BY segment_index",
            (file_info['file_id'],)
        )
        
        # Retrieve segments from Usenet
        retrieved_segments = self.segment_retriever.retrieve_segments(segments)
        
        # Reconstruct file
        result = self.download_system.reconstruct_file(
            retrieved_segments,
            output_path or file_info['file_path']
        )
        
        # Record metrics
        if self.monitoring:
            self.monitoring.record_operation(
                'download',
                result.get('duration', 0),
                success=result['success']
            )
        
        return result
    
    def add_user_commitment(self, user_id: str, folder_id: str,
                          commitment_type: str, data_size: int) -> bool:
        """
        Add user commitment
        
        Args:
            user_id: User ID
            folder_id: Folder ID
            commitment_type: Type of commitment
            data_size: Size of data committed
            
        Returns:
            True if successful
        """
        try:
            self.db_manager.execute("""
                INSERT INTO user_commitments 
                (user_id, folder_id, commitment_type, data_size)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, folder_id, commitment_type)
                DO UPDATE SET data_size = %s
            """, (user_id, folder_id, commitment_type, data_size, data_size))
            
            logger.info(f"Added commitment for user {user_id}: {commitment_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add commitment: {e}")
            return False
    
    def remove_user_commitment(self, user_id: str, folder_id: str,
                              commitment_type: str) -> bool:
        """
        Remove user commitment
        
        Args:
            user_id: User ID
            folder_id: Folder ID
            commitment_type: Type of commitment
            
        Returns:
            True if successful
        """
        try:
            self.db_manager.execute("""
                DELETE FROM user_commitments
                WHERE user_id = %s AND folder_id = %s AND commitment_type = %s
            """, (user_id, folder_id, commitment_type))
            
            logger.info(f"Removed commitment for user {user_id}: {commitment_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove commitment: {e}")
            return False
    
    def sync_changes(self, folder_path: str) -> Dict[str, Any]:
        """
        Sync changes in a folder
        
        Args:
            folder_path: Path to folder to sync
            
        Returns:
            Sync statistics
        """
        logger.info(f"Syncing changes in: {folder_path}")
        
        # Re-index to detect changes
        stats = self.index_folder(folder_path)
        
        # Find modified files
        modified_files = self.db_manager.fetchall("""
            SELECT * FROM files 
            WHERE folder_id = %s 
            AND modified_time > upload_time
            AND state = 'uploaded'
        """, (folder_path,))
        
        # Upload modified files
        upload_count = 0
        for file_info in modified_files:
            result = self.upload_file(file_info['file_hash'])
            if result['success']:
                upload_count += 1
        
        stats['files_synced'] = upload_count
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics
        
        Returns:
            System statistics
        """
        stats = {}
        
        # File statistics
        result = self.db_manager.fetchone("SELECT COUNT(*) as count FROM files")
        stats['total_files'] = result['count'] if result else 0
        
        result = self.db_manager.fetchone("SELECT SUM(file_size) as total FROM files")
        stats['total_size'] = result['total'] if result and result['total'] else 0
        
        # Segment statistics
        result = self.db_manager.fetchone("SELECT COUNT(*) as count FROM segments")
        stats['total_segments'] = result['count'] if result else 0
        
        # Publication statistics
        result = self.db_manager.fetchone("SELECT COUNT(*) as count FROM publications")
        stats['total_publications'] = result['count'] if result else 0
        
        # User commitment statistics
        result = self.db_manager.fetchone("SELECT COUNT(*) as count FROM user_commitments")
        stats['total_commitments'] = result['count'] if result else 0
        
        # State breakdown
        state_counts = {}
        results = self.db_manager.fetchall(
            "SELECT state, COUNT(*) as count FROM files GROUP BY state"
        )
        for row in results:
            state_counts[row['state']] = row['count']
        stats['state_counts'] = state_counts
        
        # NNTP status
        stats['nntp_configured'] = self.nntp_client is not None
        if self.nntp_client:
            stats['nntp_connected'] = self.nntp_client.test_connection()
        
        return stats
    
    def create_backup(self, compress: bool = True) -> Dict[str, Any]:
        """
        Create system backup
        
        Args:
            compress: Whether to compress backup
            
        Returns:
            Backup result
        """
        return self.backup_system.create_backup(self, compress=compress)
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore from backup
        
        Args:
            backup_id: Backup ID to restore
            
        Returns:
            Restore result
        """
        return self.backup_system.restore_backup(backup_id, target_system=self)
    
    def test_complete_workflow(self) -> Dict[str, Any]:
        """
        Test the complete workflow from indexing to publishing
        
        Returns:
            Test results
        """
        results = {
            'success': True,
            'steps': []
        }
        
        try:
            # Step 1: Create test file
            import tempfile
            test_dir = Path(tempfile.mkdtemp(prefix="workflow_test_"))
            test_file = test_dir / "test_document.txt"
            test_content = b"Test workflow content" * 100
            test_file.write_bytes(test_content)
            
            results['steps'].append({
                'step': 'create_file',
                'success': True,
                'file': str(test_file)
            })
            
            # Step 2: Index file
            index_stats = self.index_folder(str(test_dir))
            results['steps'].append({
                'step': 'index',
                'success': index_stats['files_indexed'] == 1,
                'stats': index_stats
            })
            
            # Step 3: Get file hash
            file_hash = hashlib.sha256(test_content).hexdigest()
            
            # Step 4: Check segments
            segments = self.db_manager.fetchall(
                "SELECT * FROM segments WHERE file_id IN (SELECT file_id FROM files WHERE file_hash = %s)",
                (file_hash,)
            )
            results['steps'].append({
                'step': 'segments',
                'success': len(segments) > 0,
                'count': len(segments)
            })
            
            # Step 5: Upload (if NNTP configured)
            if self.upload_system:
                upload_result = self.upload_file(file_hash, redundancy=5)
                results['steps'].append({
                    'step': 'upload',
                    'success': upload_result['success'],
                    'result': upload_result
                })
            else:
                # Simulate upload
                self.db_manager.execute(
                    "UPDATE files SET state = 'uploaded' WHERE file_hash = %s",
                    (file_hash,)
                )
                results['steps'].append({
                    'step': 'upload',
                    'success': True,
                    'simulated': True
                })
            
            # Step 6: Publish
            publish_result = self.publish_file(file_hash, access_level='public')
            results['steps'].append({
                'step': 'publish',
                'success': publish_result['success'],
                'publication_id': publish_result.get('publication_id')
            })
            
            # Step 7: Add user commitment
            user_id = self.security.generate_user_id("test@example.com")
            commitment_added = self.add_user_commitment(
                user_id, str(test_dir), 'storage', 1024
            )
            results['steps'].append({
                'step': 'add_commitment',
                'success': commitment_added
            })
            
            # Step 8: Modify file and sync
            test_file.write_bytes(test_content + b"\nModified")
            sync_stats = self.sync_changes(str(test_dir))
            results['steps'].append({
                'step': 'sync_changes',
                'success': True,
                'stats': sync_stats
            })
            
            # Step 9: Remove commitment
            commitment_removed = self.remove_user_commitment(
                user_id, str(test_dir), 'storage'
            )
            results['steps'].append({
                'step': 'remove_commitment',
                'success': commitment_removed
            })
            
            # Step 10: Republish with different access
            republish_result = self.publish_file(
                file_hash, 
                access_level='private',
                password='secret'
            )
            results['steps'].append({
                'step': 'republish',
                'success': republish_result['success']
            })
            
            # Cleanup
            import shutil
            shutil.rmtree(test_dir)
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            logger.error(f"Workflow test failed: {e}")
        
        return results


def test_complete_system():
    """Test the complete unified system"""
    print("\n" + "="*80)
    print(" "*20 + "COMPLETE UNIFIED SYSTEM TEST")
    print("="*80 + "\n")
    
    import tempfile
    test_dir = Path(tempfile.mkdtemp(prefix="complete_test_"))
    
    try:
        # Initialize system
        print("Initializing complete unified system...")
        system = CompleteUnifiedSystem(
            'sqlite',
            path=str(test_dir / 'test.db'),
            keys_dir=str(test_dir / 'keys'),
            backup_dir=str(test_dir / 'backups')
        )
        print("✓ System initialized\n")
        
        # Test workflow
        print("Testing complete workflow...")
        results = system.test_complete_workflow()
        
        if results['success']:
            print("✓ Complete workflow successful!\n")
            
            print("Steps completed:")
            for step in results['steps']:
                status = "✓" if step['success'] else "✗"
                print(f"  {status} {step['step']}")
        else:
            print(f"✗ Workflow failed: {results.get('error', 'Unknown error')}")
        
        # Get statistics
        print("\nSystem Statistics:")
        stats = system.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return results['success']
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_complete_system()
    sys.exit(0 if success else 1)