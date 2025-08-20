#!/usr/bin/env python3
"""
Unified Progress Module - Upload progress tracking
"""

import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class UnifiedProgress:
    """Track upload progress"""
    
    def __init__(self):
        self.progress = {}  # entity_id -> progress info
    
    def start(self, entity_id: str, total_size: int):
        """Start tracking progress"""
        self.progress[entity_id] = {
            'total_size': total_size,
            'uploaded_size': 0,
            'start_time': time.time(),
            'progress': 0.0
        }
    
    def update(self, entity_id: str, bytes_uploaded: int):
        """Update progress"""
        if entity_id in self.progress:
            info = self.progress[entity_id]
            info['uploaded_size'] += bytes_uploaded
            info['progress'] = info['uploaded_size'] / info['total_size']
    
    def get_progress(self, entity_id: str) -> Dict[str, Any]:
        """Get progress info"""
        return self.progress.get(entity_id, {})