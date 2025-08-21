#!/usr/bin/env python3
"""
Unified Permission Manager - Manage share permissions
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedPermissionManager:
    """Manage share permissions and access control"""
    
    def __init__(self, db=None):
        self.db = db
        self._permissions_cache = {}
    
    def grant_permission(self, share_id: str, user_id: str, 
                        permission: str = 'read') -> bool:
        """Grant permission to user"""
        key = f"{share_id}:{user_id}"
        self._permissions_cache[key] = permission
        
        if self.db:
            self.db.insert('user_commitments', {
                'share_id': share_id,
                'user_id': user_id,
                'permission': permission
            })
        
        logger.info(f"Granted {permission} to {user_id[:8]}... for {share_id[:8]}...")
        return True
    
    def revoke_permission(self, share_id: str, user_id: str) -> bool:
        """Revoke user permission"""
        key = f"{share_id}:{user_id}"
        
        if key in self._permissions_cache:
            del self._permissions_cache[key]
        
        if self.db:
            self.db.execute(
                "DELETE FROM user_commitments WHERE share_id = ? AND user_id = ?",
                (share_id, user_id)
            )
        
        logger.info(f"Revoked permission for {user_id[:8]}... from {share_id[:8]}...")
        return True
    
    def check_permission(self, share_id: str, user_id: str) -> Optional[str]:
        """Check user permission"""
        key = f"{share_id}:{user_id}"
        
        if key in self._permissions_cache:
            return self._permissions_cache[key]
        
        if self.db:
            result = self.db.fetch_one(
                "SELECT permission FROM user_commitments WHERE share_id = ? AND user_id = ?",
                (share_id, user_id)
            )
            
            if result:
                permission = result['permission']
                self._permissions_cache[key] = permission
                return permission
        
        return None