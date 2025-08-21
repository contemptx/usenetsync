#!/usr/bin/env python3
"""
Unified Streaming Module - Memory-efficient streaming for large datasets
"""

from typing import Generator, Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class UnifiedStreaming:
    """Streaming support for large datasets"""
    
    def __init__(self, db, chunk_size: int = 10000):
        self.db = db
        self.chunk_size = chunk_size
    
    def stream_files(self, folder_id: str) -> Generator[Dict[str, Any], None, None]:
        """Stream files for folder"""
        offset = 0
        
        while True:
            files = self.db.fetch_all(
                f"""
                SELECT * FROM files 
                WHERE folder_id = ?
                LIMIT {self.chunk_size} OFFSET {offset}
                """,
                (folder_id,)
            )
            
            if not files:
                break
            
            for file in files:
                yield file
            
            offset += self.chunk_size