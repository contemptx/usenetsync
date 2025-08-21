#!/usr/bin/env python3
"""
Persistent Queue System for Large-Scale Operations
Handles millions of upload/download tasks with resume capability
"""

import os
import json
import time
import uuid
import pickle
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass, asdict
from enum import Enum
from queue import PriorityQueue, Empty
import heapq

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    

@dataclass
class QueueTask:
    """Base task for persistent queue"""
    task_id: str
    priority: int
    created_at: float
    status: TaskStatus
    retry_count: int = 0
    max_retries: int = 3
    data: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[Dict] = None
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority < other.priority
        

@dataclass
class UploadTask(QueueTask):
    """Upload task with progress tracking"""
    file_id: str = ""
    folder_id: str = ""
    file_path: str = ""
    segments_total: int = 0
    segments_completed: int = 0
    bytes_uploaded: int = 0
    message_ids: Optional[List[str]] = None

    def __post_init__(self):
        if self.message_ids is None:
            self.message_ids = []
            

@dataclass
class DownloadTask(QueueTask):
    """Download task with progress tracking"""
    share_id: str = ""
    destination_path: str = ""
    segments_total: int = 0
    segments_completed: int = 0
    bytes_downloaded: int = 0
    message_ids: Optional[List[str]] = None

    def __post_init__(self):
        if self.message_ids is None:
            self.message_ids = []
            

