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
        
        # Initialize database with production wrapper
        db_config = DatabaseConfig(
            path=self.config.storage.database_path,
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
            'operations_db': str(Path(self.config.storage.data_directory) / 'operations.db'),
            'metrics_retention_hours': self.config.get('monitoring.retention_hours', 24)
        })
        
        # Initialize security system
        self.security = EnhancedSecuritySystem(self.db)
        
        # Initialize user management
        self.user = UserManager(self.db, self.security)
        
        # Initialize NNTP client with configured servers
        self._init_nntp_client()
        
        # Initialize segment packing
        self.segment_packer = SegmentPackingSystem(
            self.db, 
            self.config.processing.__dict__
        )
        
        # Initialize upload system with smart queue
        self.queue_manager = SmartQueueManager(self.db, self.config.network.__dict__)
        self.upload_system = EnhancedUploadSystem(
            self.db, self.nntp, self.security, self.config.network.__dict__
        )
        
        # Initialize indexing system
        self.index_system = VersionedCoreIndexSystem(
            self.db, self.security, self.config.processing.__dict__
        )
        
        # Initialize retrieval system for downloads
        from segment_packing_system import RedundancyEngine
        redundancy_engine = RedundancyEngine()
        
        self.retrieval_system = SegmentRetrievalSystem(
            self.nntp, self.db, self.config.network.__dict__
        )
        
        # Initialize download system
        self.download_system = EnhancedDownloadSystem(
            self.db, self.nntp, self.security, self.config.network.__dict__
        )
        
        # Initialize publishing system
        self.publishing_system = PublishingSystem(
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
        # TODO: Implement proper load balancer for multiple servers
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
                    progress_callback=None) -> Dict[str, Any]:
        """Index a folder"""
        with self.monitoring.track_operation('index_folder', 'index'):
            folder_path = str(Path(folder_path).resolve())
            
            if not folder_id:
                # Generate folder ID from path
                import hashlib
                folder_id = hashlib.sha256(folder_path.encode()).hexdigest()
                
            # Check if folder exists in DB
            folder = self.db.get_folder(folder_id)
            
            if folder:
                # Re-index
                self.logger.info(f"Re-indexing folder: {folder_path}")
                result = self.index_system.re_index_folder(
                    folder_path, folder_id, progress_callback
                )
            else:
                # Initial index
                self.logger.info(f"Initial indexing of folder: {folder_path}")
                result = self.index_system.index_folder(
                    folder_path, folder_id, progress_callback
                )
                
            # Record metrics
            self.monitoring.record_metric(
                'folders.indexed', 1, type=self.monitoring.metrics.MetricType.COUNTER
            )
            self.monitoring.record_metric(
                'files.indexed', result['files_processed'],
                type=self.monitoring.metrics.MetricType.COUNTER
            )
            
            return result
            
    def publish_folder(self, folder_id: str, share_type: str = 'private',
                      authorized_users: Optional[List[str]] = None,
                      password: Optional[str] = None,
                      password_hint: Optional[str] = None) -> Dict[str, Any]:
        """Publish a folder"""
        with self.monitoring.track_operation('publish_folder', 'publish'):
            job_id = self.publishing_system.publish_folder(
                folder_id=folder_id,
                share_type=share_type,
                authorized_users=authorized_users,
                password=password,
                password_hint=password_hint
            )
            
            # Wait for completion or return job ID for async tracking
            import time
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status = self.publishing_system.get_job_status(job_id)
                
                if status['state'] in ['published', 'failed']:
                    if status['state'] == 'published':
                        self.monitoring.record_metric(
                            'folders.published', 1,
                            type=self.monitoring.metrics.MetricType.COUNTER
                        )
                        
                    return status
                    
                time.sleep(1)
                
            return {'error': 'Publishing timeout'}
            
    def download_folder(self, access_string: str, destination: str,
                       password: Optional[str] = None,
                       progress_callback=None) -> str:
        """Download a folder from access string"""
        with self.monitoring.track_operation('download_folder', 'download'):
            # Add progress wrapper
            def progress_wrapper(info):
                if progress_callback:
                    progress_callback(info)
                    
                # Record metrics
                if info.get('state') == 'completed':
                    self.monitoring.record_metric(
                        'files.downloaded', 1,
                        type=self.monitoring.metrics.MetricType.COUNTER
                    )
                    
            if progress_callback:
                self.download_system.add_progress_callback(progress_wrapper)
                
            session_id = self.download_system.download_from_access_string(
                access_string, destination, password
            )
            
            self.monitoring.record_metric(
                'download.sessions', 1,
                type=self.monitoring.metrics.MetricType.COUNTER
            )
            
            return session_id
            
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'user': self.user.get_statistics() if self.user.is_initialized() else None,
            'database': self.db.get_database_stats(),
            'monitoring': self.monitoring.get_dashboard_data(),
            'upload_queue': self.queue_manager.get_statistics(),
            'nntp_servers': {
            'connection_pool': self.nntp.connection_pool.get_stats(),
            'server_stats': {
                self.nntp.host: {
                    'host': self.nntp.host,
                    'port': self.nntp.port,
                    'ssl': self.nntp.use_ssl,
                    'max_connections': self.nntp.connection_pool.max_connections,
                    'status': 'connected'
                }
            }
        },
            'active_uploads': self.upload_system.get_statistics(),
            'active_downloads': self.download_system.get_statistics(),
            'published_shares': self.publishing_system.get_statistics()
        }
        
    def cleanup(self):
        """Cleanup old data and temp files"""
        self.logger.info("Running cleanup...")
        
        # Clean old download sessions
        self.db.cleanup_old_sessions(days=30)
        
        # Clean temp files
        self.download_system.cleanup_temp_files(older_than_hours=24)
        
        # Clean old jobs
        self.publishing_system.cleanup_old_jobs(older_than_hours=48)
        
        # Database maintenance
        self.db.vacuum()
        self.db.analyze()
        
        self.logger.info("Cleanup complete")
        
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down UsenetSync...")
        
        # Stop active operations
        self.upload_system.shutdown()
        self.download_system.shutdown()
        
        # Close NNTP connections
        self.nntp.close_all_connections()
        
        # Final monitoring report
        self.monitoring.generate_report(
            str(Path(self.config.storage.log_directory) / 'final_report.json')
        )
        
        # Shutdown monitoring
        self.monitoring.shutdown()
        
        # Close database
        self.db.close()
        
        self.logger.info("Shutdown complete")

# Convenience functions
def create_app(config_path: Optional[str] = None) -> UsenetSync:
    """Create and initialize UsenetSync application"""
    return UsenetSync(config_path)

async def async_main():
    """Async main for future async operations"""
    app = create_app()
    
    # Could add async operations here
    
    return app

if __name__ == '__main__':
    # Example usage
    app = create_app()
    
    # Initialize user if needed
    if not app.user.is_initialized():
        app.initialize_user("Demo User")
        
    # Example: Index a folder
    # result = app.index_folder("/path/to/folder")
    # print(f"Indexed {result['files_processed']} files")
    
    # Example: Publish folder
    # publish_result = app.publish_folder(
    #     folder_id="folder_123",
    #     share_type="public"
    # )
    # print(f"Access string: {publish_result['access_string']}")
    
    # Get status
    status = app.get_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Cleanup and shutdown
    app.cleanup()
    app.shutdown()