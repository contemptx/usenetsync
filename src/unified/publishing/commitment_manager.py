#!/usr/bin/env python3
"""
Unified Commitment Manager - Manage user commitments for private shares
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedCommitmentManager:
    """Manage user commitments for private shares"""
    
    def __init__(self, db=None, zkp=None):
        self.db = db
        self.zkp = zkp
    
    def add_commitment(self, share_id: str, user_id: str, 
                      commitment_data: Dict) -> bool:
        """Add user commitment for private share"""
        commitment = {
            'share_id': share_id,
            'user_id': user_id,
            'commitment': hashlib.sha256(f"{user_id}{share_id}".encode()).hexdigest(),
            'created_at': datetime.now().isoformat(),
            **commitment_data
        }
        
        if self.db:
            self.db.insert('user_commitments', commitment)
        
        logger.info(f"Added commitment for user {user_id[:8]}... to share {share_id[:8]}...")
        return True
    
    def verify_commitment(self, share_id: str, user_id: str, proof: str) -> bool:
        """Verify user has commitment for share"""
        if self.db:
            commitment = self.db.fetch_one(
                "SELECT * FROM user_commitments WHERE share_id = ? AND user_id = ?",
                (share_id, user_id)
            )
            
            if commitment and self.zkp:
                return self.zkp.verify_proof(proof, commitment['commitment'])
        
        return False
    
    def list_commitments(self, share_id: str) -> List[Dict]:
        """List all commitments for a share"""
        if self.db:
            commitments = self.db.fetch_all(
                "SELECT * FROM user_commitments WHERE share_id = ?",
                (share_id,)
            )
            return [dict(c) for c in commitments]
        return []