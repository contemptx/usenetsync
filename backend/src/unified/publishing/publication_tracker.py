#!/usr/bin/env python3
"""
Unified Publication Tracker - Track published segments
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedPublicationTracker:
    """Track published segments and their status"""
    
    def __init__(self, db=None):
        self.db = db
        self._publications = {}
    
    def track_publication(self, segment_id: str, message_id: str,
                         newsgroups: List[str], server: str) -> bool:
        """Track segment publication"""
        publication = {
            'segment_id': segment_id,
            'message_id': message_id,
            'newsgroups': ','.join(newsgroups),
            'server': server,
            'published_at': datetime.now().isoformat(),
            'verified': False
        }
        
        if self.db:
            self.db.insert('messages', publication)
        
        self._publications[segment_id] = publication
        logger.info(f"Tracked publication: {segment_id}")
        return True
    
    def verify_publication(self, segment_id: str) -> bool:
        """Verify segment was successfully published"""
        if segment_id in self._publications:
            self._publications[segment_id]['verified'] = True
            
            if self.db:
                self.db.update(
                    'messages',
                    {'verified': True, 'verified_at': datetime.now().isoformat()},
                    'segment_id = ?',
                    (segment_id,)
                )
            
            return True
        return False
    
    def get_publication_status(self, folder_id: str) -> Dict:
        """Get publication status for folder"""
        if self.db:
            total = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM segments WHERE file_id IN (SELECT file_id FROM files WHERE folder_id = ?)",
                (folder_id,)
            )
            
            published = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM messages WHERE segment_id IN (SELECT segment_id FROM segments WHERE file_id IN (SELECT file_id FROM files WHERE folder_id = ?))",
                (folder_id,)
            )
            
            return {
                'total_segments': total['count'] if total else 0,
                'published_segments': published['count'] if published else 0,
                'progress': (published['count'] / total['count'] * 100) if total and total['count'] > 0 else 0
            }
        
        return {'total_segments': 0, 'published_segments': 0, 'progress': 0}