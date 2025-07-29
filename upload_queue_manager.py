#!/usr/bin/env python3
"""
Upload Queue Manager for UsenetSync
Handles priority queuing and batch processing
"""

import os
import time
import heapq
import threading
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass(order=True)
class QueuedUpload:
    """Queued upload with priority ordering"""
    priority: float = field(compare=True)
    task: Any = field(compare=False)
    added_time: float = field(default_factory=time.time, compare=False)
    
class BatchProcessor:
    """Process uploads in optimal batches"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_batches: Dict[str, List[Any]] = defaultdict(list)
        self._lock = threading.Lock()
        
    def add_to_batch(self, newsgroup: str, task: Any) -> Optional[List[Any]]:
        """
        Add task to batch, returns full batch if ready
        """
        with self._lock:
            batch = self.pending_batches[newsgroup]
            batch.append(task)
            
            if len(batch) >= self.batch_size:
                # Return full batch
                full_batch = batch.copy()
                self.pending_batches[newsgroup] = []
                return full_batch
                
        return None
        
    def get_partial_batch(self, newsgroup: str) -> List[Any]:
        """Get partial batch for newsgroup"""
        with self._lock:
            batch = self.pending_batches[newsgroup]
            self.pending_batches[newsgroup] = []
            return batch
            
    def get_all_pending(self) -> Dict[str, List[Any]]:
        """Get all pending batches"""
        with self._lock:
            all_pending = dict(self.pending_batches)
            self.pending_batches.clear()
            return all_pending

class SmartQueueManager:
    """
    Smart queue manager with advanced features:
    - Priority-based scheduling
    - Newsgroup batching
    - Rate limiting
    - Queue persistence
    """
    
    def __init__(self, db_manager, config: Dict[str, Any]):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SmartQueue")
        
        # Configuration
        self.max_queue_size = config.get('max_queue_size', 10000)
        self.batch_size = config.get('batch_size', 100)
        self.rate_limit = config.get('rate_limit_mbps', 0)  # 0 = unlimited
        
        # Priority queue
        self.queue: List[QueuedUpload] = []
        self._lock = threading.Lock()
        
        # Batch processor
        self.batch_processor = BatchProcessor(self.batch_size)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(self.rate_limit) if self.rate_limit > 0 else None
        
        # Statistics
        self.stats = {
            'total_queued': 0,
            'total_processed': 0,
            'bytes_queued': 0,
            'bytes_processed': 0,
            'by_newsgroup': defaultdict(int),
            'by_priority': defaultdict(int)
        }
        
        # Load pending from database
        self._load_pending_tasks()
        
    def add_task(self, task: Any, priority: float) -> bool:
        """Add task to queue with priority"""
        with self._lock:
            if len(self.queue) >= self.max_queue_size:
                self.logger.error("Queue is full")
                return False
                
            # Create queued upload
            queued = QueuedUpload(priority=priority, task=task)
            
            # Add to heap
            heapq.heappush(self.queue, queued)
            
            # Update stats
            self.stats['total_queued'] += 1
            self.stats['bytes_queued'] += task.size
            self.stats['by_newsgroup'][task.newsgroup] += 1
            self.stats['by_priority'][int(priority)] += 1
            
            # Persist to database
            self._persist_task(task, priority)
            
            return True
            
    def get_next_batch(self) -> Optional[Tuple[str, List[Any]]]:
        """Get next batch of tasks for processing"""
        tasks_by_newsgroup = defaultdict(list)
        
        with self._lock:
            # Get tasks up to batch size
            while self.queue and len(tasks_by_newsgroup) < self.batch_size:
                queued = heapq.heappop(self.queue)
                task = queued.task
                
                # Check rate limit
                if self.rate_limiter and not self.rate_limiter.can_send(task.size):
                    # Put back in queue
                    heapq.heappush(self.queue, queued)
                    break
                    
                tasks_by_newsgroup[task.newsgroup].append(task)
                
                # Update stats
                self.stats['total_processed'] += 1
                self.stats['bytes_processed'] += task.size
                
        # Return batch for newsgroup with most tasks
        if tasks_by_newsgroup:
            newsgroup = max(tasks_by_newsgroup, key=lambda k: len(tasks_by_newsgroup[k]))
            return newsgroup, tasks_by_newsgroup[newsgroup]
            
        return None
        
    def get_priority_distribution(self) -> Dict[int, int]:
        """Get current priority distribution"""
        distribution = defaultdict(int)
        
        with self._lock:
            for queued in self.queue:
                priority_level = int(queued.priority)
                distribution[priority_level] += 1
                
        return dict(distribution)
        
    def reprioritize_folder(self, folder_id: str, new_priority: float):
        """Change priority for all tasks from a folder"""
        with self._lock:
            # Rebuild heap with new priorities
            new_queue = []
            
            for queued in self.queue:
                if queued.task.folder_id == folder_id:
                    queued.priority = new_priority
                heapq.heappush(new_queue, queued)
                
            self.queue = new_queue
            
        self.logger.info(f"Reprioritized folder {folder_id} to {new_priority}")
        
    def cancel_folder_uploads(self, folder_id: str) -> int:
        """Cancel all uploads for a folder"""
        cancelled = 0
        
        with self._lock:
            new_queue = []
            
            for queued in self.queue:
                if queued.task.folder_id != folder_id:
                    heapq.heappush(new_queue, queued)
                else:
                    cancelled += 1
                    
            self.queue = new_queue
            
        if cancelled > 0:
            # Update database
            self._cancel_folder_tasks(folder_id)
            
        self.logger.info(f"Cancelled {cancelled} uploads for folder {folder_id}")
        return cancelled
        
    def _persist_task(self, task: Any, priority: float):
        """Save task to database"""
        try:
            with self.db.pool.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO upload_queue 
                    (segment_id, priority, queued_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (task.segment_id, priority))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to persist task: {e}")
            
    def _load_pending_tasks(self):
        """Load pending tasks from database"""
        try:
            pending = self.db.get_pending_uploads()
            
            for task_data in pending:
                # Reconstruct task and add to queue
                # This would need actual task reconstruction logic
                pass
                
            self.logger.info(f"Loaded {len(pending)} pending tasks")
            
        except Exception as e:
            self.logger.error(f"Failed to load pending tasks: {e}")
            
    def _cancel_folder_tasks(self, folder_id: str):
        """Cancel folder tasks in database"""
        try:
            with self.db.pool.get_connection() as conn:
                conn.execute("""
                    DELETE FROM upload_queue 
                    WHERE segment_id IN (
                        SELECT s.id FROM segments s
                        JOIN files f ON s.file_id = f.id
                        JOIN folders fo ON f.folder_id = fo.id
                        WHERE fo.folder_unique_id = ?
                    )
                """, (folder_id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to cancel folder tasks: {e}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self._lock:
            queue_size = len(self.queue)
            
        return {
            'queue_size': queue_size,
            'max_size': self.max_queue_size,
            'utilization': (queue_size / self.max_queue_size) * 100,
            'total_queued': self.stats['total_queued'],
            'total_processed': self.stats['total_processed'],
            'bytes_queued': self.stats['bytes_queued'],
            'bytes_processed': self.stats['bytes_processed'],
            'mb_queued': self.stats['bytes_queued'] / 1024 / 1024,
            'mb_processed': self.stats['bytes_processed'] / 1024 / 1024,
            'by_newsgroup': dict(self.stats['by_newsgroup']),
            'by_priority': dict(self.stats['by_priority']),
            'priority_distribution': self.get_priority_distribution()
        }

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_mbps: float):
        self.rate_bytes_per_sec = rate_mbps * 1024 * 1024
        self.bucket_size = self.rate_bytes_per_sec * 2  # 2 second burst
        self.tokens = self.bucket_size
        self.last_update = time.time()
        self._lock = threading.Lock()
        
    def can_send(self, bytes_to_send: int) -> bool:
        """Check if can send bytes within rate limit"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.bucket_size,
                self.tokens + (elapsed * self.rate_bytes_per_sec)
            )
            self.last_update = now
            
            # Check if enough tokens
            if self.tokens >= bytes_to_send:
                self.tokens -= bytes_to_send
                return True
                
            return False
            
    def get_wait_time(self, bytes_to_send: int) -> float:
        """Get time to wait before can send"""
        with self._lock:
            if self.tokens >= bytes_to_send:
                return 0.0
                
            tokens_needed = bytes_to_send - self.tokens
            return tokens_needed / self.rate_bytes_per_sec