class PersistentQueue:
    """
    File-based persistent queue for reliability
    Handles millions of tasks without memory exhaustion
    """
    
    def __init__(self, queue_dir: str, max_memory_items: int = 10000):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_items = max_memory_items
        self.memory_queue = PriorityQueue(maxsize=max_memory_items)
        self.disk_queue = []
        
        # Persistence files
        self.pending_file = self.queue_dir / "pending.json"
        self.in_progress_file = self.queue_dir / "in_progress.json"
        self.completed_file = self.queue_dir / "completed.json"
        self.failed_file = self.queue_dir / "failed.json"
        
        # Task tracking
        self.tasks = {}
        self._lock = threading.RLock()
        
        # Load existing tasks
        self._load_tasks()
        
    def _load_tasks(self):
        """Load tasks from disk on startup"""
        # Load pending tasks
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                pending = json.load(f)
                for task_data in pending:
                    task = self._deserialize_task(task_data)
                    self.tasks[task.task_id] = task
                    self._add_to_queue(task)
                    
        # Load in-progress tasks (convert back to pending for retry)
        if self.in_progress_file.exists():
            with open(self.in_progress_file, 'r') as f:
                in_progress = json.load(f)
                for task_data in in_progress:
                    task = self._deserialize_task(task_data)
                    task.status = TaskStatus.PENDING
                    self.tasks[task.task_id] = task
                    self._add_to_queue(task)
                    
        logger.info(f"Loaded {len(self.tasks)} tasks from disk")
        
    def _save_tasks(self):
        """Save current task state to disk"""
        with self._lock:
            # Group tasks by status
            pending = []
            in_progress = []
            completed = []
            failed = []
            
            for task in self.tasks.values():
                task_data = self._serialize_task(task)
                
                if task.status == TaskStatus.PENDING:
                    pending.append(task_data)
                elif task.status in (TaskStatus.IN_PROGRESS, TaskStatus.RETRYING):
                    in_progress.append(task_data)
                elif task.status == TaskStatus.COMPLETED:
                    completed.append(task_data)
                elif task.status == TaskStatus.FAILED:
                    failed.append(task_data)
                    
            # Save to files
            with open(self.pending_file, 'w') as f:
                json.dump(pending, f)
                
            with open(self.in_progress_file, 'w') as f:
                json.dump(in_progress, f)
                
            # Append to completed/failed (don't overwrite history)
            if completed:
                existing = []
                if self.completed_file.exists():
                    with open(self.completed_file, 'r') as f:
                        existing = json.load(f)
                existing.extend(completed)
                
                # Keep only last 10000 completed
                if len(existing) > 10000:
                    existing = existing[-10000:]
                    
                with open(self.completed_file, 'w') as f:
                    json.dump(existing, f)
                    
            if failed:
                existing = []
                if self.failed_file.exists():
                    with open(self.failed_file, 'r') as f:
                        existing = json.load(f)
                existing.extend(failed)
                
                with open(self.failed_file, 'w') as f:
                    json.dump(existing, f)
                    
    def _serialize_task(self, task: QueueTask) -> Dict:
        """Serialize task to JSON-compatible dict"""
        data = asdict(task)
        data['status'] = task.status.value
        data['task_type'] = task.__class__.__name__
        return data
        
    def _deserialize_task(self, data: Dict) -> QueueTask:
        """Deserialize task from dict"""
        task_type = data.pop('task_type', 'QueueTask')
        data['status'] = TaskStatus(data['status'])
        
        if task_type == 'UploadTask':
            return UploadTask(**data)
        elif task_type == 'DownloadTask':
            return DownloadTask(**data)
        else:
            return QueueTask(**data)
            
    def _add_to_queue(self, task: QueueTask):
        """Add task to appropriate queue"""
        try:
            # Try memory queue first
            self.memory_queue.put_nowait((task.priority, task.task_id))
        except:
            # Fall back to disk queue
            heapq.heappush(self.disk_queue, (task.priority, task.task_id))
            
    def add_task(self, task: QueueTask) -> str:
        """Add new task to queue"""
        with self._lock:
            if not task.task_id:
                task.task_id = str(uuid.uuid4())
                
            task.created_at = time.time()
            task.status = TaskStatus.PENDING
            
            self.tasks[task.task_id] = task
            self._add_to_queue(task)
            
            # Save periodically
            if len(self.tasks) % 100 == 0:
                self._save_tasks()
                
                return task.task_id

    def get_task(self, timeout: float = None) -> Optional[QueueTask]:
        """Get next task from queue"""
        task_id = None
        
        # Try memory queue first
        try:
            priority, task_id = self.memory_queue.get(timeout=timeout)
        except Empty:
            # Try disk queue
            with self._lock:
                if self.disk_queue:
                    priority, task_id = heapq.heappop(self.disk_queue)
                    
        if task_id:
            with self._lock:
                task = self.tasks.get(task_id)
                if task and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.IN_PROGRESS
                    return task
                    
        return None
        
    def update_task(self, task_id: str, **updates):
        """Update task state"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                        
                # Save if status changed
                if 'status' in updates:
                    self._save_tasks()
                    
    def complete_task(self, task_id: str):
        """Mark task as completed"""
        self.update_task(task_id, status=TaskStatus.COMPLETED)
        
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.error = error
                task.retry_count += 1
                
                if task.retry_count < task.max_retries:
                    # Retry with exponential backoff
                    task.status = TaskStatus.RETRYING
                    task.priority += task.retry_count * 10
                    self._add_to_queue(task)
                else:
                    task.status = TaskStatus.FAILED
                    
                self._save_tasks()
                
    def get_statistics(self) -> Dict:
        """Get queue statistics"""
        with self._lock:
            stats = {
                'total': len(self.tasks),
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'failed': 0,
                'retrying': 0
            }
            
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING:
                    stats['pending'] += 1
                elif task.status == TaskStatus.IN_PROGRESS:
                    stats['in_progress'] += 1
                elif task.status == TaskStatus.COMPLETED:
                    stats['completed'] += 1
                elif task.status == TaskStatus.FAILED:
                    stats['failed'] += 1
                elif task.status == TaskStatus.RETRYING:
                    stats['retrying'] += 1
                    
            return stats
            
    def cleanup_completed(self, older_than: float = 86400):
        """Remove completed tasks older than specified seconds"""
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            for task_id, task in self.tasks.items():
                if (task.status == TaskStatus.COMPLETED and 
                    current_time - task.created_at > older_than):
                    to_remove.append(task_id)
                    
            for task_id in to_remove:
                del self.tasks[task_id]
                
            if to_remove:
                self._save_tasks()
                
            return len(to_remove)
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                
                # Save periodically
                if len(self.tasks) % 10 == 0:
                    self._save_tasks()
    
    def update_task_progress(self, task_id: str, progress: Dict):
        """Update task progress"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.progress is None:
                    task.progress = {}
                task.progress.update(progress)
                
                # Update specific fields for upload/download tasks
                if isinstance(task, UploadTask):
                    for key, value in progress.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                elif isinstance(task, DownloadTask):
                    for key, value in progress.items():
                        if hasattr(task, key):
                            setattr(task, key, value)


