#!/usr/bin/env python3
"""
Unified Configuration Module - Central configuration management
Production-ready with environment support and validation
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UnifiedConfig:
    """Complete unified configuration for UsenetSync"""
    
    # Database settings
    database_type: str = "sqlite"
    database_path: str = os.environ.get('USENETSYNC_DB', "data/usenetsync.db")
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "usenetsync"
    database_user: str = "usenetsync"
    database_password: str = ""
    database_pool_size: int = 10
    
    # NNTP settings
    nntp_servers: List[Dict[str, Any]] = field(default_factory=list)
    nntp_max_connections: int = 10
    nntp_timeout: int = 30
    nntp_retry_attempts: int = 3
    nntp_ssl_enabled: bool = True
    
    # Indexing settings
    indexing_segment_size: int = 768000  # 750KB
    indexing_worker_threads: int = 8
    indexing_batch_size: int = 100
    indexing_buffer_size: int = 65536
    indexing_enable_versioning: bool = True
    indexing_compression_level: int = 9
    
    # Upload settings
    upload_priority_levels: int = 5
    upload_worker_threads: int = 4
    upload_batch_size: int = 50
    upload_rate_limit_mbps: Optional[float] = None
    upload_newsgroups: List[str] = field(default_factory=lambda: ["alt.binaries.test"])
    
    # Download settings
    download_worker_threads: int = 4
    download_parallel_segments: int = 10
    download_resume_enabled: bool = True
    download_verify_integrity: bool = True
    download_rate_limit_mbps: Optional[float] = None
    
    # Security settings
    security_encryption_algorithm: str = "AES-256-GCM"
    security_key_derivation: str = "scrypt"
    security_pbkdf2_iterations: int = 100000
    security_scrypt_n: int = 16384
    security_scrypt_r: int = 8
    security_scrypt_p: int = 1
    security_enable_zero_knowledge: bool = True
    
    # Publishing settings
    publishing_default_expiry_days: int = 30
    publishing_max_share_size_gb: int = 100
    publishing_enable_password_protection: bool = True
    publishing_enable_user_commitments: bool = True
    
    # Performance settings
    performance_cache_enabled: bool = True
    performance_cache_size_mb: int = 256
    performance_streaming_enabled: bool = True
    performance_chunk_size: int = 10000
    performance_enable_profiling: bool = False
    
    # Monitoring settings
    monitoring_enabled: bool = True
    monitoring_prometheus_enabled: bool = False
    monitoring_prometheus_port: int = 9090
    monitoring_log_level: str = "INFO"
    monitoring_log_file: Optional[str] = "logs/usenetsync.log"
    
    # API settings
    api_enabled: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_cors_enabled: bool = True
    api_cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_auth_enabled: bool = True
    api_rate_limit_per_minute: int = 60
    
    # GUI settings
    gui_enabled: bool = True
    gui_auto_update: bool = True
    gui_theme: str = "dark"
    gui_language: str = "en"
    
    # Backup settings
    backup_enabled: bool = True
    backup_schedule: str = "daily"
    backup_retention_days: int = 30
    backup_path: str = "backups"
    backup_encryption_enabled: bool = True
    
    # System settings
    system_data_directory: str = "data"
    system_temp_directory: str = "temp"
    system_log_directory: str = "logs"
    system_max_file_size_gb: int = 20
    system_enable_auto_cleanup: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'UnifiedConfig':
        """Load configuration from file"""
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        with open(path, 'r') as f:
            if path.suffix == '.json':
                data = json.load(f)
            elif path.suffix in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedConfig':
        """Create config from dictionary"""
        config = cls()
        
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")
        
        return config
    
    @classmethod
    def from_env(cls) -> 'UnifiedConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Map environment variables to config attributes
        env_mapping = {
            'USENETSYNC_DATABASE_TYPE': 'database_type',
            'USENETSYNC_DATABASE_PATH': 'database_path',
            'USENETSYNC_DATABASE_HOST': 'database_host',
            'USENETSYNC_DATABASE_PORT': ('database_port', int),
            'USENETSYNC_DATABASE_NAME': 'database_name',
            'USENETSYNC_DATABASE_USER': 'database_user',
            'USENETSYNC_DATABASE_PASSWORD': 'database_password',
            'USENETSYNC_API_PORT': ('api_port', int),
            'USENETSYNC_API_HOST': 'api_host',
            'USENETSYNC_LOG_LEVEL': 'monitoring_log_level',
        }
        
        for env_var, config_attr in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                if isinstance(config_attr, tuple):
                    attr_name, converter = config_attr
                    setattr(config, attr_name, converter(value))
                else:
                    setattr(config, config_attr, value)
        
        # Load NNTP servers from environment
        nntp_servers_json = os.environ.get('USENETSYNC_NNTP_SERVERS')
        if nntp_servers_json:
            try:
                config.nntp_servers = json.loads(nntp_servers_json)
            except json.JSONDecodeError:
                logger.error("Invalid NNTP servers JSON in environment")
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)
    
    def to_file(self, config_path: str):
        """Save configuration to file"""
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        
        with open(path, 'w') as f:
            if path.suffix == '.json':
                json.dump(data, f, indent=2)
            elif path.suffix in ['.yml', '.yaml']:
                yaml.safe_dump(data, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate database settings
        if self.database_type not in ['sqlite', 'postgresql']:
            errors.append(f"Invalid database type: {self.database_type}")
        
        if self.database_type == 'postgresql':
            if not self.database_password:
                errors.append("PostgreSQL password is required")
        
        # Validate paths
        for path_attr in ['database_path', 'backup_path', 'system_data_directory']:
            path = getattr(self, path_attr)
            if not path:
                errors.append(f"Path {path_attr} is required")
        
        # Validate numeric ranges
        if self.indexing_segment_size < 1024:
            errors.append("Segment size must be at least 1KB")
        
        if self.upload_priority_levels < 1 or self.upload_priority_levels > 10:
            errors.append("Priority levels must be between 1 and 10")
        
        # Validate NNTP servers
        if self.nntp_servers:
            for i, server in enumerate(self.nntp_servers):
                if 'host' not in server:
                    errors.append(f"NNTP server {i} missing host")
                if 'port' not in server:
                    errors.append(f"NNTP server {i} missing port")
        
        return errors
    
    def ensure_directories(self):
        """Create required directories"""
        directories = [
            self.system_data_directory,
            self.system_temp_directory,
            self.system_log_directory,
            self.backup_path,
            Path(self.database_path).parent if self.database_type == 'sqlite' else None
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_nntp_server(self, index: int = 0) -> Optional[Dict[str, Any]]:
        """Get NNTP server configuration by index"""
        if index < len(self.nntp_servers):
            return self.nntp_servers[index]
        return None
    
    def add_nntp_server(self, host: str, port: int = 119, 
                       username: Optional[str] = None,
                       password: Optional[str] = None,
                       ssl: bool = False,
                       max_connections: int = 10):
        """Add NNTP server configuration"""
        server = {
            'host': host,
            'port': port,
            'ssl': ssl,
            'max_connections': max_connections
        }
        
        if username and password:
            server['username'] = username
            server['password'] = password
        
        self.nntp_servers.append(server)
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.database_type == 'sqlite':
            return f"sqlite:///{self.database_path}"
        else:
            return (f"postgresql://{self.database_user}:{self.database_password}@"
                   f"{self.database_host}:{self.database_port}/{self.database_name}")
    
    def __str__(self) -> str:
        """String representation"""
        return f"UnifiedConfig(database={self.database_type}, api={self.api_host}:{self.api_port})"


# Global config instance
_global_config: Optional[UnifiedConfig] = None

def load_config(config_path: Optional[str] = None) -> UnifiedConfig:
    """Load configuration from file or environment"""
    global _global_config
    
    if _global_config is None:
        if config_path and Path(config_path).exists():
            _global_config = UnifiedConfig.from_file(config_path)
        elif os.environ.get('USENETSYNC_CONFIG'):
            _global_config = UnifiedConfig.from_file(os.environ['USENETSYNC_CONFIG'])
        else:
            # Try standard locations
            for path in ['config.json', 'config.yaml', '/etc/usenetsync/config.json']:
                if Path(path).exists():
                    _global_config = UnifiedConfig.from_file(path)
                    break
            else:
                # Fall back to environment or defaults
                _global_config = UnifiedConfig.from_env()
        
        # Validate configuration
        errors = _global_config.validate()
        if errors:
            logger.warning(f"Configuration validation errors: {errors}")
        
        # Ensure directories exist
        _global_config.ensure_directories()
    
    return _global_config

def get_config() -> UnifiedConfig:
    """Get current configuration"""
    if _global_config is None:
        return load_config()
    return _global_config

def set_config(config: UnifiedConfig):
    """Set global configuration"""
    global _global_config
    _global_config = config