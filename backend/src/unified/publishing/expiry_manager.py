#!/usr/bin/env python3
"""
Unified Expiry Manager - Manage share expiry
"""

from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class UnifiedExpiryManager:
    """Manage share expiry and cleanup"""
    
    def __init__(self, db=None):
        self.db = db
    
    def check_expired_shares(self) -> List[str]:
        """Check for expired shares"""
        expired = []
        
        if self.db:
            shares = self.db.fetch_all(
                "SELECT share_id FROM publications WHERE status = 'active' AND expires_at < ?",
                (datetime.now().isoformat(),)
            )
            
            for share in shares:
                expired.append(share['share_id'])
                self.db.update(
                    'publications',
                    {'status': 'expired'},
                    'share_id = ?',
                    (share['share_id'],)
                )
        
        if expired:
            logger.info(f"Found {len(expired)} expired shares")
        
        return expired
    
    def extend_expiry(self, share_id: str, days: int) -> bool:
        """Extend share expiry"""
        if self.db:
            share = self.db.fetch_one(
                "SELECT expires_at FROM publications WHERE share_id = ?",
                (share_id,)
            )
            
            if share:
                current = datetime.fromisoformat(share['expires_at'])
                new_expiry = current + timedelta(days=days)
                
                self.db.update(
                    'publications',
                    {'expires_at': new_expiry.isoformat()},
                    'share_id = ?',
                    (share_id,)
                )
                
                logger.info(f"Extended share {share_id} by {days} days")
                return True
        
        return False