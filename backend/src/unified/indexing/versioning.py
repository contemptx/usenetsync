#!/usr/bin/env python3
"""
Unified Versioning Module - File version tracking and management
"""

import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UnifiedVersioning:
    """File versioning system"""
    
    def __init__(self, db):
        self.db = db
    
    def create_version(self, file_id: str, file_hash: str, size: int,
                      change_type: str = 'modified') -> int:
        """Create new file version"""
        # Get current version
        current = self.db.fetch_one(
            "SELECT MAX(version) as v FROM files WHERE file_id = ?",
            (file_id,)
        )
        
        new_version = (current['v'] or 0) + 1
        
        # Update file with new version
        self.db.update(
            'files',
            {
                'version': new_version,
                'previous_version': current['v'],
                'hash': file_hash,
                'size': size,
                'change_type': change_type,
                'modified_at': datetime.now().isoformat()
            },
            'file_id = ?',
            (file_id,)
        )
        
        return new_version
    
    def get_version_history(self, file_id: str) -> List[Dict[str, Any]]:
        """Get version history for file"""
        return self.db.fetch_all(
            """
            SELECT version, hash, size, change_type, modified_at
            FROM files
            WHERE file_id = ?
            ORDER BY version DESC
            """,
            (file_id,)
        )