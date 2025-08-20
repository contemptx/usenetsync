#!/usr/bin/env python3
"""
Complete Tauri Bridge - Handles ALL Tauri commands
Maps all GUI commands to unified backend operations
"""

import json
import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def json_serializable(obj):
    """Convert non-serializable objects to serializable format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.hex()
    elif hasattr(obj, '__dict__'):
        return str(obj)
    return obj


class CompleteTauriBridge:
    """
    Complete bridge handling all Tauri commands
    """
    
    def __init__(self, unified_system):
        """Initialize with unified system"""
        self.system = unified_system
        self.commands = {}
        self._register_all_commands()
    
    def _register_all_commands(self):
        """Register ALL Tauri commands"""
        
        # Share operations
        self.commands['create_share'] = self._create_share
        self.commands['get_shares'] = self._get_shares
        self.commands['download_share'] = self._download_share
        self.commands['get_share_details'] = self._get_share_details
        
        # Folder operations
        self.commands['add_folder'] = self._add_folder
        self.commands['index_folder'] = self._index_folder
        self.commands['index_folder_full'] = self._index_folder
        self.commands['segment_folder'] = self._segment_folder
        self.commands['upload_folder'] = self._upload_folder
        self.commands['publish_folder'] = self._publish_folder
        self.commands['get_folders'] = self._get_folders
        self.commands['folder_info'] = self._folder_info
        self.commands['resync_folder'] = self._resync_folder
        self.commands['delete_folder'] = self._delete_folder
        self.commands['set_folder_access'] = self._set_folder_access
        
        # User management
        self.commands['add_authorized_user'] = self._add_authorized_user
        self.commands['remove_authorized_user'] = self._remove_authorized_user
        self.commands['get_authorized_users'] = self._get_authorized_users
        self.commands['get_user_info'] = self._get_user_info
        self.commands['initialize_user'] = self._initialize_user
        self.commands['is_user_initialized'] = self._is_user_initialized
        
        # System operations
        self.commands['check_database_status'] = self._check_database_status
        self.commands['setup_postgresql'] = self._setup_postgresql
        self.commands['get_system_stats'] = self._get_system_stats
        
        # File operations
        self.commands['select_files'] = self._select_files
        self.commands['select_folder'] = self._select_folder
        
    async def handle_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command from Tauri"""
        if command not in self.commands:
            logger.warning(f"Unknown command: {command}")
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
            logger.error(f"Command {command} failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== SHARE OPERATIONS ====================
    
    def _create_share(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a share"""
        files = args.get('files', [])
        share_type = args.get('share_type', 'public')
        password = args.get('password')
        
        # Get first file's folder
        if not files:
            raise ValueError("No files specified")
        
        # Create share based on type
        folder_id = self._get_folder_id_from_files(files)
        owner_id = self._get_current_user_id()
        
        if share_type == 'public':
            share = self.system.create_public_share(
                folder_id, owner_id, expiry_days=30
            )
        elif share_type == 'private':
            share = self.system.create_private_share(
                folder_id, owner_id, allowed_users=[], expiry_days=30
            )
        elif share_type == 'protected':
            share = self.system.create_protected_share(
                folder_id, owner_id, password, expiry_days=30
            )
        else:
            raise ValueError(f"Unknown share type: {share_type}")
        
        # Return in GUI expected format
        return self._format_share_for_gui(share)
    
    def _get_shares(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all shares"""
        owner_id = args.get('owner_id', self._get_current_user_id())
        
        shares = self.system.db.fetch_all("""
            SELECT * FROM shares 
            WHERE owner_id = ? 
            ORDER BY created_at DESC
        """, (owner_id,))
        
        return [self._format_share_for_gui(dict(s)) for s in shares]
    
    def _download_share(self, args: Dict[str, Any]) -> None:
        """Download a share"""
        share_id = args.get('share_id')
        destination = args.get('destination', './downloads')
        selected_files = args.get('selected_files')
        
        # Start download
        self.system.download.download_share(
            share_id, destination, selected_files
        )
    
    def _get_share_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get share details"""
        share_id = args.get('share_id')
        
        share = self.system.db.fetch_one(
            "SELECT * FROM shares WHERE share_id = ?",
            (share_id,)
        )
        
        if not share:
            raise ValueError(f"Share not found: {share_id}")
        
        return self._format_share_for_gui(dict(share))
    
    # ==================== FOLDER OPERATIONS ====================
    
    def _add_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a folder to the system"""
        path = args.get('path')
        name = args.get('name', Path(path).name)
        
        # Create folder record
        folder_id = hashlib.sha256(path.encode()).hexdigest()
        owner_id = self._get_current_user_id()
        
        self.system.db.insert('folders', {
            'folder_id': folder_id,
            'name': name,
            'path': path,
            'owner_id': owner_id,
            'created_at': time.time()
        })
        
        return {
            'folder_id': folder_id,
            'name': name,
            'path': path,
            'status': 'added'
        }
    
    def _index_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Index a folder"""
        folder_id = args.get('folder_id')
        
        # Get folder info
        folder = self.system.db.fetch_one(
            "SELECT * FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        
        if not folder:
            raise ValueError(f"Folder not found: {folder_id}")
        
        # Index the folder
        result = self.system.indexing.scanner.scan_folder(
            folder['path'], folder_id
        )
        
        # Convert generator to list if needed
        if hasattr(result, '__iter__') and not hasattr(result, '__len__'):
            result = list(result)
        
        return {
            'folder_id': folder_id,
            'files_indexed': len(result) if result else 0,
            'status': 'indexed'
        }
    
    def _segment_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Segment folder for upload"""
        folder_id = args.get('folder_id')
        
        # Get files in folder
        files = self.system.db.fetch_all(
            "SELECT * FROM files WHERE folder_id = ?",
            (folder_id,)
        )
        
        total_segments = 0
        for file in files:
            segments = self.system.segmentation.processor.segment_file(
                file['file_path']
            )
            total_segments += len(segments)
        
        return {
            'folder_id': folder_id,
            'total_segments': total_segments,
            'status': 'segmented'
        }
    
    def _upload_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upload folder to Usenet"""
        folder_id = args.get('folder_id')
        
        # Create upload record
        upload_id = hashlib.sha256(f"{folder_id}_{time.time()}".encode()).hexdigest()
        self.system.db.insert('uploads', {
            'upload_id': upload_id,
            'folder_id': folder_id,
            'status': 'pending',
            'created_at': time.time(),
            'total_segments': 0,
            'uploaded_segments': 0
        })
        
        return {
            'folder_id': folder_id,
            'upload_id': upload_id,
            'status': 'uploading'
        }
    
    def _publish_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Publish folder with access control"""
        folder_id = args.get('folder_id')
        access_type = args.get('access_type', 'public')
        user_ids = args.get('user_ids', [])
        password = args.get('password')
        
        owner_id = self._get_current_user_id()
        
        # Create publication record
        publication_id = hashlib.sha256(f"{folder_id}_{time.time()}".encode()).hexdigest()
        self.system.db.insert('publications', {
            'publication_id': publication_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'access_level': access_type,
            'created_at': time.time(),
            'total_segments': 0
        })
        
        # Handle access control based on type
        if access_type == 'private' and user_ids:
            for user_id in user_ids:
                self.system.db.insert('folder_authorizations', {
                    'folder_id': folder_id,
                    'user_id': user_id,
                    'authorized_at': time.time()
                })
        elif access_type == 'protected' and password:
            # Store password hash (simplified for now)
            pass
        
        return {
            'publication_id': publication_id,
            'folder_id': folder_id,
            'access_type': access_type,
            'status': 'published'
        }
    
    def _get_folders(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all folders"""
        owner_id = args.get('owner_id', self._get_current_user_id())
        
        folders = self.system.db.fetch_all("""
            SELECT f.*, 
                   COUNT(DISTINCT fi.file_id) as file_count,
                   SUM(fi.size) as total_size
            FROM folders f
            LEFT JOIN files fi ON f.folder_id = fi.folder_id
            WHERE f.owner_id = ?
            GROUP BY f.folder_id
            ORDER BY f.created_at DESC
        """, (owner_id,))
        
        return [dict(f) for f in folders]
    
    def _folder_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get folder information"""
        folder_id = args.get('folder_id')
        
        folder = self.system.db.fetch_one("""
            SELECT f.*, 
                   COUNT(DISTINCT fi.file_id) as file_count,
                   COUNT(DISTINCT s.segment_id) as segment_count,
                   SUM(fi.size) as total_size
            FROM folders f
            LEFT JOIN files fi ON f.folder_id = fi.folder_id
            LEFT JOIN segments s ON fi.file_id = s.file_id
            WHERE f.folder_id = ?
            GROUP BY f.folder_id
        """, (folder_id,))
        
        if not folder:
            raise ValueError(f"Folder not found: {folder_id}")
        
        return dict(folder)
    
    def _resync_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Resync folder"""
        folder_id = args.get('folder_id')
        
        # Re-index the folder
        return self._index_folder(args)
    
    def _delete_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete folder"""
        folder_id = args.get('folder_id')
        confirm = args.get('confirm', False)
        
        if not confirm:
            raise ValueError("Deletion not confirmed")
        
        # Delete folder and related data
        self.system.db.execute(
            "DELETE FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        
        return {'deleted': True, 'folder_id': folder_id}
    
    def _set_folder_access(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Set folder access type"""
        folder_id = args.get('folder_id')
        access_type = args.get('access_type')
        password = args.get('password')
        
        # Update folder access
        self.system.db.update('folders', 
            {'access_type': access_type, 'updated_at': time.time()},
            'folder_id = ?',
            (folder_id,)
        )
        
        return {'updated': True}
    
    # ==================== USER MANAGEMENT ====================
    
    def _add_authorized_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add authorized user to folder"""
        folder_id = args.get('folder_id')
        user_id = args.get('user_id')
        
        # Add user authorization
        self.system.db.insert('folder_authorizations', {
            'folder_id': folder_id,
            'user_id': user_id,
            'authorized_at': time.time()
        })
        
        return {'added': True}
    
    def _remove_authorized_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove authorized user from folder"""
        folder_id = args.get('folder_id')
        user_id = args.get('user_id')
        
        # Remove authorization
        self.system.db.execute("""
            DELETE FROM folder_authorizations 
            WHERE folder_id = ? AND user_id = ?
        """, (folder_id, user_id))
        
        return {'removed': True}
    
    def _get_authorized_users(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get authorized users for folder"""
        folder_id = args.get('folder_id')
        
        users = self.system.db.fetch_all("""
            SELECT u.* FROM users u
            JOIN folder_authorizations fa ON u.user_id = fa.user_id
            WHERE fa.folder_id = ?
        """, (folder_id,))
        
        return {'users': [dict(u) for u in users]}
    
    def _get_user_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current user info"""
        user_id = self._get_current_user_id()
        
        user = self.system.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        
        if user:
            result = dict(user)
            # Convert datetime objects to strings
            for key, value in result.items():
                result[key] = json_serializable(value)
            return result
        return {}
    
    def _initialize_user(self, args: Dict[str, Any]) -> str:
        """Initialize new user"""
        display_name = args.get('display_name', 'User')
        
        # Create user using the system's method
        user = self.system.create_user(display_name)
        
        # Store as current user
        self._set_current_user_id(user['user_id'])
        
        return user['user_id']
    
    def _is_user_initialized(self, args: Dict[str, Any]) -> bool:
        """Check if user is initialized"""
        try:
            user_id = self._get_current_user_id()
            return bool(user_id)
        except:
            return False
    
    # ==================== SYSTEM OPERATIONS ====================
    
    def _check_database_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check database status"""
        try:
            # Test database connection
            self.system.db.fetch_one("SELECT 1")
            
            # Get table counts
            tables = ['users', 'folders', 'files', 'segments', 'shares']
            counts = {}
            
            for table in tables:
                result = self.system.db.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                counts[table] = result['count'] if result else 0
            
            return {
                'connected': True,
                'type': 'sqlite',
                'tables': counts
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def _setup_postgresql(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Setup PostgreSQL (placeholder)"""
        return {
            'status': 'PostgreSQL setup would be performed here',
            'note': 'Currently using SQLite'
        }
    
    def _get_system_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system statistics"""
        stats = self.system.get_metrics()
        
        return {
            'totalFiles': stats.get('total_files', 0),
            'totalSize': stats.get('total_size', 0),
            'totalShares': stats.get('total_shares', 0),
            'activeUploads': stats.get('active_uploads', 0),
            'activeDownloads': stats.get('active_downloads', 0),
            'cpuUsage': stats.get('cpu_usage', 0),
            'memoryUsage': stats.get('memory_usage', 0),
            'diskUsage': stats.get('disk_usage', 0),
            'uploadSpeed': stats.get('upload_speed', 0),
            'downloadSpeed': stats.get('download_speed', 0)
        }
    
    # ==================== FILE OPERATIONS ====================
    
    def _select_files(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select files (returns mock data for GUI)"""
        # This would open a file dialog in Tauri
        # Returning mock data for testing
        return [
            {
                'id': 'file1',
                'name': 'document.pdf',
                'type': 'file',
                'size': 1024000,
                'path': '/home/user/document.pdf',
                'modifiedAt': datetime.now().isoformat()
            }
        ]
    
    def _select_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Select folder (returns mock data for GUI)"""
        # This would open a folder dialog in Tauri
        # Returning mock data for testing
        return {
            'id': 'folder1',
            'name': 'Documents',
            'type': 'folder',
            'path': '/home/user/Documents',
            'modifiedAt': datetime.now().isoformat()
        }
    
    # ==================== HELPER METHODS ====================
    
    def _get_current_user_id(self) -> str:
        """Get current user ID"""
        # In production, this would get from session/config
        # For now, get or create default user
        user = self.system.db.fetch_one(
            "SELECT user_id FROM users LIMIT 1"
        )
        
        if user:
            return user['user_id']
        
        # Create default user
        new_user = self.system.user_manager.create_user('DefaultUser')
        return new_user['user_id']
    
    def _set_current_user_id(self, user_id: str):
        """Set current user ID"""
        # In production, store in session/config
        pass
    
    def _get_folder_id_from_files(self, files: List[str]) -> str:
        """Get folder ID from file paths"""
        if not files:
            raise ValueError("No files provided")
        
        # Get parent folder of first file
        folder_path = str(Path(files[0]).parent)
        folder_id = hashlib.sha256(folder_path.encode()).hexdigest()
        
        return folder_id
    
    def _format_share_for_gui(self, share: Dict[str, Any]) -> Dict[str, Any]:
        """Format share data for GUI"""
        return {
            'id': share.get('share_id', ''),
            'shareId': share.get('share_id', ''),
            'type': share.get('access_level', 'public').lower(),
            'name': share.get('name', 'Shared Folder'),
            'size': share.get('size', 0),
            'fileCount': share.get('file_count', 0),
            'folderCount': share.get('folder_count', 0),
            'createdAt': datetime.fromtimestamp(
                share.get('created_at', time.time())
            ).isoformat(),
            'expiresAt': datetime.fromtimestamp(
                share.get('expires_at', time.time() + 86400 * 30)
            ).isoformat() if share.get('expires_at') else None,
            'accessCount': share.get('access_count', 0),
            'lastAccessed': None
        }