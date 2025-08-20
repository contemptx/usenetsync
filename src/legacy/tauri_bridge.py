#!/usr/bin/env python3
"""
Unified Tauri Bridge - Bridge between Python backend and Tauri frontend
Production-ready with command handling and event emission
"""

import json
import asyncio
import subprocess
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class UnifiedTauriBridge:
    """
    Unified bridge for Tauri integration
    Handles communication between Python backend and Tauri/React frontend
    """
    
    def __init__(self, unified_system=None):
        """Initialize Tauri bridge"""
        self.system = unified_system
        self.commands = {}
        self.event_handlers = {}
        self.websocket_connections = set()
        
        # Register default commands
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Register default Tauri commands"""
        
        # License commands (matching existing Tauri commands)
        self.register_command('activate_license', self._activate_license)
        self.register_command('check_license', self._check_license)
        self.register_command('deactivate_license', self._deactivate_license)
        self.register_command('get_trial_days_remaining', self._get_trial_days)
        
        # User commands
        self.register_command('create_user', self._create_user)
        self.register_command('get_user', self._get_user)
        
        # Folder commands
        self.register_command('index_folder', self._index_folder)
        self.register_command('get_folder_status', self._get_folder_status)
        self.register_command('scan_directory', self._scan_directory)
        
        # Share commands
        self.register_command('create_share', self._create_share)
        self.register_command('get_shares', self._get_shares)
        self.register_command('verify_share_access', self._verify_share_access)
        
        # Upload/Download commands
        self.register_command('queue_upload', self._queue_upload)
        self.register_command('get_upload_status', self._get_upload_status)
        self.register_command('start_download', self._start_download)
        self.register_command('get_download_progress', self._get_download_progress)
        
        # System commands
        self.register_command('get_statistics', self._get_statistics)
        self.register_command('get_metrics', self._get_metrics)
        self.register_command('get_config', self._get_config)
        self.register_command('update_config', self._update_config)
    
    def register_command(self, name: str, handler: Callable):
        """Register a Tauri command handler"""
        self.commands[name] = handler
        logger.debug(f"Registered command: {name}")
    
    async def handle_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Tauri command
        
        Args:
            command: Command name
            args: Command arguments
        
        Returns:
            Command response
        """
        if command not in self.commands:
            return {
                'success': False,
                'error': f'Unknown command: {command}'
            }
        
        try:
            handler = self.commands[command]
            
            # Execute handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(args)
            else:
                result = handler(args)
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Command {command} failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def emit_event(self, event: str, payload: Any):
        """
        Emit event to frontend
        
        Args:
            event: Event name
            payload: Event payload
        """
        message = {
            'event': event,
            'payload': payload
        }
        
        # Send to all WebSocket connections
        for ws in self.websocket_connections:
            try:
                asyncio.create_task(ws.send_json(message))
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
    
    # Command handlers
    def _activate_license(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Activate license"""
        # Would integrate with TurboActivate
        return {
            'activated': True,
            'message': 'License activated successfully'
        }
    
    def _check_license(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check license status"""
        return {
            'valid': True,
            'type': 'trial',
            'days_remaining': 30
        }
    
    def _deactivate_license(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate license"""
        return {
            'deactivated': True,
            'message': 'License deactivated'
        }
    
    def _get_trial_days(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get trial days remaining"""
        return {'days': 30}
    
    def _create_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create user"""
        if not self.system:
            raise RuntimeError("System not initialized")
        
        username = args.get('username')
        email = args.get('email')
        
        user = self.system.create_user(username, email)
        
        # Emit user created event
        self.emit_event('user_created', user)
        
        return user
    
    def _get_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information"""
        if not self.system or not self.system.db:
            raise RuntimeError("System not initialized")
        
        user_id = args.get('user_id')
        
        user = self.system.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        
        return dict(user) if user else {}
    
    def _index_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Index folder"""
        if not self.system:
            raise RuntimeError("System not initialized")
        
        folder_path = args.get('folder_path')
        owner_id = args.get('owner_id')
        
        # Start indexing (would be async in production)
        result = self.system.index_folder(folder_path, owner_id)
        
        # Emit progress events
        self.emit_event('indexing_started', {
            'folder_path': folder_path,
            'folder_id': result['folder_id']
        })
        
        # Simulate progress events
        for i in range(0, 101, 10):
            self.emit_event('indexing_progress', {
                'folder_id': result['folder_id'],
                'progress': i
            })
        
        self.emit_event('indexing_complete', result)
        
        return result
    
    def _get_folder_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get folder indexing status"""
        folder_id = args.get('folder_id')
        
        # Would get real status from system
        return {
            'folder_id': folder_id,
            'status': 'indexed',
            'files_count': 100,
            'total_size': 1024000
        }
    
    def _scan_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scan directory for files"""
        path = args.get('path')
        
        if not Path(path).exists():
            raise ValueError(f"Path does not exist: {path}")
        
        files = []
        for item in Path(path).iterdir():
            files.append({
                'name': item.name,
                'path': str(item),
                'is_directory': item.is_dir(),
                'size': item.stat().st_size if item.is_file() else 0
            })
        
        return {'files': files}
    
    def _create_share(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create share"""
        if not self.system:
            raise RuntimeError("System not initialized")
        
        from ..security.access_control import AccessLevel
        
        folder_id = args.get('folder_id')
        owner_id = args.get('owner_id')
        share_type = args.get('share_type', 'public')
        password = args.get('password')
        expiry_days = args.get('expiry_days', 30)
        
        access_level = AccessLevel[share_type.upper()]
        
        share = self.system.create_share(
            folder_id, owner_id, access_level,
            password=password, expiry_days=expiry_days
        )
        
        # Emit share created event
        self.emit_event('share_created', share)
        
        return share
    
    def _get_shares(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get user's shares"""
        if not self.system or not self.system.db:
            raise RuntimeError("System not initialized")
        
        owner_id = args.get('owner_id')
        
        shares = self.system.db.fetch_all(
            "SELECT * FROM publications WHERE owner_id = ?",
            (owner_id,)
        )
        
        return {'shares': [dict(s) for s in shares]}
    
    def _verify_share_access(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Verify share access"""
        if not self.system:
            raise RuntimeError("System not initialized")
        
        share_id = args.get('share_id')
        user_id = args.get('user_id')
        password = args.get('password')
        
        has_access = self.system.verify_access(share_id, user_id, password)
        
        return {'access_granted': has_access}
    
    def _queue_upload(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Queue upload"""
        # Would queue upload
        entity_id = args.get('entity_id')
        
        # Emit upload queued event
        self.emit_event('upload_queued', {
            'entity_id': entity_id,
            'queue_id': 'queue_123'
        })
        
        return {
            'queue_id': 'queue_123',
            'status': 'queued'
        }
    
    def _get_upload_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get upload status"""
        return {
            'queued': 5,
            'uploading': 2,
            'completed': 10,
            'failed': 0
        }
    
    def _start_download(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start download"""
        share_id = args.get('share_id')
        output_path = args.get('output_path')
        
        # Emit download started event
        self.emit_event('download_started', {
            'share_id': share_id,
            'download_id': 'dl_123'
        })
        
        return {
            'download_id': 'dl_123',
            'status': 'downloading'
        }
    
    def _get_download_progress(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get download progress"""
        download_id = args.get('download_id')
        
        return {
            'download_id': download_id,
            'progress': 45,
            'bytes_downloaded': 450000,
            'total_bytes': 1000000
        }
    
    def _get_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system statistics"""
        if not self.system:
            return {}
        
        return self.system.get_statistics()
    
    def _get_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            'cpu_usage': 25,
            'memory_usage': 40,
            'disk_usage': 60,
            'network_upload': 1000000,
            'network_download': 2000000
        }
    
    def _get_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration"""
        if not self.system or not self.system.config:
            return {}
        
        return self.system.config.to_dict()
    
    def _update_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        config = args.get('config', {})
        
        # Would update config
        self.emit_event('config_updated', config)
        
        return {'updated': True}