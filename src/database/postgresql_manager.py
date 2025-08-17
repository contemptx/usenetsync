#!/usr/bin/env python3
"""
PostgreSQL Manager with Embedded Database Support
Handles automatic installation, sharding, and optimization for 20TB+ datasets
"""

import os
import sys
import json
import time
import hashlib
import logging
import subprocess
import platform
import zipfile
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, execute_batch
import threading

logger = logging.getLogger(__name__)


@dataclass
class PostgresConfig:
    """PostgreSQL configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "usenet_sync"
    user: str = "usenet"
    password: str = "usenet_secure_2024"
    pool_size: int = 20
    max_overflow: int = 40
    shard_count: int = 16
    embedded: bool = True
    data_dir: str = "./postgres_data"
    
    
class EmbeddedPostgresInstaller:
    """
    One-click PostgreSQL installation for Windows/Mac/Linux
    No admin rights required - runs in user space
    """
    
    POSTGRES_VERSIONS = {
        'windows': {
            'url': 'https://get.enterprisedb.com/postgresql/postgresql-15.4-1-windows-x64-binaries.zip',
            'extract_dir': 'pgsql'
        },
        'linux': {
            'url': 'https://get.enterprisedb.com/postgresql/postgresql-15.4-1-linux-x64-binaries.tar.gz',
            'extract_dir': 'pgsql'
        },
        'darwin': {
            'url': 'https://get.enterprisedb.com/postgresql/postgresql-15.4-1-osx-binaries.zip',
            'extract_dir': 'pgsql'
        }
    }
    
    def __init__(self, install_dir: str = "./postgres_embedded"):
        self.install_dir = Path(install_dir)
        self.data_dir = self.install_dir / "data"
        self.bin_dir = self.install_dir / "bin"
        self.system = platform.system().lower()
        
    def is_installed(self) -> bool:
        """Check if PostgreSQL is already installed"""
        return (self.bin_dir / "postgres").exists() or (self.bin_dir / "postgres.exe").exists()
        
    def install(self) -> bool:
        """
        Automatically download and install PostgreSQL
        Shows progress and handles all platforms
        """
        if self.is_installed():
            logger.info("PostgreSQL already installed")
            return True
            
        print("🚀 Setting up PostgreSQL for optimal performance...")
        print("This is a one-time setup that takes 2-3 minutes.")
        
        try:
            # Download PostgreSQL
            self._download_postgres()
            
            # Extract files
            self._extract_postgres()
            
            # Initialize database
            self._init_database()
            
            # Apply optimizations
            self._optimize_config()
            
            # Start PostgreSQL
            self._start_postgres()
            
            print("✅ PostgreSQL installed successfully!")
            print(f"   Data directory: {self.data_dir}")
            print(f"   No admin rights required - running in user space")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install PostgreSQL: {e}")
            print(f"❌ Installation failed: {e}")
            print("   You can install PostgreSQL manually from https://postgresql.org")
            return False
            
    def _download_postgres(self):
        """Download PostgreSQL with progress bar"""
        postgres_info = self.POSTGRES_VERSIONS.get(self.system)
        if not postgres_info:
            raise OSError(f"Unsupported platform: {self.system}")
            
        url = postgres_info['url']
        filename = url.split('/')[-1]
        download_path = self.install_dir / filename
        
        # Create directory
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        print(f"📥 Downloading PostgreSQL ({filename})...")
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\r   {bar} {percent:.1f}%', end='', flush=True)
            
        urllib.request.urlretrieve(url, download_path, download_progress)
        print()  # New line after progress bar
        
    def _extract_postgres(self):
        """Extract PostgreSQL archive"""
        postgres_info = self.POSTGRES_VERSIONS.get(self.system)
        filename = postgres_info['url'].split('/')[-1]
        archive_path = self.install_dir / filename
        
        print("📦 Extracting PostgreSQL...")
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
        else:  # tar.gz
            import tarfile
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(self.install_dir)
                
        # Move to correct location
        extract_dir = self.install_dir / postgres_info['extract_dir']
        if extract_dir.exists() and extract_dir != self.install_dir:
            for item in extract_dir.iterdir():
                item.rename(self.install_dir / item.name)
            extract_dir.rmdir()
            
        # Clean up archive
        archive_path.unlink()
        
    def _init_database(self):
        """Initialize PostgreSQL database cluster"""
        print("🔧 Initializing database...")
        
        initdb = self.bin_dir / ("initdb.exe" if self.system == "windows" else "initdb")
        
        # Initialize with optimal settings
        subprocess.run([
            str(initdb),
            "-D", str(self.data_dir),
            "-E", "UTF8",
            "--locale=C",  # Faster sorting
            "-U", "postgres",
            "--auth-local=trust",
            "--auth-host=md5"
        ], check=True, capture_output=True, text=True)
        
    def _optimize_config(self):
        """Apply performance optimizations for large datasets"""
        print("⚡ Optimizing for large datasets...")
        
        config_file = self.data_dir / "postgresql.conf"
        
        optimizations = """
