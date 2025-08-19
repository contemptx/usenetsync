#!/usr/bin/env python3
"""
Unified Share Manager - Manage folder shares
Production-ready with complete share lifecycle management
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ShareType(Enum):
    """Share types"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"

class ShareStatus(Enum):
    """Share status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class UnifiedShareManager:
    """
    Unified share manager
    Manages folder shares with full lifecycle support
    """
    
    def __init__(self, db=None, security=None):
        """Initialize share manager"""
        self.db = db
        self.security = security
        self._share_cache = {}
        self._statistics = {
            'shares_created': 0,
            'shares_revoked': 0,
            'shares_accessed': 0,
            'shares_expired': 0
        }
    
    def create_share(self, folder_id: str, owner_id: str,
                    share_type: ShareType = ShareType.PUBLIC,
                    expiry_days: int = 30,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create new share
        
        Args:
            folder_id: Folder to share
            owner_id: Owner creating share
            share_type: Type of share
            expiry_days: Days until expiry
            metadata: Optional metadata
        
        Returns:
            Share information
        """
        # Generate share ID (no Usenet data)
        share_id = str(uuid.uuid4())
        
        # Calculate expiry
        expires_at = datetime.now() + timedelta(days=expiry_days)
        
        # Create share record
        share = {
            'share_id': share_id,
            'folder_id': folder_id,
            'owner_id': owner_id,
            'share_type': share_type.value,
            'status': ShareStatus.ACTIVE.value,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'access_count': 0,
            'last_accessed': None,
            'metadata': metadata or {}
        }
        
        # Generate share key if needed
        if share_type in [ShareType.PRIVATE, ShareType.PROTECTED]:
            share['encryption_key'] = secrets.token_urlsafe(32)
        
        # Store in database
        if self.db:
            self.db.insert('publications', share)
        
        # Cache share
        self._share_cache[share_id] = share
        self._statistics['shares_created'] += 1
        
        logger.info(f"Created {share_type.value} share: {share_id}")
        
        return share
    
    def get_share(self, share_id: str) -> Optional[Dict[str, Any]]:
        """
        Get share information
        
        Args:
            share_id: Share identifier
        
        Returns:
            Share information or None
        """
        # Check cache
        if share_id in self._share_cache:
            return self._share_cache[share_id]
        
        # Load from database
        if self.db:
            share = self.db.fetch_one(
                "SELECT * FROM publications WHERE share_id = ?",
                (share_id,)
            )
            
            if share:
                share = dict(share)
                self._share_cache[share_id] = share
                return share
        
        return None
    
    def update_share(self, share_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update share information
        
        Args:
            share_id: Share identifier
            updates: Updates to apply
        
        Returns:
            True if updated
        """
        share = self.get_share(share_id)
        
        if not share:
            logger.warning(f"Share not found: {share_id}")
            return False
        
        # Apply updates
        for key, value in updates.items():
            if key not in ['share_id', 'folder_id', 'owner_id']:  # Immutable fields
                share[key] = value
        
        share['updated_at'] = datetime.now().isoformat()
        
        # Update database
        if self.db:
            self.db.update(
                'publications',
                share,
                'share_id = ?',
                (share_id,)
            )
        
        # Update cache
        self._share_cache[share_id] = share
        
        logger.info(f"Updated share: {share_id}")
        return True
    
    def revoke_share(self, share_id: str, owner_id: str) -> bool:
        """
        Revoke share
        
        Args:
            share_id: Share to revoke
            owner_id: Owner revoking share
        
        Returns:
            True if revoked
        """
        share = self.get_share(share_id)
        
        if not share:
            return False
        
        # Verify ownership
        if share['owner_id'] != owner_id:
            logger.warning(f"Unauthorized revoke attempt for {share_id}")
            return False
        
        # Update status
        return self.update_share(share_id, {
            'status': ShareStatus.REVOKED.value,
            'revoked_at': datetime.now().isoformat()
        })
    
    def extend_share(self, share_id: str, additional_days: int) -> bool:
        """
        Extend share expiry
        
        Args:
            share_id: Share to extend
            additional_days: Days to add
        
        Returns:
            True if extended
        """
        share = self.get_share(share_id)
        
        if not share or share['status'] != ShareStatus.ACTIVE.value:
            return False
        
        # Calculate new expiry
        current_expiry = datetime.fromisoformat(share['expires_at'])
        new_expiry = current_expiry + timedelta(days=additional_days)
        
        return self.update_share(share_id, {
            'expires_at': new_expiry.isoformat()
        })
    
    def record_access(self, share_id: str, user_id: str) -> bool:
        """
        Record share access
        
        Args:
            share_id: Share being accessed
            user_id: User accessing share
        
        Returns:
            True if recorded
        """
        share = self.get_share(share_id)
        
        if not share:
            return False
        
        # Update access statistics
        updates = {
            'access_count': share.get('access_count', 0) + 1,
            'last_accessed': datetime.now().isoformat(),
            'last_accessed_by': user_id
        }
        
        self._statistics['shares_accessed'] += 1
        
        return self.update_share(share_id, updates)
    
    def list_shares(self, owner_id: Optional[str] = None,
                   folder_id: Optional[str] = None,
                   status: Optional[ShareStatus] = None) -> List[Dict[str, Any]]:
        """
        List shares with filters
        
        Args:
            owner_id: Filter by owner
            folder_id: Filter by folder
            status: Filter by status
        
        Returns:
            List of shares
        """
        if not self.db:
            return list(self._share_cache.values())
        
        # Build query
        query = "SELECT * FROM publications WHERE 1=1"
        params = []
        
        if owner_id:
            query += " AND owner_id = ?"
            params.append(owner_id)
        
        if folder_id:
            query += " AND folder_id = ?"
            params.append(folder_id)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC"
        
        shares = self.db.fetch_all(query, params)
        
        return [dict(share) for share in shares]
    
    def check_expiry(self) -> int:
        """
        Check and update expired shares
        
        Returns:
            Number of expired shares
        """
        expired_count = 0
        current_time = datetime.now()
        
        # Get active shares
        active_shares = self.list_shares(status=ShareStatus.ACTIVE)
        
        for share in active_shares:
            expires_at = datetime.fromisoformat(share['expires_at'])
            
            if current_time > expires_at:
                # Mark as expired
                self.update_share(share['share_id'], {
                    'status': ShareStatus.EXPIRED.value
                })
                expired_count += 1
                self._statistics['shares_expired'] += 1
        
        if expired_count > 0:
            logger.info(f"Expired {expired_count} shares")
        
        return expired_count
    
    def get_share_statistics(self, share_id: str) -> Dict[str, Any]:
        """
        Get share statistics
        
        Args:
            share_id: Share identifier
        
        Returns:
            Share statistics
        """
        share = self.get_share(share_id)
        
        if not share:
            return {}
        
        # Calculate statistics
        created_at = datetime.fromisoformat(share['created_at'])
        expires_at = datetime.fromisoformat(share['expires_at'])
        now = datetime.now()
        
        return {
            'share_id': share_id,
            'share_type': share['share_type'],
            'status': share['status'],
            'access_count': share.get('access_count', 0),
            'days_active': (now - created_at).days,
            'days_remaining': max(0, (expires_at - now).days),
            'created_at': share['created_at'],
            'expires_at': share['expires_at'],
            'last_accessed': share.get('last_accessed')
        }
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global share statistics"""
        if self.db:
            # Get counts by status
            status_counts = {}
            for status in ShareStatus:
                count = self.db.fetch_one(
                    "SELECT COUNT(*) as count FROM publications WHERE status = ?",
                    (status.value,)
                )
                status_counts[status.value] = count['count'] if count else 0
            
            # Get counts by type
            type_counts = {}
            for share_type in ShareType:
                count = self.db.fetch_one(
                    "SELECT COUNT(*) as count FROM publications WHERE share_type = ?",
                    (share_type.value,)
                )
                type_counts[share_type.value] = count['count'] if count else 0
            
            return {
                **self._statistics,
                'by_status': status_counts,
                'by_type': type_counts
            }
        
        return self._statistics.copy()