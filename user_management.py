#!/usr/bin/env python3
"""
User Management for UsenetSync
Simplified single-user profile system
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class UserManager:
    """
    Manages the single user profile for UsenetSync
    """
    
    def __init__(self, db_manager, security_system):
        self.db = db_manager
        self.security = security_system
        self._config = None
        self._preferences = None
        self._load_user()
        
    def _load_user(self):
        """Load user configuration from database"""
        self._config = self.db.get_user_config()
        if self._config:
            self._preferences = self._config.get('preferences', {})
            
    def is_initialized(self) -> bool:
        """Check if user is initialized"""
        return self._config is not None
        
    def initialize(self, display_name: Optional[str] = None) -> str:
        """Initialize user for first time"""
        if self.is_initialized():
            logger.warning("User already initialized")
            return self._config['user_id']
            
        # Initialize through security system
        user_id = self.security.initialize_user(display_name)
        
        # Set default preferences
        default_prefs = self._get_default_preferences()
        self.db.update_user_preferences(default_prefs)
        
        # Reload
        self._load_user()
        
        logger.info(f"User initialized with ID: {user_id[:16]}...")
        return user_id
        
    def get_user_id(self) -> Optional[str]:
        """Get user ID"""
        return self._config['user_id'] if self._config else None
        
    def get_display_name(self) -> str:
        """Get display name"""
        if self._config:
            return self._config.get('display_name', 'User')
        return 'User'
        
    def set_display_name(self, name: str):
        """Update display name"""
        if not self._config:
            raise RuntimeError("User not initialized")
            
        # Update in database
        with self.db.pool.get_connection() as conn:
            conn.execute("""
                UPDATE user_config SET display_name = ? WHERE id = 1
            """, (name,))
            conn.commit()
            
        self._config['display_name'] = name
        logger.info(f"Updated display name to: {name}")
        
    def get_preference(self, key: str, default=None):
        """Get user preference"""
        return self._preferences.get(key, default)
        
    def set_preference(self, key: str, value):
        """Set user preference"""
        if not self._config:
            raise RuntimeError("User not initialized")
            
        self._preferences[key] = value
        self.db.update_user_preferences(self._preferences)
        logger.debug(f"Updated preference: {key} = {value}")
        
    def get_all_preferences(self) -> Dict:
        """Get all preferences"""
        return self._preferences.copy()
        
    def update_preferences(self, preferences: Dict):
        """Update multiple preferences"""
        if not self._config:
            raise RuntimeError("User not initialized")
            
        self._preferences.update(preferences)
        self.db.update_user_preferences(self._preferences)
        logger.info(f"Updated {len(preferences)} preferences")
        
    def get_download_path(self) -> str:
        """Get download path"""
        if self._config and self._config.get('download_path'):
            return self._config['download_path']
        return self.get_preference('download_path', './downloads')
        
    def set_download_path(self, path: str):
        """Set download path"""
        # Validate path
        path = os.path.abspath(path)
        os.makedirs(path, exist_ok=True)
        
        # Update in database
        with self.db.pool.get_connection() as conn:
            conn.execute("""
                UPDATE user_config SET download_path = ? WHERE id = 1
            """, (path,))
            conn.commit()
            
        if self._config:
            self._config['download_path'] = path
            
        logger.info(f"Set download path to: {path}")
        
    def get_temp_path(self) -> str:
        """Get temporary files path"""
        if self._config and self._config.get('temp_path'):
            return self._config['temp_path']
        return self.get_preference('temp_path', './temp')
        
    def set_temp_path(self, path: str):
        """Set temporary files path"""
        # Validate path
        path = os.path.abspath(path)
        os.makedirs(path, exist_ok=True)
        
        # Update in database
        with self.db.pool.get_connection() as conn:
            conn.execute("""
                UPDATE user_config SET temp_path = ? WHERE id = 1
            """, (path,))
            conn.commit()
            
        if self._config:
            self._config['temp_path'] = path
            
        logger.info(f"Set temp path to: {path}")
        
    def update_last_active(self):
        """Update last active timestamp"""
        with self.db.pool.get_connection() as conn:
            conn.execute("""
                UPDATE user_config SET last_active = CURRENT_TIMESTAMP WHERE id = 1
            """)
            conn.commit()
            
    def get_statistics(self) -> Dict:
        """Get user statistics"""
        stats = {
            'user_id': self.get_user_id(),
            'display_name': self.get_display_name(),
            'created_at': self._config.get('created_at') if self._config else None,
            'last_active': self._config.get('last_active') if self._config else None
        }
        
        # Add folder statistics
        with self.db.pool.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as folder_count,
                    SUM(total_files) as total_files,
                    SUM(total_size) as total_size
                FROM folders WHERE state = 'active'
            """)
            folder_stats = cursor.fetchone()
            
            stats.update({
                'folders': folder_stats['folder_count'] or 0,
                'files': folder_stats['total_files'] or 0,
                'total_size': folder_stats['total_size'] or 0
            })
            
        return stats
        
    def export_config(self) -> Dict:
        """Export user configuration for backup"""
        if not self._config:
            raise RuntimeError("User not initialized")
            
        return {
            'user_id': self._config['user_id'],
            'display_name': self._config.get('display_name'),
            'preferences': self._preferences,
            'download_path': self.get_download_path(),
            'temp_path': self.get_temp_path(),
            'exported_at': datetime.now().isoformat()
        }
        
    def import_config(self, config_data: Dict, preserve_user_id: bool = True):
        """Import user configuration from backup"""
        if preserve_user_id and self._config:
            # Keep existing user ID
            config_data['user_id'] = self._config['user_id']
            
        # Validate user ID
        if 'user_id' not in config_data or len(config_data['user_id']) != 64:
            raise ValueError("Invalid user ID in config")
            
        # Initialize or update
        if not self._config:
            self.db.initialize_user(
                config_data['user_id'],
                config_data.get('display_name')
            )
        else:
            self.set_display_name(config_data.get('display_name', 'User'))
            
        # Update preferences
        if 'preferences' in config_data:
            self.update_preferences(config_data['preferences'])
            
        # Update paths
        if 'download_path' in config_data:
            self.set_download_path(config_data['download_path'])
        if 'temp_path' in config_data:
            self.set_temp_path(config_data['temp_path'])
            
        # Reload
        self._load_user()
        
        logger.info("User configuration imported successfully")
        
    def reset_preferences(self):
        """Reset preferences to defaults"""
        if not self._config:
            raise RuntimeError("User not initialized")
            
        default_prefs = self._get_default_preferences()
        self.update_preferences(default_prefs)
        logger.info("Preferences reset to defaults")
        
    def _get_default_preferences(self) -> Dict:
        """Get default preferences"""
        return {
            # Performance
            'parallel_uploads': 3,
            'parallel_downloads': 3,
            'worker_threads': 8,
            'segment_size': 768000,  # 750KB
            
            # Behavior
            'auto_resume': True,
            'verify_downloads': True,
            'delete_after_upload': False,
            'preserve_timestamps': True,
            
            # UI
            'theme': 'system',
            'show_hidden_files': False,
            'confirm_deletions': True,
            'minimize_to_tray': True,
            
            # Advanced
            'enable_redundancy': True,
            'redundancy_level': 2,
            'enable_subject_fallback': False,
            'max_retries': 3,
            'retry_delay': 5,
            
            # Paths
            'download_path': './downloads',
            'temp_path': './temp',
            'log_path': './logs'
        }