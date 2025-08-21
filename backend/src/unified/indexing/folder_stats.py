#!/usr/bin/env python3
"""
Unified Folder Stats Module - Folder statistics tracking
"""

from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UnifiedFolderStats:
    """Folder statistics management"""
    
    def __init__(self, db):
        self.db = db
    
    def update_stats(self, folder_id: str) -> Dict[str, Any]:
        """Update folder statistics"""
        stats = self.db.fetch_one(
            """
            SELECT 
                COUNT(*) as file_count,
                SUM(size) as total_size,
                COUNT(DISTINCT hash) as unique_files
            FROM files
            WHERE folder_id = ?
            """,
            (folder_id,)
        )
        
        # Update folder record
        self.db.update(
            'folders',
            {
                'file_count': stats['file_count'],
                'total_size': stats['total_size'] or 0,
                'updated_at': datetime.now().isoformat()
            },
            'folder_id = ?',
            (folder_id,)
        )
        
        return stats