class AdaptiveScheduler:
    """
    Adaptive upload scheduler that adjusts based on:
    - Server response times
    - Error rates
    - Time of day
    - Network conditions
    """
    
    def __init__(self):
        self.server_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'response_times': [],
            'error_count': 0,
            'success_count': 0,
            'last_error': None
        })
        self._lock = threading.Lock()
        
    def record_upload_result(self, server: str, success: bool, response_time: float):
        """Record upload result for adaptive scheduling"""
        with self._lock:
            stats = self.server_stats[server]
            
            if success:
                stats['success_count'] += 1
                stats['response_times'].append(response_time)
                # Keep last 100 response times
                if len(stats['response_times']) > 100:
                    stats['response_times'].pop(0)
            else:
                stats['error_count'] += 1
                stats['last_error'] = datetime.now()
                
    def get_server_score(self, server: str) -> float:
        """
        Get server score for scheduling (higher is better)
        """
        with self._lock:
            stats = self.server_stats[server]
            
            # Calculate success rate
            total = stats['success_count'] + stats['error_count']
            if total == 0:
                return 1.0  # Neutral score for new servers
                
            success_rate = stats['success_count'] / total
            
            # Calculate average response time
            if stats['response_times']:
                avg_response = sum(stats['response_times']) / len(stats['response_times'])
                # Normalize to 0-1 (assuming 1 second is good, 10 seconds is bad)
                response_score = max(0, 1 - (avg_response - 1) / 9)
            else:
                response_score = 0.5
                
            # Penalize recent errors
            if stats['last_error']:
                time_since_error = (datetime.now() - stats['last_error']).total_seconds()
                if time_since_error < 300:  # Within 5 minutes
                    error_penalty = 0.5
                else:
                    error_penalty = 1.0
            else:
                error_penalty = 1.0
                
            # Combined score
            return success_rate * response_score * error_penalty
            
    def get_optimal_worker_count(self) -> int:
        """
        Determine optimal worker count based on conditions
        """
        # Get average response times across all servers
        all_response_times = []
        
        with self._lock:
            for stats in self.server_stats.values():
                all_response_times.extend(stats['response_times'])
                
        if not all_response_times:
            return 3  # Default
            
        avg_response = sum(all_response_times) / len(all_response_times)
        
        # Adjust workers based on response time
        if avg_response < 0.5:
            return 5  # Fast responses, can handle more
        elif avg_response < 1.0:
            return 4
        elif avg_response < 2.0:
            return 3
        else:
            return 2  # Slow responses, reduce load
            
    def should_delay_upload(self) -> Tuple[bool, float]:
        """
        Check if uploads should be delayed
        Returns (should_delay, delay_seconds)
        """
        # Check overall error rate
        total_errors = sum(s['error_count'] for s in self.server_stats.values())
        total_success = sum(s['success_count'] for s in self.server_stats.values())
        
        if total_errors + total_success == 0:
            return False, 0
            
        error_rate = total_errors / (total_errors + total_success)
        
        # High error rate - back off
        if error_rate > 0.3:
            return True, 30.0  # 30 second delay
        elif error_rate > 0.1:
            return True, 10.0  # 10 second delay
            
        return False, 0