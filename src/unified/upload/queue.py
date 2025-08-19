#!/usr/bin/env python3
"""
Unified Upload Queue - Priority-based upload queue management
Production-ready with persistence and state management
"""

import uuid
import heapq
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class UploadPriority(Enum):
    """Upload priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 5
    LOW = 8
    BACKGROUND = 10

class UploadState(Enum):
    """Upload states"""
    QUEUED = "queued"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

class UploadItem:
    """Upload queue item"""
    
    def __init__(self, entity_id: str, entity_type: str,
                 priority: UploadPriority = UploadPriority.NORMAL,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize upload item"""
        self.queue_id = str(uuid.uuid4())
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.priority = priority
        self.state = UploadState.QUEUED
        self.progress = 0.0
        self.retry_count = 0
        self.max_retries = 3
        self.metadata = metadata or {}
        self.queued_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.session_id = None
        self.worker_id = None
    
    def __lt__(self, other):
        """Compare by priority for heap queue"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'queue_id': self.queue_id,
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'priority': self.priority.value,
            'state': self.state.value,
            'progress': self.progress,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'metadata': self.metadata,
            'queued_at': self.queued_at.isoformat() if self.queued_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'session_id': self.session_id,
            'worker_id': self.worker_id
        }

class UnifiedUploadQueue:
    """
    Unified upload queue with priority management
    Handles queuing, dequeuing, and state management
    """
    
    def __init__(self, db=None):
        """Initialize upload queue"""
        self.db = db
        self._queue = []  # Heap queue
        self._items = {}  # queue_id -> UploadItem
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._paused = False
        
        # Load persisted queue from database
        if self.db:
            self._load_queue()
    
    def add(self, entity_id: str, entity_type: str,
           priority: UploadPriority = UploadPriority.NORMAL,
           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add item to upload queue
        
        Args:
            entity_id: Entity to upload
            entity_type: Type of entity
            priority: Upload priority
            metadata: Optional metadata
        
        Returns:
            Queue ID
        """
        item = UploadItem(entity_id, entity_type, priority, metadata)
        
        with self._lock:
            # Add to heap queue
            heapq.heappush(self._queue, item)
            self._items[item.queue_id] = item
            
            # Persist to database
            if self.db:
                self._persist_item(item)
            
            # Notify waiting workers
            self._condition.notify()
        
        logger.info(f"Added {entity_type} {entity_id} to queue with priority {priority.name}")
        
        return item.queue_id
    
    def get_next(self, worker_id: str, timeout: Optional[float] = None) -> Optional[UploadItem]:
        """
        Get next item from queue
        
        Args:
            worker_id: Worker requesting item
            timeout: Optional timeout in seconds
        
        Returns:
            Upload item or None
        """
        with self._condition:
            # Wait for item if queue is empty
            if not self._queue and timeout:
                self._condition.wait(timeout)
            
            if self._queue and not self._paused:
                item = heapq.heappop(self._queue)
                
                # Update state
                item.state = UploadState.UPLOADING
                item.started_at = datetime.now()
                item.worker_id = worker_id
                
                # Update database
                if self.db:
                    self._update_item(item)
                
                return item
        
        return None
    
    def complete(self, queue_id: str):
        """Mark item as completed"""
        with self._lock:
            if queue_id in self._items:
                item = self._items[queue_id]
                item.state = UploadState.COMPLETED
                item.completed_at = datetime.now()
                item.progress = 1.0
                
                if self.db:
                    self._update_item(item)
                
                logger.info(f"Upload completed: {item.entity_id}")
    
    def fail(self, queue_id: str, error: str):
        """Mark item as failed"""
        with self._lock:
            if queue_id in self._items:
                item = self._items[queue_id]
                item.state = UploadState.FAILED
                item.error_message = error
                item.retry_count += 1
                
                # Check if should retry
                if item.retry_count < item.max_retries:
                    item.state = UploadState.RETRYING
                    item.priority = UploadPriority(min(item.priority.value + 1, 10))
                    heapq.heappush(self._queue, item)
                    logger.warning(f"Upload failed, retrying: {item.entity_id}")
                else:
                    item.completed_at = datetime.now()
                    logger.error(f"Upload failed permanently: {item.entity_id}")
                
                if self.db:
                    self._update_item(item)
    
    def update_progress(self, queue_id: str, progress: float):
        """Update item progress"""
        with self._lock:
            if queue_id in self._items:
                item = self._items[queue_id]
                item.progress = progress
                
                if self.db:
                    self._update_item(item)
    
    def cancel(self, queue_id: str):
        """Cancel upload item"""
        with self._lock:
            if queue_id in self._items:
                item = self._items[queue_id]
                item.state = UploadState.CANCELLED
                item.completed_at = datetime.now()
                
                # Remove from queue if still queued
                if item in self._queue:
                    self._queue.remove(item)
                    heapq.heapify(self._queue)
                
                if self.db:
                    self._update_item(item)
                
                logger.info(f"Upload cancelled: {item.entity_id}")
    
    def pause(self):
        """Pause queue processing"""
        with self._lock:
            self._paused = True
            logger.info("Upload queue paused")
    
    def resume(self):
        """Resume queue processing"""
        with self._lock:
            self._paused = False
            self._condition.notify_all()
            logger.info("Upload queue resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        with self._lock:
            states = {}
            for item in self._items.values():
                state = item.state.value
                states[state] = states.get(state, 0) + 1
            
            return {
                'total': len(self._items),
                'queued': len(self._queue),
                'paused': self._paused,
                'states': states
            }
    
    def get_items(self, state: Optional[UploadState] = None) -> List[Dict[str, Any]]:
        """Get items in queue"""
        with self._lock:
            items = []
            for item in self._items.values():
                if state is None or item.state == state:
                    items.append(item.to_dict())
            return items
    
    def _persist_item(self, item: UploadItem):
        """Persist item to database"""
        try:
            self.db.upsert(
                'upload_queue',
                item.to_dict(),
                ['queue_id']
            )
        except Exception as e:
            logger.error(f"Failed to persist queue item: {e}")
    
    def _update_item(self, item: UploadItem):
        """Update item in database"""
        try:
            self.db.update(
                'upload_queue',
                item.to_dict(),
                'queue_id = ?',
                (item.queue_id,)
            )
        except Exception as e:
            logger.error(f"Failed to update queue item: {e}")
    
    def _load_queue(self):
        """Load queue from database"""
        try:
            items = self.db.fetch_all(
                """
                SELECT * FROM upload_queue 
                WHERE state IN ('queued', 'retrying')
                ORDER BY priority, queued_at
                """
            )
            
            for item_data in items:
                item = UploadItem(
                    item_data['entity_id'],
                    item_data['entity_type'],
                    UploadPriority(item_data['priority'])
                )
                
                # Restore state
                item.queue_id = item_data['queue_id']
                item.state = UploadState(item_data['state'])
                item.retry_count = item_data.get('retry_count', 0)
                
                # Add to queue
                heapq.heappush(self._queue, item)
                self._items[item.queue_id] = item
            
            logger.info(f"Loaded {len(items)} items from database")
            
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")