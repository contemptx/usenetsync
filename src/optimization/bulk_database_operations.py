"""
Bulk Database Operations for PostgreSQL
Uses COPY command for 100x faster bulk inserts
"""

import io
import csv
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch, execute_values
from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class BulkDatabaseOperations:
    """Optimized bulk database operations using PostgreSQL COPY and batch operations"""
    
    def __init__(self, connection_params: dict, batch_size: int = 1000):
        self.connection_params = connection_params
        self.batch_size = batch_size
        self.logger = logger
        
    @contextmanager
    def get_connection(self):
        """Get database connection with optimized settings"""
        conn = psycopg2.connect(**self.connection_params)
        try:
            # Set performance optimizations
            with conn.cursor() as cur:
                cur.execute("SET work_mem = '256MB'")
                cur.execute("SET maintenance_work_mem = '512MB'")
                cur.execute("SET synchronous_commit = OFF")  # Faster writes
                cur.execute("SET effective_cache_size = '2GB'")
            yield conn
        finally:
            conn.close()
    
    def bulk_insert_copy(self, table_name: str, columns: List[str], 
                        data: List[tuple]) -> int:
        """
        Bulk insert using COPY command (100x faster than INSERT)
        
        Args:
            table_name: Name of the table
            columns: List of column names
            data: List of tuples containing data
            
        Returns:
            Number of rows inserted
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create in-memory CSV
                output = io.StringIO()
                writer = csv.writer(output, delimiter='\t')
                writer.writerows(data)
                output.seek(0)
                
                # Use COPY for ultra-fast insertion
                cur.copy_expert(
                    f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')",
                    output
                )
                
                conn.commit()
                return len(data)
    
    def bulk_insert_files(self, files_data: List[Dict]) -> int:
        """Bulk insert files using COPY"""
        columns = ['file_id', 'folder_id', 'name', 'size', 'hash', 'modified_at', 'created_at']
        
        # Prepare data for COPY
        rows = []
        for file_data in files_data:
            rows.append((
                file_data.get('file_id', str(uuid.uuid4())),
                file_data['folder_id'],
                file_data['name'],
                file_data['size'],
                file_data['hash'],
                file_data.get('modified_at', datetime.now()),
                file_data.get('created_at', datetime.now())
            ))
        
        return self.bulk_insert_copy('files', columns, rows)
    
    def bulk_insert_segments(self, segments_data: List[Dict]) -> int:
        """Bulk insert segments using COPY"""
        columns = ['segment_id', 'file_id', 'pack_id', 'segment_index', 
                  'size', 'hash', 'message_id', 'subject']
        
        rows = []
        for seg in segments_data:
            rows.append((
                seg.get('segment_id', str(uuid.uuid4())),
                seg.get('file_id'),
                seg.get('pack_id'),
                seg['segment_index'],
                seg['size'],
                seg.get('hash', ''),
                seg.get('message_id', ''),
                seg.get('subject', '')
            ))
        
        return self.bulk_insert_copy('segments', columns, rows)
    
    def bulk_update_batch(self, table_name: str, updates: List[Dict]) -> int:
        """
        Bulk update using execute_batch (10x faster than individual updates)
        
        Args:
            table_name: Name of the table
            updates: List of dicts with 'id', 'column', and 'value'
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Group updates by column
                updates_by_column = {}
                for update in updates:
                    column = update['column']
                    if column not in updates_by_column:
                        updates_by_column[column] = []
                    updates_by_column[column].append((update['value'], update['id']))
                
                total_updated = 0
                for column, values in updates_by_column.items():
                    query = f"UPDATE {table_name} SET {column} = %s WHERE id = %s"
                    execute_batch(cur, query, values, page_size=self.batch_size)
                    total_updated += cur.rowcount
                
                conn.commit()
                return total_updated
    
    def stream_large_result(self, query: str, params: tuple = None,
                           chunk_size: int = 10000) -> Generator[List[Dict], None, None]:
        """
        Stream large result sets to avoid memory issues
        
        Yields chunks of results instead of loading all into memory
        """
        with self.get_connection() as conn:
            with conn.cursor('streamer', cursor_factory=RealDictCursor) as cur:
                cur.itersize = chunk_size
                cur.execute(query, params)
                
                chunk = []
                for row in cur:
                    chunk.append(dict(row))
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                
                if chunk:
                    yield chunk
    
    def create_temp_table_from_data(self, temp_name: str, columns: List[str],
                                   data: List[tuple]) -> str:
        """Create and populate temporary table for complex joins"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create temp table
                column_defs = ', '.join([f"{col} TEXT" for col in columns])
                cur.execute(f"CREATE TEMP TABLE {temp_name} ({column_defs})")
                
                # Bulk insert data
                output = io.StringIO()
                writer = csv.writer(output, delimiter='\t')
                writer.writerows(data)
                output.seek(0)
                
                cur.copy_expert(
                    f"COPY {temp_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')",
                    output
                )
                
                conn.commit()
                return temp_name
    
    def optimize_for_bulk_read(self, table_name: str) -> None:
        """Optimize table for bulk read operations"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Update statistics
                cur.execute(f"ANALYZE {table_name}")
                
                # Create BRIN index for large sequential data
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_created_brin 
                    ON {table_name} USING BRIN(created_at)
                """)
                
                conn.commit()


class OptimizedProgressTracker:
    """Optimized progress tracking with batch updates"""
    
    def __init__(self, db_ops: BulkDatabaseOperations):
        self.db_ops = db_ops
        self.pending_updates = []
        self.update_threshold = 100
        
    def update_progress(self, progress_id: str, segments_completed: int,
                       bytes_transferred: int) -> None:
        """Queue progress update for batch processing"""
        self.pending_updates.append({
            'progress_id': progress_id,
            'segments_completed': segments_completed,
            'bytes_transferred': bytes_transferred,
            'updated_at': datetime.now()
        })
        
        # Flush if threshold reached
        if len(self.pending_updates) >= self.update_threshold:
            self.flush_updates()
    
    def flush_updates(self) -> int:
        """Flush all pending progress updates"""
        if not self.pending_updates:
            return 0
        
        with self.db_ops.get_connection() as conn:
            with conn.cursor() as cur:
                # Use execute_values for fast multi-row update
                query = """
                    UPDATE upload_progress AS up
                    SET uploaded_segments = data.segments,
                        bytes_uploaded = data.bytes,
                        updated_at = data.updated
                    FROM (VALUES %s) AS data(id, segments, bytes, updated)
                    WHERE up.progress_id = data.id::UUID
                """
                
                values = [
                    (u['progress_id'], u['segments_completed'], 
                     u['bytes_transferred'], u['updated_at'])
                    for u in self.pending_updates
                ]
                
                execute_values(cur, query, values)
                conn.commit()
                
                count = len(self.pending_updates)
                self.pending_updates.clear()
                return count


class DatabasePartitioner:
    """Handle database partitioning for massive datasets"""
    
    def __init__(self, db_ops: BulkDatabaseOperations):
        self.db_ops = db_ops
        
    def create_partitioned_table(self, base_table: str, partition_column: str,
                                partition_type: str = 'RANGE') -> None:
        """Create partitioned table for better performance with large datasets"""
        with self.db_ops.get_connection() as conn:
            with conn.cursor() as cur:
                # Create base partitioned table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {base_table}_partitioned (
                        LIKE {base_table} INCLUDING ALL
                    ) PARTITION BY {partition_type} ({partition_column})
                """)
                
                conn.commit()
    
    def create_monthly_partitions(self, base_table: str, start_year: int = 2024,
                                 num_months: int = 24) -> None:
        """Create monthly partitions for time-series data"""
        with self.db_ops.get_connection() as conn:
            with conn.cursor() as cur:
                for month_offset in range(num_months):
                    year = start_year + (month_offset // 12)
                    month = (month_offset % 12) + 1
                    
                    partition_name = f"{base_table}_{year}_{month:02d}"
                    start_date = f"{year}-{month:02d}-01"
                    
                    if month == 12:
                        end_date = f"{year + 1}-01-01"
                    else:
                        end_date = f"{year}-{month + 1:02d}-01"
                    
                    cur.execute(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {base_table}_partitioned
                        FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                    """)
                
                conn.commit()
    
    def create_size_based_partitions(self, base_table: str) -> None:
        """Create partitions based on file size for better query performance"""
        with self.db_ops.get_connection() as conn:
            with conn.cursor() as cur:
                # Small files (< 1MB)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {base_table}_small
                    PARTITION OF {base_table}_partitioned
                    FOR VALUES FROM (0) TO (1048576)
                """)
                
                # Medium files (1MB - 100MB)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {base_table}_medium
                    PARTITION OF {base_table}_partitioned
                    FOR VALUES FROM (1048576) TO (104857600)
                """)
                
                # Large files (> 100MB)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {base_table}_large
                    PARTITION OF {base_table}_partitioned
                    FOR VALUES FROM (104857600) TO (MAXVALUE)
                """)
                
                conn.commit()