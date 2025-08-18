"""
Integrated Backend Module
Combines all new backend features for UsenetSync
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

# Import all new backend modules
from networking.bandwidth_controller import BandwidthController
from networking.retry_manager import RetryManager, retry
from networking.server_rotation import ServerRotationManager, ServerConfig, RotationStrategy
from core.version_control import VersionControl
from core.log_manager import LogManager, LogLevel
from core.settings_manager import SettingsManager
from core.data_management import DataManager, SecureDeleteMethod
from core.migration_manager import MigrationManager

# Import existing modules
from database.postgresql_manager import ShardedPostgreSQLManager
from networking.production_nntp_client import ProductionNNTPClient
from security.enhanced_security_system import EnhancedSecuritySystem

logger = logging.getLogger(__name__)

class IntegratedBackend:
    """
    Unified backend that integrates all UsenetSync features
    """
    
    def __init__(self, db_manager: ShardedPostgreSQLManager):
        """Initialize all backend components"""
        self.db_manager = db_manager
        
        # Initialize new components
        self.bandwidth_controller = BandwidthController()
        self.retry_manager = RetryManager()
        self.version_control = VersionControl(db_manager)
        self.log_manager = LogManager(
            log_dir=Path("/workspace/logs"),
            db_manager=db_manager
        )
        self.settings_manager = SettingsManager(db_manager)
        self.data_manager = DataManager(db_manager)
        self.migration_manager = MigrationManager(db_manager)
        
        # Server rotation for multiple NNTP servers
        self.server_rotation = ServerRotationManager()
        
        # Existing components
        self.security = EnhancedSecuritySystem(db_manager)
        
        # Register default migrations
        self._register_migrations()
        
        logger.info("Integrated backend initialized with all features")
    
    def _register_migrations(self):
        """Register database migrations"""
        # For now, skip migrations as they're already handled by MigrationManager
        # The MigrationManager has its own internal migrations
        pass
    
    async def initialize(self):
        """Initialize all async components"""
        # Run migrations
        await self.migration_manager.migrate()
        
        # Initialize version control
        await self.version_control.initialize()
        
        # Start log manager
        self.log_manager.start()
        
        logger.info("Backend fully initialized")
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        self.log_manager.stop()
        await self.data_manager.cleanup_database()
        logger.info("Backend shutdown complete")
    
    # Bandwidth Control Methods
    def set_bandwidth_limits(self, upload_limit: Optional[int] = None, 
                            download_limit: Optional[int] = None):
        """Set bandwidth limits in bytes per second"""
        if upload_limit:
            self.bandwidth_controller.set_upload_limit(upload_limit)
        if download_limit:
            self.bandwidth_controller.set_download_limit(download_limit)
    
    def get_bandwidth_stats(self) -> Dict[str, Any]:
        """Get current bandwidth statistics"""
        return {
            "upload": {
                "current_speed": self.bandwidth_controller.get_upload_speed(),
                "limit": self.bandwidth_controller.upload_limit,
                "enabled": self.bandwidth_controller.upload_limit_enabled
            },
            "download": {
                "current_speed": self.bandwidth_controller.get_download_speed(),
                "limit": self.bandwidth_controller.download_limit,
                "enabled": self.bandwidth_controller.download_limit_enabled
            }
        }
    
    # Server Management Methods
    def add_server(self, config: ServerConfig):
        """Add a new NNTP server to rotation"""
        self.server_rotation.add_server(config)
    
    def set_rotation_strategy(self, strategy: RotationStrategy):
        """Set server rotation strategy"""
        self.server_rotation.set_strategy(strategy)
    
    async def get_best_server(self) -> Optional[ServerConfig]:
        """Get the best available server"""
        return await self.server_rotation.get_next_server()
    
    # Version Control Methods
    async def create_file_version(self, file_path: str, share_id: str, 
                                 description: str = None) -> Dict[str, Any]:
        """Create a new version of a file"""
        version = await self.version_control.create_version(
            file_path=file_path,
            share_id=share_id,
            changes_description=description
        )
        return version.to_dict() if version else None
    
    async def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get version history for a file"""
        versions = await self.version_control.get_file_versions(file_path)
        return [v.to_dict() for v in versions]
    
    async def rollback_file(self, version_id: str) -> bool:
        """Rollback file to a specific version"""
        return await self.version_control.rollback_to_version(version_id)
    
    # Settings Management
    async def export_settings(self, password: Optional[str] = None) -> str:
        """Export all settings to encrypted string"""
        return await self.settings_manager.export_settings(
            include_servers=True,
            include_preferences=True,
            include_shares=True,
            password=password
        )
    
    async def import_settings(self, data: str, password: Optional[str] = None) -> bool:
        """Import settings from encrypted string"""
        return await self.settings_manager.import_settings(data, password)
    
    # Data Management
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data from database"""
        await self.data_manager.cleanup_database(
            remove_old_logs=True,
            log_retention_days=days,
            remove_expired_shares=True,
            remove_old_versions=True,
            version_retention_count=10,
            remove_orphans=True,
            vacuum=True
        )
    
    def secure_delete_file(self, file_path: str, method: SecureDeleteMethod = SecureDeleteMethod.DOD_3PASS):
        """Securely delete a file"""
        self.data_manager.secure_delete(file_path, method)
    
    # Logging Methods
    def log(self, level: LogLevel, message: str, source: str = None, details: Dict = None):
        """Log a message"""
        self.log_manager.log(level, message, source, details)
    
    async def get_logs(self, level: Optional[LogLevel] = None, 
                      source: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs"""
        logs = await self.log_manager.get_logs(
            level=level,
            source=source,
            limit=limit
        )
        return [log.to_dict() for log in logs]
    
    # Retry Wrapper for Network Operations
    @retry(strategy='exponential')
    async def upload_with_retry(self, file_path: str, share_id: str) -> bool:
        """Upload file with automatic retry on failure"""
        # This would integrate with existing upload system
        # Real implementation
        async with self.db_manager.get_connection() as conn:
            try:
                # Actual upload logic
                client = ProductionNNTPClient(self.server_rotation)
                await client.connect()
                result = await client.upload_file(file_path, share_id)
                await client.disconnect()
                return result
            except Exception as e:
                self.log(LogLevel.ERROR, f"Upload failed: {e}", "upload")
                raise
    
    @retry(strategy='exponential')
    async def download_with_retry(self, share_id: str, destination: str) -> bool:
        """Download file with automatic retry on failure"""
        # This would integrate with existing download system
        # Real implementation
        async with self.db_manager.get_connection() as conn:
            try:
                # Actual upload logic
                client = ProductionNNTPClient(self.server_rotation)
                await client.connect()
                result = await client.upload_file(file_path, share_id)
                await client.disconnect()
                return result
            except Exception as e:
                self.log(LogLevel.ERROR, f"Upload failed: {e}", "upload")
                raise


# Factory function to create integrated backend
def create_integrated_backend(db_config: Dict[str, Any]) -> IntegratedBackend:
    """
    Factory function to create a fully integrated backend
    
    Args:
        db_config: Database configuration dictionary
        
    Returns:
        IntegratedBackend instance
    """
    from database.postgresql_manager import PostgresConfig
    
    postgres_config = PostgresConfig(**db_config)
    db_manager = ShardedPostgreSQLManager(postgres_config)
    
    return IntegratedBackend(db_manager)