#!/usr/bin/env python3
"""
Unified Batch Module - Batch uploads by newsgroup
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class UnifiedBatch:
    """Batch uploads for efficiency"""
    
    def __init__(self, max_batch_size: int = 50):
        self.max_batch_size = max_batch_size
        self.batches = {}  # newsgroup -> list of items
    
    def add_to_batch(self, newsgroup: str, item: Any):
        """Add item to batch"""
        if newsgroup not in self.batches:
            self.batches[newsgroup] = []
        self.batches[newsgroup].append(item)
    
    def get_ready_batches(self) -> List[Tuple[str, List[Any]]]:
        """Get batches ready for upload"""
        ready = []
        for newsgroup, items in self.batches.items():
            if len(items) >= self.max_batch_size:
                ready.append((newsgroup, items[:self.max_batch_size]))
                self.batches[newsgroup] = items[self.max_batch_size:]
        return ready