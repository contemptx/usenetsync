#!/usr/bin/env python3
"""
Fix all issues in the complete_tauri_bridge.py
"""

with open('/workspace/src/unified/gui_bridge/complete_tauri_bridge.py', 'r') as f:
    content = f.read()

# Add imports at the top
import_section = '''#!/usr/bin/env python3
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
'''

# Replace the import section
import_end = content.find('logger = logging.getLogger(__name__)')
if import_end > 0:
    content = import_section + '\n' + content[import_end + len('logger = logging.getLogger(__name__)') + 1:]
else:
    content = import_section + '\n' + content[content.find('class CompleteTauriBridge'):]

# Fix the _get_user_info method to handle datetime
old_get_user_info = '''    def _get_user_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current user info"""
        user_id = self._get_current_user_id()
        
        user = self.system.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        
        if user:
            return dict(user)
        return {}'''

new_get_user_info = '''    def _get_user_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
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
        return {}'''

content = content.replace(old_get_user_info, new_get_user_info)

# Fix _initialize_user to use the system's create_user method
old_initialize = '''    def _initialize_user(self, args: Dict[str, Any]) -> str:
        """Initialize new user"""
        display_name = args.get('display_name', 'User')
        
        # Create user
        user = self.system.user_manager.create_user(display_name)
        
        # Store as current user
        self._set_current_user_id(user['user_id'])
        
        return user['user_id']'''

new_initialize = '''    def _initialize_user(self, args: Dict[str, Any]) -> str:
        """Initialize new user"""
        display_name = args.get('display_name', 'User')
        
        # Create user using the system's method
        user = self.system.create_user(display_name)
        
        # Store as current user
        self._set_current_user_id(user['user_id'])
        
        return user['user_id']'''

content = content.replace(old_initialize, new_initialize)

# Fix _create_share to use the system's security methods properly
old_create_share = '''        if share_type == 'public':
            share = self.system.security.access_control.create_public_share(
                folder_id, owner_id, expiry_days=30
            )
        elif share_type == 'private':
            share = self.system.security.access_control.create_private_share(
                folder_id, owner_id, allowed_users=[], expiry_days=30
            )
        elif share_type == 'protected':
            share = self.system.security.access_control.create_protected_share(
                folder_id, owner_id, password, expiry_days=30
            )'''

new_create_share = '''        if share_type == 'public':
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
            )'''

content = content.replace(old_create_share, new_create_share)

# Fix _get_system_stats to use the correct method
old_stats = '''    def _get_system_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system statistics"""
        stats = self.system.monitoring.metrics_collector.get_metrics()'''

new_stats = '''    def _get_system_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system statistics"""
        stats = self.system.get_metrics()'''

content = content.replace(old_stats, new_stats)

# Write back
with open('/workspace/src/unified/gui_bridge/complete_tauri_bridge.py', 'w') as f:
    f.write(content)

print("✅ Fixed JSON serialization for datetime objects")
print("✅ Fixed _initialize_user to use system.create_user")
print("✅ Fixed _create_share to use system methods")
print("✅ Fixed _get_system_stats to use system.get_metrics")
print("✅ All bridge methods now use correct system attributes")