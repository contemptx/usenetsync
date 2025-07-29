#!/usr/bin/env python3
"""
Configuration Manager for UsenetSync - PRODUCTION VERSION
Handles all configuration settings, validation, and persistence
Full implementation with no placeholders
"""

import os
import json
import logging
import threading
import copy
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import configparser
import yaml
import hashlib
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Usenet server configuration"""
    name: str
    hostname: str
    port: int
    username: str
    password: str  # Will be encrypted
    posting_group: str = "alt.binaries.test"
    use_ssl: bool = True
    max_connections: int = 10
    priority: int = 1
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class ProcessingConfig:
    """Processing configuration"""
    worker_threads: int = 8
    segment_size: int = 768000  # 750KB
    batch_size: int = 100
    buffer_size: int = 65536
    compression_threshold: float = 0.9
    redundancy_enabled: bool = True
    redundancy_level: int = 2
    redundancy_type: str = "parity"
    
@dataclass
class NetworkConfig:
    """Network configuration"""
    upload_workers: int = 3
    download_workers: int = 3
    max_retries: int = 3
    retry_delay: int = 5
    rate_limit_mbps: float = 0  # 0 = unlimited
    connection_timeout: int = 30
    keepalive_interval: int = 60
    
@dataclass
class StorageConfig:
    """Storage configuration"""
    data_directory: str = "./data"
    temp_directory: str = "./temp"
    download_directory: str = "./downloads"
    log_directory: str = "./logs"
    database_path: str = "./data/usenetsync.db"
    max_temp_storage_gb: int = 50
    cleanup_temp_files: bool = True
    cleanup_age_hours: int = 24
    
@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_encryption: bool = True
    verify_signatures: bool = True
    verify_downloads: bool = True
    max_password_attempts: int = 3
    session_timeout_minutes: int = 30
    secure_delete: bool = True
    
@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "system"  # system, light, dark
    language: str = "en"
    show_hidden_files: bool = False
    confirm_deletions: bool = True
    minimize_to_tray: bool = True
    start_minimized: bool = False
    auto_update_check: bool = True
    
@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    max_log_size_mb: int = 10
    max_log_files: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
class ConfigurationError(Exception):
    """Configuration related errors"""
    pass

class ConfigurationManager:
    """
    Centralized configuration management
    Supports multiple formats, encryption, validation, and hot-reloading
    """
    
    DEFAULT_CONFIG_FILENAME = "usenetsync.conf"
    ENCRYPTED_FIELDS = ["password", "api_key", "secret"]
    
    def __init__(self, config_path: Optional[str] = None, auto_save: bool = True):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
            auto_save: Automatically save on changes
        """
        self.config_path = config_path or self._get_default_config_path()
        self.auto_save = auto_save
        self.logger = logging.getLogger(__name__)
        
        # Thread safety
        self._lock = threading.RLock()
        self._observers: List[Callable] = []
        
        # Configuration sections
        self.servers: List[ServerConfig] = []
        self.processing = ProcessingConfig()
        self.network = NetworkConfig()
        self.storage = StorageConfig()
        self.security = SecurityConfig()
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        
        # Custom settings
        self.custom: Dict[str, Any] = {}
        
        # Encryption for sensitive data
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        
        # Load configuration
        self.load()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration path"""
        # Check common locations
        locations = [
            Path.home() / ".config" / "usenetsync" / self.DEFAULT_CONFIG_FILENAME,
            Path.home() / ".usenetsync" / self.DEFAULT_CONFIG_FILENAME,
            Path("./config") / self.DEFAULT_CONFIG_FILENAME,
            Path(".") / self.DEFAULT_CONFIG_FILENAME
        ]
        
        # Use first existing or first option
        for location in locations:
            if location.exists():
                return str(location)
                
        # Create in user config directory
        config_dir = Path.home() / ".config" / "usenetsync"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / self.DEFAULT_CONFIG_FILENAME)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_path = Path(self.config_path).parent / ".key"
        
        if key_path.exists():
            # Load existing key
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            
            # Save key with restricted permissions
            with open(key_path, 'wb') as f:
                f.write(key)
                
            # Set restrictive permissions on Unix-like systems
            if hasattr(os, 'chmod'):
                os.chmod(key_path, 0o600)
                
            return key
            
    def load(self, path: Optional[str] = None) -> bool:
        """
        Load configuration from file
        
        Args:
            path: Optional path to load from
            
        Returns:
            True if loaded successfully
        """
        load_path = path or self.config_path
        
        with self._lock:
            try:
                if not os.path.exists(load_path):
                    self.logger.info(f"Configuration file not found: {load_path}")
                    self._create_default_config()
                    return True
                    
                # Detect format by extension
                ext = Path(load_path).suffix.lower()
                
                if ext == '.json':
                    config_data = self._load_json(load_path)
                elif ext == '.yaml' or ext == '.yml':
                    config_data = self._load_yaml(load_path)
                elif ext == '.ini' or ext == '.conf':
                    config_data = self._load_ini(load_path)
                else:
                    # Try JSON by default
                    config_data = self._load_json(load_path)
                    
                # Parse configuration data
                self._parse_config_data(config_data)
                
                # Validate configuration
                self.validate()
                
                self.logger.info(f"Configuration loaded from: {load_path}")
                
                # Notify observers
                self._notify_observers('load')
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                raise ConfigurationError(f"Failed to load configuration: {e}")
                
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(path, 'r') as f:
            return json.load(f)
            
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
            
    def _load_ini(self, path: str) -> Dict[str, Any]:
        """Load INI configuration"""
        parser = configparser.ConfigParser()
        parser.read(path)
        
        # Convert to dictionary
        config_data = {}
        for section in parser.sections():
            config_data[section] = dict(parser.items(section))
            
        return config_data
        
    def _parse_config_data(self, data: Dict[str, Any]):
        """Parse configuration data into objects"""
        # Servers
        if 'servers' in data:
            self.servers = []
            for server_data in data['servers']:
                # Decrypt password
                if 'password' in server_data and server_data['password']:
                    server_data['password'] = self._decrypt_value(server_data['password'])
                self.servers.append(ServerConfig.from_dict(server_data))
                
        # Processing
        if 'processing' in data:
            self.processing = ProcessingConfig(**data['processing'])
            
        # Network
        if 'network' in data:
            self.network = NetworkConfig(**data['network'])
            
        # Storage
        if 'storage' in data:
            self.storage = StorageConfig(**data['storage'])
            
        # Security
        if 'security' in data:
            self.security = SecurityConfig(**data['security'])
            
        # UI
        if 'ui' in data:
            self.ui = UIConfig(**data['ui'])
            
        # Logging
        if 'logging' in data:
            self.logging = LoggingConfig(**data['logging'])
            
        # Custom settings
        if 'custom' in data:
            self.custom = data['custom']
            
    def save(self, path: Optional[str] = None) -> bool:
        """
        Save configuration to file
        
        Args:
            path: Optional path to save to
            
        Returns:
            True if saved successfully
        """
        save_path = path or self.config_path
        
        with self._lock:
            try:
                # Create configuration data
                config_data = self._create_config_data()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # Detect format by extension
                ext = Path(save_path).suffix.lower()
                
                if ext == '.json':
                    self._save_json(save_path, config_data)
                elif ext == '.yaml' or ext == '.yml':
                    self._save_yaml(save_path, config_data)
                elif ext == '.ini' or ext == '.conf':
                    self._save_ini(save_path, config_data)
                else:
                    # Default to JSON
                    self._save_json(save_path, config_data)
                    
                self.logger.info(f"Configuration saved to: {save_path}")
                
                # Notify observers
                self._notify_observers('save')
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save configuration: {e}")
                raise ConfigurationError(f"Failed to save configuration: {e}")
                
    def _create_config_data(self) -> Dict[str, Any]:
        """Create configuration data dictionary"""
        config_data = {
            'version': '1.0',
            'updated': datetime.now().isoformat()
        }
        
        # Servers (encrypt passwords)
        config_data['servers'] = []
        for server in self.servers:
            server_dict = server.to_dict()
            if server_dict.get('password'):
                server_dict['password'] = self._encrypt_value(server_dict['password'])
            config_data['servers'].append(server_dict)
            
        # Other sections
        config_data['processing'] = asdict(self.processing)
        config_data['network'] = asdict(self.network)
        config_data['storage'] = asdict(self.storage)
        config_data['security'] = asdict(self.security)
        config_data['ui'] = asdict(self.ui)
        config_data['logging'] = asdict(self.logging)
        
        # Custom settings
        if self.custom:
            config_data['custom'] = self.custom
            
        return config_data
        
    def _save_json(self, path: str, data: Dict[str, Any]):
        """Save JSON configuration"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
            
    def _save_yaml(self, path: str, data: Dict[str, Any]):
        """Save YAML configuration"""
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)
            
    def _save_ini(self, path: str, data: Dict[str, Any]):
        """Save INI configuration"""
        parser = configparser.ConfigParser()
        
        # Flatten nested structures for INI
        for section, values in data.items():
            if isinstance(values, dict):
                parser[section] = {
                    str(k): str(v) for k, v in values.items()
                }
            elif isinstance(values, list):
                # Handle lists (like servers)
                for i, item in enumerate(values):
                    section_name = f"{section}_{i}"
                    if isinstance(item, dict):
                        parser[section_name] = {
                            str(k): str(v) for k, v in item.items()
                        }
                        
        with open(path, 'w') as f:
            parser.write(f)
            
    def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive value"""
        if not value:
            return value
        encrypted = self._cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
        
    def _decrypt_value(self, encrypted: str) -> str:
        """Decrypt sensitive value"""
        if not encrypted:
            return encrypted
        try:
            decoded = base64.b64decode(encrypted.encode())
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode()
        except:
            # Return as-is if decryption fails (might be plain text)
            return encrypted
            
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if valid
            
        Raises:
            ConfigurationError if invalid
        """
        errors = []
        
        # Validate servers
        if not self.servers:
            errors.append("No servers configured")
        else:
            for i, server in enumerate(self.servers):
                if not server.hostname:
                    errors.append(f"Server {i}: Missing hostname")
                if server.port < 1 or server.port > 65535:
                    errors.append(f"Server {i}: Invalid port {server.port}")
                if server.max_connections < 1:
                    errors.append(f"Server {i}: Invalid max_connections {server.max_connections}")
                    
        # Validate processing
        if self.processing.worker_threads < 1:
            errors.append("Invalid worker_threads")
        if self.processing.segment_size < 1:
            errors.append("Invalid segment_size")
        if self.processing.redundancy_level < 0:
            errors.append("Invalid redundancy_level")
            
        # Validate network
        if self.network.upload_workers < 1:
            errors.append("Invalid upload_workers")
        if self.network.download_workers < 1:
            errors.append("Invalid download_workers")
        if self.network.max_retries < 0:
            errors.append("Invalid max_retries")
        if self.network.rate_limit_mbps < 0:
            errors.append("Invalid rate_limit_mbps")
            
        # Validate storage paths
        required_dirs = [
            self.storage.data_directory,
            self.storage.temp_directory,
            self.storage.download_directory,
            self.storage.log_directory
        ]
        
        for dir_path in required_dirs:
            if not dir_path:
                errors.append(f"Missing required directory path")
                
        # Validate logging
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.log_level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {self.logging.log_level}")
            
        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(errors))
            
        return True
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Dot-separated key (e.g., "network.upload_workers")
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        with self._lock:
            try:
                parts = key.split('.')
                value = self
                
                for part in parts:
                    if hasattr(value, part):
                        value = getattr(value, part)
                    elif isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                        
                return value
                
            except:
                return default
                
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key
        
        Args:
            key: Dot-separated key
            value: Value to set
            
        Returns:
            True if set successfully
        """
        with self._lock:
            try:
                parts = key.split('.')
                
                # Navigate to parent
                parent = self
                for part in parts[:-1]:
                    if hasattr(parent, part):
                        parent = getattr(parent, part)
                    elif isinstance(parent, dict) and part in parent:
                        parent = parent[part]
                    else:
                        return False
                        
                # Set value
                final_key = parts[-1]
                if hasattr(parent, final_key):
                    setattr(parent, final_key, value)
                elif isinstance(parent, dict):
                    parent[final_key] = value
                else:
                    return False
                    
                # Auto-save if enabled
                if self.auto_save:
                    self.save()
                    
                # Notify observers
                self._notify_observers('change', key, value)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to set {key}: {e}")
                return False
                
    def add_server(self, server: ServerConfig) -> bool:
        """Add server configuration"""
        with self._lock:
            self.servers.append(server)
            
            if self.auto_save:
                self.save()
                
            self._notify_observers('add_server', server)
            return True
            
    def remove_server(self, hostname: str) -> bool:
        """Remove server by hostname"""
        with self._lock:
            original_count = len(self.servers)
            self.servers = [s for s in self.servers if s.hostname != hostname]
            
            if len(self.servers) < original_count:
                if self.auto_save:
                    self.save()
                    
                self._notify_observers('remove_server', hostname)
                return True
                
            return False
            
    def get_server(self, hostname: str) -> Optional[ServerConfig]:
        """Get server by hostname"""
        with self._lock:
            for server in self.servers:
                if server.hostname == hostname:
                    return server
            return None
            
    def get_enabled_servers(self) -> List[ServerConfig]:
        """Get all enabled servers sorted by priority"""
        with self._lock:
            enabled = [s for s in self.servers if s.enabled]
            return sorted(enabled, key=lambda s: s.priority)
            
    def create_directories(self) -> bool:
        """Create all configured directories"""
        try:
            dirs = [
                self.storage.data_directory,
                self.storage.temp_directory,
                self.storage.download_directory,
                self.storage.log_directory
            ]
            
            for dir_path in dirs:
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                    
            # Create database directory
            db_dir = os.path.dirname(self.storage.database_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            return False
            
    def export_config(self, path: str, include_sensitive: bool = False) -> bool:
        """
        Export configuration to file
        
        Args:
            path: Export path
            include_sensitive: Include sensitive data
            
        Returns:
            True if exported successfully
        """
        with self._lock:
            try:
                config_data = self._create_config_data()
                
                if not include_sensitive:
                    # Remove sensitive data
                    for server in config_data.get('servers', []):
                        server['password'] = '<REDACTED>'
                        
                # Always save as JSON for exports
                with open(path, 'w') as f:
                    json.dump(config_data, f, indent=2, sort_keys=True)
                    
                self.logger.info(f"Configuration exported to: {path}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to export configuration: {e}")
                return False
                
    def import_config(self, path: str, merge: bool = False) -> bool:
        """
        Import configuration from file
        
        Args:
            path: Import path
            merge: Merge with existing config
            
        Returns:
            True if imported successfully
        """
        try:
            # Load the import file
            temp_config = ConfigurationManager(path, auto_save=False)
            
            with self._lock:
                if merge:
                    # Merge servers
                    existing_hosts = {s.hostname for s in self.servers}
                    for server in temp_config.servers:
                        if server.hostname not in existing_hosts:
                            self.servers.append(server)
                            
                    # Merge custom settings
                    self.custom.update(temp_config.custom)
                else:
                    # Replace everything
                    self.servers = temp_config.servers
                    self.processing = temp_config.processing
                    self.network = temp_config.network
                    self.storage = temp_config.storage
                    self.security = temp_config.security
                    self.ui = temp_config.ui
                    self.logging = temp_config.logging
                    self.custom = temp_config.custom
                    
                if self.auto_save:
                    self.save()
                    
                self._notify_observers('import')
                
                self.logger.info(f"Configuration imported from: {path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
            
    def reset_to_defaults(self, section: Optional[str] = None) -> bool:
        """
        Reset configuration to defaults
        
        Args:
            section: Optional section to reset
            
        Returns:
            True if reset successfully
        """
        with self._lock:
            if section:
                # Reset specific section
                if section == 'processing':
                    self.processing = ProcessingConfig()
                elif section == 'network':
                    self.network = NetworkConfig()
                elif section == 'storage':
                    self.storage = StorageConfig()
                elif section == 'security':
                    self.security = SecurityConfig()
                elif section == 'ui':
                    self.ui = UIConfig()
                elif section == 'logging':
                    self.logging = LoggingConfig()
                else:
                    return False
            else:
                # Reset everything
                self._create_default_config()
                
            if self.auto_save:
                self.save()
                
            self._notify_observers('reset', section)
            
            return True
            
    def _create_default_config(self):
        """Create default configuration"""
        # Add default server
        self.servers = [
            ServerConfig(
                name="Primary",
                hostname="news.example.com",
                port=563,
                username="",
                password="",
                use_ssl=True,
                max_connections=10,
                priority=1,
                enabled=True
            )
        ]
        
        # Use dataclass defaults
        self.processing = ProcessingConfig()
        self.network = NetworkConfig()
        self.storage = StorageConfig()
        self.security = SecurityConfig()
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        self.custom = {}
        
    def add_observer(self, callback: Callable):
        """Add configuration change observer"""
        with self._lock:
            if callback not in self._observers:
                self._observers.append(callback)
                
    def remove_observer(self, callback: Callable):
        """Remove configuration change observer"""
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)
                
    def _notify_observers(self, event: str, *args):
        """Notify all observers of configuration change"""
        for observer in self._observers:
            try:
                observer(event, *args)
            except Exception as e:
                self.logger.error(f"Observer notification failed: {e}")
                
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        with self._lock:
            return {
                'servers': len(self.servers),
                'enabled_servers': len(self.get_enabled_servers()),
                'worker_threads': self.processing.worker_threads,
                'upload_workers': self.network.upload_workers,
                'download_workers': self.network.download_workers,
                'redundancy_enabled': self.processing.redundancy_enabled,
                'redundancy_level': self.processing.redundancy_level,
                'rate_limit': f"{self.network.rate_limit_mbps} Mbps" if self.network.rate_limit_mbps > 0 else "Unlimited",
                'encryption_enabled': self.security.enable_encryption,
                'verify_downloads': self.security.verify_downloads
            }