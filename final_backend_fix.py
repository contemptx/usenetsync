#!/usr/bin/env python3
"""
Main UsenetSync application entry point
Integrates all components into a cohesive system
"""

import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_database_manager import DatabaseConfig
from production_db_wrapper import ProductionDatabaseManager
from enhanced_security_system import EnhancedSecuritySystem
from production_nntp_client import ProductionNNTPClient
from segment_packing_system import SegmentPackingSystem
from enhanced_upload_system import EnhancedUploadSystem
from versioned_core_index_system import VersionedCoreIndexSystem
from simplified_binary_index import SimplifiedBinaryIndex
from enhanced_download_system import EnhancedDownloadSystem
from publishing_system import PublishingSystem
from user_management import UserManager
from configuration_manager import ConfigurationManager, ServerConfig
from monitoring_system import MonitoringSystem
from segment_retrieval_system import SegmentRetrievalSystem
from upload_queue_manager import SmartQueueManager

class UsenetSync:
    """Main application class integrating all components"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing UsenetSync...")
        
        # Load configuration
        self.config = ConfigurationManager(config_path)
        
        # Create directories
        self.config.create_directories()
        
        # Ensure database directory exists and path is valid
        db_path = self.config.storage.database_path
        if not db_path or db_path.strip() == "":
            db_path = "data/usenetsync.db"
            self.config.storage.database_path = db_path
        
        # Create database directory
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database with production wrapper
        db_config = DatabaseConfig(
            path=db_path,
            pool_size=self.config.get('database.pool_size', 10)
        )
        self.db = ProductionDatabaseManager(
            config=db_config,
            enable_monitoring=True,
            enable_retry=True,
            log_file=str(Path(self.config.storage.log_directory) / 'database.log')
        )
        
        # Initialize monitoring early
        self.monitoring = MonitoringSystem({
            'log_directory': self.config.storage.log_directory,
            'operations_db': str(Path(self.config.storage.log_directory) / 'operations.db')
        })
        
        # Initialize security system
        self.security = EnhancedSecuritySystem(self.db)
        
        # Initialize user management
        self.user = UserManager(self.db, self.security)
        
        # Initialize NNTP client
        self._init_nntp_client()
        
        # Create config dictionary for components that need it
        component_config = {
            'worker_threads': 8,
            'segment_size': 768000,
            'batch_size': 100,
            'buffer_size': 65536,
            'upload_workers': 3,
            'max_retries': 3,
            'retry_delay': 5,
            'max_connections': 4
        }
        
        # Initialize core systems with proper configuration
        # SegmentPackingSystem(db_manager, config)
        self.segment_packing = SegmentPackingSystem(self.db, component_config)
        
        # EnhancedUploadSystem(db_manager, nntp_client, security_system, config)
        self.upload_system = EnhancedUploadSystem(
            self.db, self.nntp, self.security, component_config
        )
        
        # EnhancedDownloadSystem(db_manager, nntp_client, security_system, config)
        self.download_system = EnhancedDownloadSystem(
            self.db, self.nntp, self.security, component_config
        )
        
        # VersionedCoreIndexSystem(db_manager, security_system, config)
        self.index_system = VersionedCoreIndexSystem(
            self.db, self.security, component_config
        )
        
        # SmartQueueManager(db_manager, config)
        self.queue_manager = SmartQueueManager(
            self.db, component_config
        )
        
        # Initialize publishing system
        self.publishing = PublishingSystem(
            self.db, self.security, self.upload_system,
            self.nntp, self.index_system, SimplifiedBinaryIndex,
            self.config.__dict__
        )
        
        self.logger.info("UsenetSync initialization complete")
        
    def _init_nntp_client(self):
        """Initialize NNTP client with multi-server support"""
        enabled_servers = [s for s in self.config.servers if s.enabled]
        
        if not enabled_servers:
            raise ValueError("No enabled servers configured")
        
        # Sort by priority
        enabled_servers.sort(key=lambda s: s.priority)
        
        # For now, use the primary server (highest priority)
        primary_server = enabled_servers[0]
        
        self.nntp = ProductionNNTPClient(
            host=primary_server.hostname,
            port=primary_server.port,
            username=primary_server.username,
            password=primary_server.password,
            use_ssl=primary_server.use_ssl,
            max_connections=primary_server.max_connections
        )
        
        self.logger.info(
            f"Initialized NNTP client with primary server {primary_server.hostname}:{primary_server.port}"
        )
        if len(enabled_servers) > 1:
            self.logger.info(
                f"Additional {len(enabled_servers) - 1} backup servers configured"
            )
    
    def initialize_user(self, display_name: Optional[str] = None) -> str:
        """Initialize user profile"""
        if self.user.is_initialized():
            self.logger.info("User already initialized")
            return self.user.get_user_id()
            
        user_id = self.user.initialize(display_name)
        self.logger.info(f"User initialized with ID: {user_id[:16]}...")
        return user_id
        
    def index_folder(self, folder_path: str, folder_id: Optional[str] = None,
                    progress_callback=None, reindex: bool = False) -> Dict[str, Any]:
        """Index a folder"""
        with self.monitoring.track_operation('index_folder', 'index'):
            folder_path = str(Path(folder_path).resolve())
            
            if not folder_id:
                # Generate folder ID from path
                import hashlib
                folder_id = hashlib.sha256(folder_path.encode()).hexdigest()
                
            # Check if folder exists in DB
            try:
                existing_folder = self.db.get_folder_by_path(folder_path)
                if existing_folder and not reindex:
                    self.logger.info(f"Folder already indexed: {folder_path}")
                    return {
                        'folder_id': existing_folder['folder_unique_id'],
                        'files_indexed': existing_folder.get('file_count', 0),
                        'status': 'already_indexed'
                    }
            except:
                # Ignore errors in checking existing folder
                pass
            
            # Perform indexing
            result = self.index_system.index_folder(
                folder_path, folder_id, progress_callback
            )
            
            self.logger.info(f"Indexed folder: {folder_path} -> {result['files_indexed']} files")
            return result
    
    def publish_folder(self, folder_id: str, share_type: str = 'public', 
                      authorized_users: Optional[List[str]] = None,
                      password: Optional[str] = None) -> str:
        """Publish a folder as a share"""
        with self.monitoring.track_operation('publish_folder', 'publish'):
            access_string = self.publishing.create_share(
                folder_id, share_type, authorized_users, password
            )
            
            self.logger.info(f"Published folder {folder_id} as {share_type} share")
            return access_string
    
    def download_share(self, access_string: str, destination_path: str,
                      password: Optional[str] = None) -> str:
        """Download a share"""
        with self.monitoring.track_operation('download_share', 'download'):
            result = self.download_system.download_from_access_string(
                access_string, destination_path, password
            )
            
            self.logger.info(f"Downloaded share to: {destination_path}")
            return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        status = {
            'user': None,
            'folders': [],
            'upload_queue': {},
            'active_uploads': {},
            'active_downloads': {},
            'published_shares': {},
            'nntp_servers': {}
        }
        
        # User status
        try:
            if self.user.is_initialized():
                user_id = self.user.get_user_id()
                
                # Get folders safely
                try:
                    folders = self.db.get_indexed_folders()
                except:
                    folders = []
                
                total_files = sum(f.get('file_count', 0) for f in folders)
                total_size = sum(f.get('total_size', 0) for f in folders)
                
                status['user'] = {
                    'user_id': user_id,
                    'display_name': self.user.get_display_name(),
                    'folders': len(folders),
                    'files': total_files,
                    'total_size': total_size
                }
        except Exception as e:
            self.logger.warning(f"Error getting user status: {e}")
        
        # Folders
        try:
            status['folders'] = self.db.get_indexed_folders()
        except:
            status['folders'] = []
        
        # Upload queue
        try:
            queue_stats = self.queue_manager.get_stats()
            status['upload_queue'] = queue_stats
        except:
            status['upload_queue'] = {'error': 'Queue manager not available'}
        
        # NNTP status
        try:
            if hasattr(self, 'nntp') and self.nntp:
                nntp_stats = self.nntp.connection_pool.get_stats()
                status['nntp_servers'] = {'connection_pool': nntp_stats}
        except:
            status['nntp_servers'] = {'error': 'NNTP not available'}
        
        return status
    
    def cleanup(self):
        """Cleanup resources and temporary files"""
        try:
            # Close NNTP connections
            if hasattr(self, 'nntp') and self.nntp:
                self.nntp.connection_pool.close()
            
            # Cleanup monitoring
            if hasattr(self, 'monitoring'):
                self.monitoring.cleanup()
            
            # Cleanup database connections
            if hasattr(self, 'db'):
                self.db.close()
                
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UsenetSync - Secure Usenet File Synchronization')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        app = UsenetSync(args.config)
        
        # Basic status check
        status = app.get_status()
        print("UsenetSync Status:")
        print(f"User: {'Initialized' if status['user'] else 'Not initialized'}")
        print(f"Folders: {len(status['folders'])}")
        
        if status['user']:
            print(f"Files: {status['user']['files']:,}")
            print(f"Total Size: {status['user']['total_size']:,} bytes")
        
        app.cleanup()
        
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())