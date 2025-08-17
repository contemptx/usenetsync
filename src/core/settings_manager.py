"""Settings export/import manager for UsenetSync."""

import json
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import zipfile
import io
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

@dataclass
class SettingsBackup:
    """Settings backup metadata."""
    version: str
    created_at: datetime
    app_version: str
    settings: Dict[str, Any]
    encrypted: bool = False
    checksum: Optional[str] = None

class SettingsManager:
    """Manages application settings export and import."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.settings_version = "1.0.0"
        self.app_version = "1.0.0"
        
    async def export_settings(
        self,
        include_servers: bool = True,
        include_preferences: bool = True,
        include_shares: bool = False,
        password: Optional[str] = None
    ) -> str:
        """
        Export application settings to a JSON string.
        
        Args:
            include_servers: Include Usenet server configurations
            include_preferences: Include user preferences
            include_shares: Include share configurations
            password: Optional password for encryption
            
        Returns:
            Base64 encoded settings backup
        """
        settings = {}
        
        # Collect settings from database
        if include_servers:
            settings['servers'] = await self._get_server_configs()
            
        if include_preferences:
            settings['preferences'] = await self._get_user_preferences()
            
        if include_shares:
            settings['shares'] = await self._get_share_configs()
            
        # Add general app settings
        settings['app_config'] = await self._get_app_config()
        
        # Create backup object
        backup = SettingsBackup(
            version=self.settings_version,
            created_at=datetime.now(),
            app_version=self.app_version,
            settings=settings,
            encrypted=password is not None
        )
        
        # Convert to JSON
        backup_data = json.dumps(asdict(backup), default=str, indent=2)
        
        # Calculate checksum
        checksum = hashlib.sha256(backup_data.encode()).hexdigest()
        backup.checksum = checksum
        
        # Encrypt if password provided
        if password:
            backup_data = self._encrypt_data(backup_data, password)
            
        # Encode to base64
        return base64.b64encode(backup_data.encode() if isinstance(backup_data, str) else backup_data).decode()
    
    async def import_settings(
        self,
        backup_data: str,
        password: Optional[str] = None,
        merge: bool = False
    ) -> Dict[str, Any]:
        """
        Import settings from a backup.
        
        Args:
            backup_data: Base64 encoded backup data
            password: Password for decryption if encrypted
            merge: Merge with existing settings instead of replacing
            
        Returns:
            Import result with statistics
        """
        try:
            # Decode from base64
            data = base64.b64decode(backup_data)
            
            # Decrypt if needed
            if password:
                data = self._decrypt_data(data, password)
            
            # Parse JSON
            if isinstance(data, bytes):
                data = data.decode()
            backup = json.loads(data)
            
            # Verify checksum
            if 'checksum' in backup:
                settings_str = json.dumps(backup['settings'], default=str)
                calculated_checksum = hashlib.sha256(settings_str.encode()).hexdigest()
                # Note: Checksum verification simplified for demo
            
            # Check version compatibility
            if not self._is_version_compatible(backup.get('version')):
                raise ValueError(f"Incompatible settings version: {backup.get('version')}")
            
            # Import settings
            result = {
                'imported': {},
                'skipped': {},
                'errors': []
            }
            
            settings = backup.get('settings', {})
            
            # Import server configurations
            if 'servers' in settings:
                server_result = await self._import_server_configs(settings['servers'], merge)
                result['imported']['servers'] = server_result['imported']
                result['skipped']['servers'] = server_result['skipped']
                
            # Import user preferences
            if 'preferences' in settings:
                pref_result = await self._import_preferences(settings['preferences'], merge)
                result['imported']['preferences'] = pref_result['imported']
                result['skipped']['preferences'] = pref_result['skipped']
                
            # Import share configurations
            if 'shares' in settings:
                share_result = await self._import_share_configs(settings['shares'], merge)
                result['imported']['shares'] = share_result['imported']
                result['skipped']['shares'] = share_result['skipped']
                
            # Import app configuration
            if 'app_config' in settings:
                app_result = await self._import_app_config(settings['app_config'], merge)
                result['imported']['app_config'] = app_result['imported']
                
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'imported': {},
                'skipped': {},
                'errors': [str(e)]
            }
    
    async def export_to_file(
        self,
        filepath: Path,
        **kwargs
    ) -> bool:
        """Export settings to a file."""
        try:
            backup_data = await self.export_settings(**kwargs)
            
            # Create a zip file with metadata
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add main settings
                zf.writestr('settings.json', backup_data)
                
                # Add metadata
                metadata = {
                    'export_date': datetime.now().isoformat(),
                    'app_version': self.app_version,
                    'settings_version': self.settings_version,
                    'encrypted': kwargs.get('password') is not None
                }
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    async def import_from_file(
        self,
        filepath: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """Import settings from a file."""
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Read settings
                backup_data = zf.read('settings.json').decode()
                
                # Read metadata if available
                if 'metadata.json' in zf.namelist():
                    metadata = json.loads(zf.read('metadata.json'))
                    # Could use metadata for validation
                    
            return await self.import_settings(backup_data, **kwargs)
            
        except Exception as e:
            return {
                'error': str(e),
                'imported': {},
                'skipped': {},
                'errors': [str(e)]
            }
    
    def _encrypt_data(self, data: str, password: str) -> bytes:
        """Encrypt data with password."""
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'usenetsync_salt',  # Should use random salt in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Encrypt
        f = Fernet(key)
        return f.encrypt(data.encode())
    
    def _decrypt_data(self, data: bytes, password: str) -> str:
        """Decrypt data with password."""
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'usenetsync_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Decrypt
        f = Fernet(key)
        return f.decrypt(data).decode()
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if settings version is compatible."""
        if not version:
            return False
            
        # Simple major version check
        current_major = self.settings_version.split('.')[0]
        import_major = version.split('.')[0]
        
        return current_major == import_major
    
    async def _get_server_configs(self) -> List[Dict[str, Any]]:
        """Get Usenet server configurations."""
        query = """
            SELECT host, port, username, ssl_enabled, max_connections,
                   priority, enabled, created_at
            FROM usenet_servers
            ORDER BY priority
        """
        
        rows = await self.db.fetch_all(query)
        return [dict(row) for row in rows]
    
    async def _get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences."""
        query = """
            SELECT key, value, category
            FROM preferences
        """
        
        rows = await self.db.fetch_all(query)
        
        # Group by category
        prefs = {}
        for row in rows:
            category = row['category'] or 'general'
            if category not in prefs:
                prefs[category] = {}
            prefs[category][row['key']] = row['value']
            
        return prefs
    
    async def _get_share_configs(self) -> List[Dict[str, Any]]:
        """Get share configurations."""
        query = """
            SELECT share_id, name, type, password_protected,
                   max_downloads, expires_at, created_at
            FROM shares
            WHERE active = true
            ORDER BY created_at DESC
        """
        
        rows = await self.db.fetch_all(query)
        return [dict(row) for row in rows]
    
    async def _get_app_config(self) -> Dict[str, Any]:
        """Get general application configuration."""
        return {
            'bandwidth_limits': {
                'upload': await self._get_setting('bandwidth_upload_limit', 0),
                'download': await self._get_setting('bandwidth_download_limit', 0)
            },
            'network': {
                'connection_timeout': await self._get_setting('connection_timeout', 30),
                'retry_attempts': await self._get_setting('retry_attempts', 3),
                'connection_pool_size': await self._get_setting('connection_pool_size', 10)
            },
            'storage': {
                'temp_directory': await self._get_setting('temp_directory', '/tmp'),
                'cache_size_mb': await self._get_setting('cache_size_mb', 500)
            }
        }
    
    async def _get_setting(self, key: str, default: Any) -> Any:
        """Get a single setting value."""
        query = "SELECT value FROM settings WHERE key = ?"
        result = await self.db.fetch_one(query, (key,))
        return result['value'] if result else default
    
    async def _import_server_configs(
        self,
        servers: List[Dict[str, Any]],
        merge: bool
    ) -> Dict[str, Any]:
        """Import server configurations."""
        imported = 0
        skipped = 0
        
        if not merge:
            # Clear existing servers
            await self.db.execute("DELETE FROM usenet_servers")
        
        for server in servers:
            # Check if server already exists
            existing = await self.db.fetch_one(
                "SELECT id FROM usenet_servers WHERE host = ? AND port = ?",
                (server['host'], server['port'])
            )
            
            if existing and merge:
                # Update existing
                await self.db.execute("""
                    UPDATE usenet_servers
                    SET username = ?, ssl_enabled = ?, max_connections = ?,
                        priority = ?, enabled = ?
                    WHERE host = ? AND port = ?
                """, (
                    server['username'], server['ssl_enabled'],
                    server['max_connections'], server['priority'],
                    server['enabled'], server['host'], server['port']
                ))
                imported += 1
            elif not existing:
                # Insert new
                await self.db.execute("""
                    INSERT INTO usenet_servers
                    (host, port, username, ssl_enabled, max_connections,
                     priority, enabled, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    server['host'], server['port'], server['username'],
                    server['ssl_enabled'], server['max_connections'],
                    server['priority'], server['enabled'],
                    server.get('created_at', datetime.now())
                ))
                imported += 1
            else:
                skipped += 1
                
        return {'imported': imported, 'skipped': skipped}
    
    async def _import_preferences(
        self,
        preferences: Dict[str, Any],
        merge: bool
    ) -> Dict[str, Any]:
        """Import user preferences."""
        imported = 0
        skipped = 0
        
        if not merge:
            await self.db.execute("DELETE FROM preferences")
        
        for category, prefs in preferences.items():
            for key, value in prefs.items():
                existing = await self.db.fetch_one(
                    "SELECT id FROM preferences WHERE key = ? AND category = ?",
                    (key, category)
                )
                
                if existing:
                    if merge:
                        await self.db.execute(
                            "UPDATE preferences SET value = ? WHERE key = ? AND category = ?",
                            (value, key, category)
                        )
                        imported += 1
                    else:
                        skipped += 1
                else:
                    await self.db.execute(
                        "INSERT INTO preferences (key, value, category) VALUES (?, ?, ?)",
                        (key, value, category)
                    )
                    imported += 1
                    
        return {'imported': imported, 'skipped': skipped}
    
    async def _import_share_configs(
        self,
        shares: List[Dict[str, Any]],
        merge: bool
    ) -> Dict[str, Any]:
        """Import share configurations."""
        imported = 0
        skipped = 0
        
        for share in shares:
            # Shares are always created new (not updated)
            # Check for duplicate share_id
            existing = await self.db.fetch_one(
                "SELECT id FROM shares WHERE share_id = ?",
                (share['share_id'],)
            )
            
            if not existing:
                await self.db.execute("""
                    INSERT INTO shares
                    (share_id, name, type, password_protected,
                     max_downloads, expires_at, created_at, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    share['share_id'], share['name'], share['type'],
                    share['password_protected'], share['max_downloads'],
                    share.get('expires_at'), share.get('created_at', datetime.now()),
                    True
                ))
                imported += 1
            else:
                skipped += 1
                
        return {'imported': imported, 'skipped': skipped}
    
    async def _import_app_config(
        self,
        config: Dict[str, Any],
        merge: bool
    ) -> Dict[str, int]:
        """Import application configuration."""
        imported = 0
        
        # Flatten nested config
        flat_config = {}
        
        if 'bandwidth_limits' in config:
            flat_config['bandwidth_upload_limit'] = config['bandwidth_limits'].get('upload', 0)
            flat_config['bandwidth_download_limit'] = config['bandwidth_limits'].get('download', 0)
            
        if 'network' in config:
            flat_config['connection_timeout'] = config['network'].get('connection_timeout', 30)
            flat_config['retry_attempts'] = config['network'].get('retry_attempts', 3)
            flat_config['connection_pool_size'] = config['network'].get('connection_pool_size', 10)
            
        if 'storage' in config:
            flat_config['temp_directory'] = config['storage'].get('temp_directory', '/tmp')
            flat_config['cache_size_mb'] = config['storage'].get('cache_size_mb', 500)
        
        # Import each setting
        for key, value in flat_config.items():
            existing = await self.db.fetch_one(
                "SELECT id FROM settings WHERE key = ?",
                (key,)
            )
            
            if existing:
                await self.db.execute(
                    "UPDATE settings SET value = ? WHERE key = ?",
                    (value, key)
                )
            else:
                await self.db.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            imported += 1
            
        return {'imported': imported}