class ResumableUploadQueue(PersistentQueue):
    """
    Specialized queue for resumable uploads
    Tracks segment-level progress for 30M+ segments
    """
    
    def __init__(self, queue_dir: str, db_manager):
        super().__init__(queue_dir)
        self.db_manager = db_manager
        
    def add_upload(self, file_id: str, folder_id: str, 
                   file_path: str, segments: List[Dict]) -> str:
        """Add upload task with segment tracking"""
        task = UploadTask(
            task_id=str(uuid.uuid4()),
            priority=1,  # Can be adjusted based on file size
            created_at=time.time(),
            status=TaskStatus.PENDING,
            file_id=file_id,
            folder_id=folder_id,
            file_path=file_path,
            segments_total=len(segments),
            segments_completed=0,
            data={'segments': segments}
        )
        
        return self.add_task(task)
        
    def update_upload_progress(self, task_id: str, segment_index: int, 
                              message_id: str, bytes_uploaded: int):
        """Update upload progress for a segment"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if isinstance(task, UploadTask):
                    task.segments_completed += 1
                    task.bytes_uploaded += bytes_uploaded
                    task.message_ids.append(message_id)
                    
                    # Update progress
                    task.progress = {
                        'percent': (task.segments_completed / task.segments_total) * 100,
                        'segments': f"{task.segments_completed}/{task.segments_total}",
                        'bytes': task.bytes_uploaded
                    }
                    
                    # Save progress to database
                    self.db_manager.save_progress(
                        task_id,
                        'upload',
                        {
                            'total_items': task.segments_total,
                            'processed_items': task.segments_completed,
                            'last_item_id': str(segment_index),
                            'state': {
                                'file_id': task.file_id,
                                'message_ids': task.message_ids,
                                'bytes_uploaded': task.bytes_uploaded
                            }
                        }
                    )
                    
    def resume_uploads(self) -> List[UploadTask]:
        """Get all incomplete uploads for resuming"""
        resumable = []
        
        with self._lock:
            for task in self.tasks.values():
                if isinstance(task, UploadTask):
                    if task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS, 
                                      TaskStatus.RETRYING):
                        # Load saved progress
                        progress = self.db_manager.load_progress(task.task_id)
                        if progress:
                            task.segments_completed = progress['processed_items']
                            task.message_ids = progress['state'].get('message_ids', [])
                            task.bytes_uploaded = progress['state'].get('bytes_uploaded', 0)
                            
                        resumable.append(task)
                        
        return resumable
        

class ResumableDownloadQueue(PersistentQueue):
    """
    Specialized queue for resumable downloads
    Handles partial downloads and segment verification
    """
    
    def __init__(self, queue_dir: str, db_manager):
        super().__init__(queue_dir)
        self.db_manager = db_manager
        
    def add_download(self, share_id: str, destination_path: str,
                    segments: List[Dict]) -> str:
        """Add download task with segment tracking"""
        task = DownloadTask(
            task_id=str(uuid.uuid4()),
            priority=1,
            created_at=time.time(),
            status=TaskStatus.PENDING,
            share_id=share_id,
            destination_path=destination_path,
            segments_total=len(segments),
            segments_completed=0,
            data={'segments': segments}
        )
        
        return self.add_task(task)
        
    def update_download_progress(self, task_id: str, segment_index: int,
                                bytes_downloaded: int):
        """Update download progress for a segment"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if isinstance(task, DownloadTask):
                    task.segments_completed += 1
                    task.bytes_downloaded += bytes_downloaded
                    
                    # Update progress
                    task.progress = {
                        'percent': (task.segments_completed / task.segments_total) * 100,
                        'segments': f"{task.segments_completed}/{task.segments_total}",
                        'bytes': task.bytes_downloaded
                    }
                    
                    # Save progress
                    self.db_manager.save_progress(
                        task_id,
                        'download',
                        {
                            'total_items': task.segments_total,
                            'processed_items': task.segments_completed,
                            'last_item_id': str(segment_index),
                            'state': {
                                'share_id': task.share_id,
                                'destination': task.destination_path,
                                'bytes_downloaded': task.bytes_downloaded
                            }
                        }
                    )
                    

# Example usage
if __name__ == "__main__":
    from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
    
    # Setup database
    config = PostgresConfig(embedded=True)
    db_manager = ShardedPostgreSQLManager(config)
    
    # Create upload queue
    upload_queue = ResumableUploadQueue("./queues/upload", db_manager)
    
    # Add upload task
    task_id = upload_queue.add_upload(
        file_id="file123",
        folder_id="folder456",
        file_path="/path/to/large/file.zip",
        segments=[{'index': i, 'size': 750000} for i in range(1000)]
    )
    
    print(f"Added upload task: {task_id}")
    
    # Simulate progress
    for i in range(10):
        upload_queue.update_upload_progress(
            task_id,
            segment_index=i,
            message_id=f"<msg{i}@ngPost.com>",
            bytes_uploaded=750000
        )
        
    # Get statistics
    stats = upload_queue.get_statistics()
    print(f"Queue statistics: {stats}")
    
    # Resume uploads
    resumable = upload_queue.resume_uploads()
    print(f"Resumable uploads: {len(resumable)}")