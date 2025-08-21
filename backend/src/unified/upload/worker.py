#!/usr/bin/env python3
"""
Unified Worker Module - Upload worker threads
"""

import threading
import logging

logger = logging.getLogger(__name__)

class UnifiedWorker:
    """Upload worker thread"""
    
    def __init__(self, worker_id: str, queue, connection_pool):
        self.worker_id = worker_id
        self.queue = queue
        self.connection_pool = connection_pool
        self.running = False
        self.thread = None
    
    def start(self):
        """Start worker"""
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
    
    def stop(self):
        """Stop worker"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run(self):
        """Worker loop"""
        while self.running:
            item = self.queue.get_next(self.worker_id, timeout=1.0)
            if item:
                self._process_item(item)
    
    def _process_item(self, item):
        """Process upload item"""
        logger.info(f"Worker {self.worker_id} processing {item.entity_id}")