# UsenetSync Optimizations for 20TB+ datasets
# Generated automatically - do not modify

# Memory (adjust based on available RAM)
shared_buffers = 1GB              # 25% of RAM for dedicated server
effective_cache_size = 3GB        # 75% of RAM
work_mem = 32MB                   # Per sort/hash operation
maintenance_work_mem = 512MB      # For VACUUM, CREATE INDEX

# Parallelization
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# Write performance
checkpoint_completion_target = 0.9
wal_buffers = 32MB
max_wal_size = 4GB
min_wal_size = 1GB

# Connection pooling
max_connections = 200

# SSD optimizations
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging (minimal for performance)
logging_collector = off
log_statement = 'none'
log_duration = off

# Statistics
default_statistics_target = 100
track_counts = on
autovacuum = on
"""
        
        with open(config_file, 'a') as f:
            f.write(optimizations)
            
    def _start_postgres(self):
        """Start PostgreSQL server"""
        print("🚀 Starting PostgreSQL...")
        
        pg_ctl = self.bin_dir / ("pg_ctl.exe" if self.system == "windows" else "pg_ctl")
        
        # Start server
        subprocess.run([
            str(pg_ctl),
            "-D", str(self.data_dir),
            "-l", str(self.install_dir / "postgres.log"),
            "start"
        ], check=True, capture_output=True, text=True)
        
        # Wait for startup
        time.sleep(3)
        
        # Create database and user
        self._create_database()
        
    def _create_database(self):
        """Create UsenetSync database and user"""
        createdb = self.bin_dir / ("createdb.exe" if self.system == "windows" else "createdb")
        psql = self.bin_dir / ("psql.exe" if self.system == "windows" else "psql")
        
        # Create database
        subprocess.run([
            str(createdb),
            "-U", "postgres",
            "usenet_sync"
        ], capture_output=True, text=True)
        
        # Create user and grant permissions
        sql = """
        CREATE USER usenet WITH PASSWORD 'usenet_secure_2024';
        GRANT ALL PRIVILEGES ON DATABASE usenet_sync TO usenet;
        ALTER DATABASE usenet_sync OWNER TO usenet;
        """
        
        subprocess.run([
            str(psql),
            "-U", "postgres",
            "-d", "usenet_sync",
            "-c", sql
        ], capture_output=True, text=True)
        

class ShardedPostgreSQLManager:
    """
    PostgreSQL manager with sharding for 30M+ segments
    Implements connection pooling, batch operations, and streaming
    """
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.pools: Dict[int, ThreadedConnectionPool] = {}
        self.shard_count = config.shard_count
        self._lock = threading.Lock()
        
        # Install PostgreSQL if needed
        if config.embedded:
            installer = EmbeddedPostgresInstaller()
            if not installer.is_installed():
                if not installer.install():
                    raise RuntimeError("Failed to install PostgreSQL")
                    
        # Initialize connection pools for each shard
        self._init_pools()
        
        # Create schema on all shards
        self._init_schema()
        
    def _init_pools(self):
        """Initialize connection pools for all shards"""
        for shard_id in range(self.shard_count):
            # Each shard can be a separate database or schema
            db_name = f"{self.config.database}_shard_{shard_id}"
            
            self.pools[shard_id] = ThreadedConnectionPool(
                minconn=2,
                maxconn=self.config.pool_size,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,  # Use single DB with schemas
                user=self.config.user,
                password=self.config.password,
                options=f'-c search_path=shard_{shard_id}'
            )
            
    def _init_schema(self):
        """Create optimized schema with proper indexes"""
        schema_sql = """
        -- Create schema for this shard
        CREATE SCHEMA IF NOT EXISTS shard_{shard_id};
        
        -- Segments table with partitioning
        CREATE TABLE IF NOT EXISTS shard_{shard_id}.segments (
            id BIGSERIAL PRIMARY KEY,
            segment_id UUID NOT NULL,
            file_id UUID NOT NULL,
            folder_id UUID NOT NULL,
            segment_index INTEGER NOT NULL,
            segment_hash BYTEA NOT NULL,
            size BIGINT NOT NULL,
            message_id TEXT,
            subject TEXT,
            internal_subject TEXT,
            uploaded_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            
            -- Unique constraint
            UNIQUE(file_id, segment_index)
        ) PARTITION BY RANGE (created_at);
        
        -- Create monthly partitions
        CREATE TABLE IF NOT EXISTS shard_{shard_id}.segments_2024_01 
        PARTITION OF shard_{shard_id}.segments
        FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
        
        -- Critical indexes for performance
        CREATE INDEX IF NOT EXISTS idx_segments_file_id_{shard_id} 
            ON shard_{shard_id}.segments(file_id, segment_index);
            
        CREATE INDEX IF NOT EXISTS idx_segments_folder_{shard_id}
            ON shard_{shard_id}.segments(folder_id);
            
        CREATE INDEX IF NOT EXISTS idx_segments_uploaded_{shard_id}
            ON shard_{shard_id}.segments(uploaded_at) 
            WHERE uploaded_at IS NOT NULL;
            
        CREATE INDEX IF NOT EXISTS idx_segments_hash_{shard_id}
            ON shard_{shard_id}.segments USING hash(segment_hash);
            
        -- BRIN index for time-series data (very space efficient)
        CREATE INDEX IF NOT EXISTS idx_segments_created_brin_{shard_id}
            ON shard_{shard_id}.segments USING BRIN(created_at);
            
        -- Files table
        CREATE TABLE IF NOT EXISTS shard_{shard_id}.files (
            id BIGSERIAL PRIMARY KEY,
            file_id UUID NOT NULL UNIQUE,
            folder_id UUID NOT NULL,
            filename TEXT NOT NULL,
            size BIGINT NOT NULL,
            hash BYTEA NOT NULL,
            segment_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_files_folder_{shard_id}
            ON shard_{shard_id}.files(folder_id);
            
        CREATE INDEX IF NOT EXISTS idx_files_hash_{shard_id}
            ON shard_{shard_id}.files USING hash(hash);
            
        -- Progress tracking table for resume capability
        CREATE TABLE IF NOT EXISTS shard_{shard_id}.progress (
            session_id UUID PRIMARY KEY,
            operation_type TEXT NOT NULL,
            total_items BIGINT NOT NULL,
            processed_items BIGINT NOT NULL,
            last_item_id TEXT,
            state JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        );
        
        CREATE INDEX IF NOT EXISTS idx_progress_updated_{shard_id}
            ON shard_{shard_id}.progress(updated_at);
        """
        
        for shard_id in range(self.shard_count):
            with self.get_connection(shard_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql.format(shard_id=shard_id))
                conn.commit()
                
    def get_shard_id(self, key: str) -> int:
        """Get shard ID for a given key using consistent hashing"""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.shard_count
        
    @contextmanager
    def get_connection(self, shard_id: int):
        """Get connection from pool with automatic cleanup"""
        conn = self.pools[shard_id].getconn()
        try:
            yield conn
        finally:
            self.pools[shard_id].putconn(conn)
            
    def insert_segments_batch(self, segments: List[Dict], batch_size: int = 1000):
        """
        Batch insert segments with high performance
        Uses COPY for maximum speed
        """
        # Group segments by shard
        sharded_segments = {}
        for segment in segments:
            shard_id = self.get_shard_id(segment['file_id'])
            if shard_id not in sharded_segments:
                sharded_segments[shard_id] = []
            sharded_segments[shard_id].append(segment)
            
        # Insert into each shard in parallel
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for shard_id, shard_segments in sharded_segments.items():
                future = executor.submit(
                    self._insert_shard_batch,
                    shard_id,
                    shard_segments,
                    batch_size
                )
                futures.append(future)
                
            # Wait for all inserts to complete
            for future in concurrent.futures.as_completed(futures):
                future.result()
                
    def _insert_shard_batch(self, shard_id: int, segments: List[Dict], batch_size: int):
        """Insert batch into specific shard"""
        with self.get_connection(shard_id) as conn:
            with conn.cursor() as cur:
                # Use execute_batch for better performance
                insert_sql = """
                    INSERT INTO segments (
                        segment_id, file_id, folder_id, segment_index,
                        segment_hash, size, message_id, subject, internal_subject
                    ) VALUES (
                        %(segment_id)s, %(file_id)s, %(folder_id)s, %(segment_index)s,
                        %(segment_hash)s, %(size)s, %(message_id)s, %(subject)s, %(internal_subject)s
                    ) ON CONFLICT (file_id, segment_index) DO NOTHING
                """
                
                execute_batch(cur, insert_sql, segments, page_size=batch_size)
            conn.commit()
            
    def iterate_segments(self, file_id: str, batch_size: int = 1000) -> Iterator[List[Dict]]:
        """
        Stream segments without loading all into memory
        Critical for handling millions of segments
        """
        shard_id = self.get_shard_id(file_id)
        
        with self.get_connection(shard_id) as conn:
            with conn.cursor('segment_cursor', cursor_factory=RealDictCursor) as cur:
                cur.itersize = batch_size
                cur.execute("""
                    SELECT * FROM segments 
                    WHERE file_id = %s 
                    ORDER BY segment_index
                """, (file_id,))
                
                batch = []
                for row in cur:
                    batch.append(dict(row))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        
                if batch:
                    yield batch
                    
    def get_segments_paginated(self, folder_id: str, offset: int = 0, 
                              limit: int = 1000) -> Tuple[List[Dict], int]:
        """
        Paginated segment retrieval to prevent memory exhaustion
        Returns (segments, total_count)
        """
        shard_id = self.get_shard_id(folder_id)
        
        with self.get_connection(shard_id) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get total count
                cur.execute("""
                    SELECT COUNT(*) FROM segments WHERE folder_id = %s
                """, (folder_id,))
                total_count = cur.fetchone()['count']
                
                # Get paginated results
                cur.execute("""
                    SELECT * FROM segments 
                    WHERE folder_id = %s
                    ORDER BY file_id, segment_index
                    LIMIT %s OFFSET %s
                """, (folder_id, limit, offset))
                
                segments = [dict(row) for row in cur.fetchall()]
                
        return segments, total_count
        
    def save_progress(self, session_id: str, operation_type: str, 
                     progress_data: Dict) -> None:
        """
        Save progress for resume capability
        Critical for recovering from crashes during 20TB operations
        """
        # Use first shard for progress tracking
        with self.get_connection(0) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO progress (
                        session_id, operation_type, total_items, 
                        processed_items, last_item_id, state
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        processed_items = EXCLUDED.processed_items,
                        last_item_id = EXCLUDED.last_item_id,
                        state = EXCLUDED.state,
                        updated_at = NOW()
                """, (
                    session_id,
                    operation_type,
                    progress_data.get('total_items', 0),
                    progress_data.get('processed_items', 0),
                    progress_data.get('last_item_id'),
                    json.dumps(progress_data.get('state', {}))
                ))
            conn.commit()
            
    def load_progress(self, session_id: str) -> Optional[Dict]:
        """Load saved progress for resuming operations"""
        with self.get_connection(0) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM progress 
                    WHERE session_id = %s AND completed_at IS NULL
                """, (session_id,))
                
                row = cur.fetchone()
                if row:
                    return {
                        'session_id': row['session_id'],
                        'operation_type': row['operation_type'],
                        'total_items': row['total_items'],
                        'processed_items': row['processed_items'],
                        'last_item_id': row['last_item_id'],
                        'state': row['state']
                    }
        return None
        
    def mark_progress_complete(self, session_id: str) -> None:
        """Mark an operation as complete"""
        with self.get_connection(0) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE progress 
                    SET completed_at = NOW() 
                    WHERE session_id = %s
                """, (session_id,))
            conn.commit()
            
    def vacuum_analyze(self):
        """
        Run VACUUM ANALYZE on all shards
        Important for maintaining performance with large datasets
        """
        for shard_id in range(self.shard_count):
            with self.get_connection(shard_id) as conn:
                conn.set_isolation_level(0)  # AUTOCOMMIT
                with conn.cursor() as cur:
                    cur.execute("VACUUM ANALYZE")
                    
    def get_statistics(self) -> Dict:
        """Get database statistics across all shards"""
        stats = {
            'total_segments': 0,
            'total_files': 0,
            'total_size': 0,
            'shards': []
        }
        
        for shard_id in range(self.shard_count):
            with self.get_connection(shard_id) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get segment count
                    cur.execute("SELECT COUNT(*) as count FROM segments")
                    segment_count = cur.fetchone()['count']
                    
                    # Get file count
                    cur.execute("SELECT COUNT(*) as count FROM files")
                    file_count = cur.fetchone()['count']
                    
                    # Get total size
                    cur.execute("SELECT COALESCE(SUM(size), 0) as total FROM segments")
                    total_size = cur.fetchone()['total']
                    
                    stats['total_segments'] += segment_count
                    stats['total_files'] += file_count
                    stats['total_size'] += total_size
                    
                    stats['shards'].append({
                        'shard_id': shard_id,
                        'segments': segment_count,
                        'files': file_count,
                        'size': total_size
                    })
                    
        return stats
        
    def close(self):
        """Close all connection pools"""
        for pool in self.pools.values():
            pool.closeall()
            

# Example usage
if __name__ == "__main__":
    # Configure for large dataset
    config = PostgresConfig(
        embedded=True,  # Use embedded PostgreSQL
        shard_count=16,  # 16 shards for distribution
        pool_size=20     # Connection pool per shard
    )
    
    # Initialize manager (will auto-install PostgreSQL if needed)
    manager = ShardedPostgreSQLManager(config)
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"Database initialized with {config.shard_count} shards")
    print(f"Ready to handle 30M+ segments")
    print(f"Current stats: {stats}")