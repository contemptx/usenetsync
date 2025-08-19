#!/usr/bin/env python3
"""
Unified Change Detection Module - Detect file changes
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UnifiedChangeDetection:
    """File change detection"""
    
    def __init__(self, db):
        self.db = db
    
    def detect_changes(self, folder_id: str, current_files: Dict[str, Any]) -> Dict[str, List]:
        """Detect changes in folder"""
        changes = {'added': [], 'modified': [], 'deleted': []}
        
        # Get existing files
        existing = {}
        for file in self.db.fetch_all(
            "SELECT * FROM files WHERE folder_id = ?",
            (folder_id,)
        ):
            existing[file['path']] = file
        
        # Check current files
        for path, file_info in current_files.items():
            if path in existing:
                if file_info['hash'] != existing[path]['hash']:
                    changes['modified'].append(file_info)
            else:
                changes['added'].append(file_info)
        
        # Check deleted
        for path in existing:
            if path not in current_files:
                changes['deleted'].append(existing[path])
        
        return changes