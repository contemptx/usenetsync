#!/usr/bin/env python3
"""
Database Write Queue System
Prevents database locking by serializing write operations
"""

import queue
import threading
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of database operations"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    BATCH = "batch"


@dataclass
class WriteOperation:
    """Represents a database write operation"""
    operation_type: OperationType
    table: str
    data: Any
    callback: Optional[Callable] = None
    priority: int = 5  # 1 = highest, 10 = lowest


class DatabaseWriteQueue:
    """
    Manages database writes through a queue to prevent locking
    """
    
    def __init__(self, db_manager, max_batch_size: int = 100, batch_timeout: float = 0.5):
        """
        Initialize write queue
        
        Args:
            db_manager: Database manager instance
            max_batch_size: Maximum operations to batch together
            batch_timeout: Maximum time to wait before flushing batch
        """
        self.db = db_manager
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        
        # Priority queue for operations
        self.queue = queue.PriorityQueue()
        
        # Batch for accumulating operations
        self.batch = []
        self.batch_lock = threading.Lock()
        self.last_flush = time.time()
        
        # Worker thread
        self.running = False
        self.worker_thread = None
        
        # Statistics
        self.stats = {
            'operations_queued': 0,
            'operations_completed': 0,
            'batches_processed': 0,
            'errors': 0
        }
    
    def start(self):
        """Start the write queue worker"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Database write queue started")
    
    def stop(self):
        """Stop the write queue worker"""
        if not self.running:
            return
        
        self.running = False
        
        # Add sentinel to wake up worker
        self.queue.put((10, None))
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        # Flush any remaining operations
        self._flush_batch()
        
        logger.info(f"Database write queue stopped. Stats: {self.stats}")
    
    def add_operation(self, operation: WriteOperation) -> bool:
        """
        Add an operation to the queue
        
        Returns:
            True if operation was queued successfully
        """
        if not self.running:
            logger.warning("Write queue not running, executing directly")
            return self._execute_operation(operation)
        
        try:
            # Add to priority queue (priority, operation)
            self.queue.put((operation.priority, operation))
            self.stats['operations_queued'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue operation: {e}")
            return False
    
    def add_segment(self, file_id: int, segment_data: Dict) -> Optional[int]:
        """
        Add a segment to the database
        """
        result_queue = queue.Queue()
        
        def callback(success, result):
            result_queue.put((success, result))
        
        operation = WriteOperation(
            operation_type=OperationType.INSERT,
            table='segments',
            data={
                'file_id': file_id,
                'segment_index': segment_data['index'],
                'message_id': segment_data.get('message_id'),
                'size': segment_data['size'],
                'hash': segment_data['hash'],
                'offset': segment_data.get('offset', 0)
            },
            callback=callback,
            priority=3
        )
        
        if self.add_operation(operation):
            # Wait for result
            try:
                success, result = result_queue.get(timeout=10)
                return result if success else None
            except queue.Empty:
                logger.error("Timeout waiting for segment insert")
                return None
        
        return None
    
    def batch_add_segments(self, segments: List[Tuple[int, Dict]]) -> int:
        """
        Add multiple segments in a batch
        
        Args:
            segments: List of (file_id, segment_data) tuples
            
        Returns:
            Number of segments successfully added
        """
        result_queue = queue.Queue()
        
        def callback(success, result):
            result_queue.put((success, result))
        
        operation = WriteOperation(
            operation_type=OperationType.BATCH,
            table='segments',
            data=segments,
            callback=callback,
            priority=2
        )
        
        if self.add_operation(operation):
            try:
                success, result = result_queue.get(timeout=30)
                return result if success else 0
            except queue.Empty:
                logger.error("Timeout waiting for batch insert")
                return 0
        
        return 0
    
    def _worker(self):
        """Worker thread that processes the queue"""
        logger.info("Write queue worker started")
        
        while self.running:
            try:
                # Get operation from queue with timeout
                priority, operation = self.queue.get(timeout=0.1)
                
                if operation is None:  # Sentinel
                    break
                
                # Add to batch
                with self.batch_lock:
                    self.batch.append(operation)
                
                # Check if we should flush
                should_flush = (
                    len(self.batch) >= self.max_batch_size or
                    time.time() - self.last_flush > self.batch_timeout
                )
                
                if should_flush:
                    self._flush_batch()
                
            except queue.Empty:
                # Check if we have pending operations to flush
                if self.batch and time.time() - self.last_flush > self.batch_timeout:
                    self._flush_batch()
            
            except Exception as e:
                logger.error(f"Worker error: {e}")
                self.stats['errors'] += 1
    
    def _flush_batch(self):
        """Flush accumulated operations to database"""
        with self.batch_lock:
            if not self.batch:
                return
            
            operations = self.batch[:]
            self.batch.clear()
            self.last_flush = time.time()
        
        # Group operations by type and table
        grouped = {}
        for op in operations:
            key = (op.operation_type, op.table)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(op)
        
        # Execute grouped operations
        for (op_type, table), ops in grouped.items():
            if op_type == OperationType.BATCH:
                self._execute_batch_operations(ops)
            else:
                self._execute_grouped_operations(op_type, table, ops)
        
        self.stats['batches_processed'] += 1
    
    def _execute_grouped_operations(self, op_type: OperationType, table: str, operations: List[WriteOperation]):
        """Execute a group of similar operations"""
        success_count = 0
        
        try:
            with self.db.pool.get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN DEFERRED")
                
                for op in operations:
                    try:
                        if op_type == OperationType.INSERT:
                            result = self._do_insert(conn, table, op.data)
                        elif op_type == OperationType.UPDATE:
                            result = self._do_update(conn, table, op.data)
                        elif op_type == OperationType.DELETE:
                            result = self._do_delete(conn, table, op.data)
                        else:
                            result = None
                        
                        success_count += 1
                        self.stats['operations_completed'] += 1
                        
                        # Call callback if provided
                        if op.callback:
                            op.callback(True, result)
                    
                    except Exception as e:
                        logger.error(f"Operation failed: {e}")
                        if op.callback:
                            op.callback(False, str(e))
                        self.stats['errors'] += 1
                
                # Commit transaction
                conn.commit()
                
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            # Rollback and notify callbacks
            try:
                conn.rollback()
            except:
                pass
            
            for op in operations[success_count:]:
                if op.callback:
                    op.callback(False, str(e))
    
    def _execute_batch_operations(self, operations: List[WriteOperation]):
        """Execute batch operations"""
        for op in operations:
            all_segments = op.data
            
            try:
                with self.db.pool.get_connection() as conn:
                    conn.execute("BEGIN DEFERRED")
                    
                    inserted = 0
                    for file_id, segment_data in all_segments:
                        cursor = conn.execute("""
                            INSERT INTO segments 
                            (file_id, segment_index, message_id, size, hash, offset)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            file_id,
                            segment_data['index'],
                            segment_data.get('message_id'),
                            segment_data['size'],
                            segment_data['hash'],
                            segment_data.get('offset', 0)
                        ))
                        inserted += 1
                    
                    conn.commit()
                    
                    if op.callback:
                        op.callback(True, inserted)
                    
                    self.stats['operations_completed'] += inserted
                    
            except Exception as e:
                logger.error(f"Batch insert failed: {e}")
                if op.callback:
                    op.callback(False, str(e))
                self.stats['errors'] += 1
    
    def _do_insert(self, conn, table: str, data: Dict) -> int:
        """Execute INSERT operation"""
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        
        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor = conn.execute(sql, list(data.values()))
        return cursor.lastrowid
    
    def _do_update(self, conn, table: str, data: Dict) -> int:
        """Execute UPDATE operation"""
        # Assumes 'id' field for WHERE clause
        id_value = data.pop('id')
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        
        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        cursor = conn.execute(sql, list(data.values()) + [id_value])
        return cursor.rowcount
    
    def _do_delete(self, conn, table: str, data: Dict) -> int:
        """Execute DELETE operation"""
        where_clause = ' AND '.join([f"{k} = ?" for k in data.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        
        cursor = conn.execute(sql, list(data.values()))
        return cursor.rowcount
    
    def _execute_operation(self, operation: WriteOperation) -> bool:
        """Execute a single operation directly"""
        try:
            with self.db.pool.get_connection() as conn:
                if operation.operation_type == OperationType.INSERT:
                    result = self._do_insert(conn, operation.table, operation.data)
                elif operation.operation_type == OperationType.UPDATE:
                    result = self._do_update(conn, operation.table, operation.data)
                elif operation.operation_type == OperationType.DELETE:
                    result = self._do_delete(conn, operation.table, operation.data)
                else:
                    result = None
                
                conn.commit()
                
                if operation.callback:
                    operation.callback(True, result)
                
                return True
                
        except Exception as e:
            logger.error(f"Direct operation failed: {e}")
            if operation.callback:
                operation.callback(False, str(e))
            return False
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'batch_size': len(self.batch)
        }


def test_write_queue():
    """Test the write queue system"""
    from src.database.enhanced_database_manager import DatabaseConfig, EnhancedDatabaseManager
    from complete_schema_fix import create_complete_schema
    
    print("Testing Database Write Queue")
    print("="*60)
    
    # Setup test database
    db_path = "test_workspace/queue_test.db"
    create_complete_schema(db_path)
    
    # Create database manager
    db_config = DatabaseConfig(path=db_path, pool_size=10)
    db = EnhancedDatabaseManager(db_config)
    
    # Create parent records first
    with db.pool.get_connection() as conn:
        # Create a test folder
        conn.execute("""
            INSERT INTO folders (folder_unique_id, folder_path, display_name, share_type)
            VALUES ('test_folder', '/test', 'Test Folder', 'private')
        """)
        folder_id = conn.lastrowid
        
        # Create test files
        conn.execute("""
            INSERT INTO files (folder_id, filename, file_path, size, hash)
            VALUES (?, 'file1.txt', '/test/file1.txt', 1000, 'hash1')
        """, (folder_id,))
        file1_id = conn.lastrowid
        
        conn.execute("""
            INSERT INTO files (folder_id, filename, file_path, size, hash)
            VALUES (?, 'file2.txt', '/test/file2.txt', 2000, 'hash2')
        """, (folder_id,))
        file2_id = conn.lastrowid
        
        conn.commit()
    
    # Create write queue
    write_queue = DatabaseWriteQueue(db, max_batch_size=10, batch_timeout=0.5)
    write_queue.start()
    
    print("✅ Write queue started")
    
    # Test single operations
    print("\nTesting single operations...")
    for i in range(5):
        segment_id = write_queue.add_segment(file1_id, {
            'index': i,
            'size': 1000 + i,
            'hash': f'hash_{i}',
            'message_id': f'msg_{i}'
        })
        print(f"  Added segment {i}: ID={segment_id}")
    
    # Test batch operations
    print("\nTesting batch operations...")
    segments = [
        (file2_id, {'index': i, 'size': 2000 + i, 'hash': f'batch_hash_{i}'})
        for i in range(20)
    ]
    
    count = write_queue.batch_add_segments(segments)
    print(f"✅ Batch inserted {count} segments")
    
    # Wait for operations to complete
    time.sleep(1)
    
    # Get statistics
    stats = write_queue.get_stats()
    print("\nQueue Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Stop queue
    write_queue.stop()
    print("\n✅ Write queue stopped")
    
    # Verify data
    with db.pool.get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM segments")
        count = cursor.fetchone()[0]
        print(f"\n✅ Total segments in database: {count}")
    
    db.pool.close_all()
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_write_queue()