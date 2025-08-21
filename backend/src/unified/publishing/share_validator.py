#!/usr/bin/env python3
"""
Unified Share Validator - Validate share access
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedShareValidator:
    """Validate share access and integrity"""
    
    def __init__(self, share_manager=None, permission_manager=None):
        self.share_manager = share_manager
        self.permission_manager = permission_manager
    
    def validate_access(self, share_id: str, user_id: str,
                       password: Optional[str] = None) -> Dict:
        """Validate user access to share"""
        result = {
            'valid': False,
            'reason': None,
            'share_type': None
        }
        
        if not self.share_manager:
            result['reason'] = 'No share manager'
            return result
        
        # Get share
        share = self.share_manager.get_share(share_id)
        
        if not share:
            result['reason'] = 'Share not found'
            return result
        
        # Check expiry
        if share['status'] == 'expired':
            result['reason'] = 'Share expired'
            return result
        
        if share['status'] == 'revoked':
            result['reason'] = 'Share revoked'
            return result
        
        expires_at = datetime.fromisoformat(share['expires_at'])
        if datetime.now() > expires_at:
            result['reason'] = 'Share expired'
            return result
        
        result['share_type'] = share['share_type']
        
        # Check access based on type
        if share['share_type'] == 'public':
            result['valid'] = True
            
        elif share['share_type'] == 'private':
            # Check permissions
            if self.permission_manager:
                permission = self.permission_manager.check_permission(share_id, user_id)
                result['valid'] = permission is not None
                if not result['valid']:
                    result['reason'] = 'No permission'
            
        elif share['share_type'] == 'protected':
            # Validate password
            if password:
                # In production, compare hashed passwords
                result['valid'] = True
            else:
                result['reason'] = 'Password required'
        
        # Record access if valid
        if result['valid']:
            self.share_manager.record_access(share_id, user_id)
        
        return result