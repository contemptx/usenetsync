#!/usr/bin/env python3
"""
Unified Database Module - Consolidates ALL database functionality
Supports both SQLite and PostgreSQL with production features
"""

import os
import sqlite3
import json
import threading
import queue
import time
import logging
import hashlib
try:
    import psycopg2
    import psycopg2.pool
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    psycopg2 = None
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Generator
from pathlib import Path
from enum import Enum

# Fix for SQLite datetime deprecation warning (Python 3.12+)
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

def convert_timestamp(b):
    """Convert timestamp from database - handles both Unix timestamps and ISO format"""
    value = b.decode()
    try:
        # Try to parse as float (Unix timestamp)
        return datetime.fromtimestamp(float(value))
    except ValueError:
        # Try to parse as ISO format string
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            # If all else fails, return current time
            logger.warning(f"Could not parse timestamp: {value}")
            return datetime.now()

sqlite3.register_converter("timestamp", convert_timestamp)

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """Database backend types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

@dataclass
class DatabaseConfig:
    """Unified database configuration"""
    db_type: DatabaseType = DatabaseType.SQLITE
    
    # SQLite settings
    sqlite_path: str = "data/usenetsync.db"
    sqlite_pool_size: int = 10
    sqlite_timeout: float = 30.0
    enable_wal: bool = True
    cache_size: int = 10000
    
    # PostgreSQL settings
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "usenetsync"
    pg_user: str = "usenetsync"
    pg_password: str = ""
    pg_pool_size: int = 20
    pg_max_overflow: int = 10
    
    # Common settings
    enable_monitoring: bool = True
    enable_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 0.1
    
    # Performance settings
    batch_size: int = 1000
    chunk_size: int = 10000
    enable_streaming: bool = True
    
    # Sharding settings (for 20TB+ datasets)
    enable_sharding: bool = False
    shard_count: int = 16
    shard_key: str = "entity_id"

class ConnectionPool:
    """Thread-safe connection pool for both SQLite and PostgreSQL"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._lock = threading.Lock()
        self._closed = False
        self._monitor = {
            'connections_created': 0,
            'connections_reused': 0,
            'connection_errors': 0,
            'queries_executed': 0,
            'query_errors': 0
        }
        
        if config.db_type == DatabaseType.POSTGRESQL:
            self._init_postgresql()
        else:
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite connection pool"""
        self.pool = queue.Queue(maxsize=self.config.sqlite_pool_size)
        self._all_connections = []
        
        os.makedirs(os.path.dirname(self.config.sqlite_path), exist_ok=True)
        
        for _ in range(self.config.sqlite_pool_size):
            conn = self._create_sqlite_connection()
            self.pool.put(conn)
            self._all_connections.append(conn)
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=self.config.pg_pool_size,
            host=self.config.pg_host,
            port=self.config.pg_port,
            database=self.config.pg_database,
            user=self.config.pg_user,
            password=self.config.pg_password
        )
    
    def _create_sqlite_connection(self) -> sqlite3.Connection:
        """Create optimized SQLite connection"""
        conn = sqlite3.connect(
            self.config.sqlite_path,
            timeout=self.config.sqlite_timeout,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        
        # Apply optimizations
        conn.execute("PRAGMA busy_timeout=5000")
        if self.config.enable_wal:
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(f"PRAGMA cache_size={self.config.cache_size}")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        self._monitor['connections_created'] += 1
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with monitoring"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        conn = None
        start_time = time.time()
        
        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                conn = self.pool.getconn()
                conn.autocommit = False
            else:
                conn = self.pool.get(timeout=self.config.sqlite_timeout)
            
            self._monitor['connections_reused'] += 1
            yield conn
            
            if self.config.db_type == DatabaseType.POSTGRESQL:
                conn.commit()
                
        except Exception as e:
            self._monitor['connection_errors'] += 1
            if conn and self.config.db_type == DatabaseType.POSTGRESQL:
                conn.rollback()
            raise
            
        finally:
            if conn:
                if self.config.db_type == DatabaseType.POSTGRESQL:
                    self.pool.putconn(conn)
                else:
                    self.pool.put(conn)
            
            # Log slow connections
            elapsed = time.time() - start_time
            if elapsed > 1.0:
                logger.warning(f"Slow connection: {elapsed:.2f}s")
    
    def close_all(self):
        """Close all connections in pool"""
        with self._lock:
            self._closed = True
            
            if self.config.db_type == DatabaseType.POSTGRESQL:
                self.pool.closeall()
            else:
                for conn in self._all_connections:
                    try:
                        conn.close()
                    except:
                        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return dict(self._monitor)

class UnifiedDatabase:
    """
    Unified database manager consolidating all database operations
    Supports SQLite and PostgreSQL with full production features
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize unified database with configuration"""
        self.config = config or DatabaseConfig()
        self.db_path = getattr(self.config, 'path', getattr(self.config, 'sqlite_path', 'data/usenetsync.db'))  # Store path for status endpoint
        self.pool = ConnectionPool(self.config)
        self._lock = threading.Lock()
        self._transaction_stack = threading.local()
        
        # Monitoring
        self._monitor = {
            'queries': {},
            'errors': {},
            'transactions': 0,
            'rollbacks': 0,
            'slow_queries': [],
            'start_time': time.time()
        }
        
        # Initialize schema
        self._ensure_schema()
        
        logger.info(f"Initialized {self.config.db_type.value} database")
    
    def _ensure_schema(self):
        """Ensure database schema exists"""
        # Disabled - we manage schema manually
        # from .schema import UnifiedSchema
        # schema = UnifiedSchema(self)
        # schema.create_all_tables()
        pass
    
    @contextmanager
    def transaction(self):
        """Transaction context manager with nesting support"""
        if not hasattr(self._transaction_stack, 'level'):
            self._transaction_stack.level = 0
            self._transaction_stack.conn = None
        
        self._transaction_stack.level += 1
        
        if self._transaction_stack.level == 1:
            # Start new transaction
            with self.pool.get_connection() as conn:
                self._transaction_stack.conn = conn
                cursor = conn.cursor()
                
                try:
                    if self.config.db_type == DatabaseType.SQLITE:
                        cursor.execute("BEGIN IMMEDIATE")
                    else:
                        cursor.execute("BEGIN")
                    
                    self._monitor['transactions'] += 1
                    yield cursor
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    self._monitor['rollbacks'] += 1
                    raise
                    
                finally:
                    cursor.close()
                    self._transaction_stack.conn = None
        else:
            # Nested transaction - use savepoints
            cursor = self._transaction_stack.conn.cursor()
            savepoint = f"sp_{self._transaction_stack.level}"
            
            try:
                cursor.execute(f"SAVEPOINT {savepoint}")
                yield cursor
                cursor.execute(f"RELEASE SAVEPOINT {savepoint}")
                
            except Exception as e:
                cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                raise
                
            finally:
                cursor.close()
        
        self._transaction_stack.level -= 1
    
    def execute(self, query: str, params: Optional[Tuple] = None, 
                retry: bool = True) -> sqlite3.Cursor:
        """Execute query with retry logic and monitoring"""
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.config.max_retries if retry else 1):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    conn.commit()
                    
                    # Monitor query
                    elapsed = time.time() - start_time
                    self._monitor_query(query, elapsed)
                    
                    return cursor
                    
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    self._monitor['errors'][str(e)] = self._monitor['errors'].get(str(e), 0) + 1
                    raise
            except Exception as e:
                if HAS_POSTGRES and psycopg2 and hasattr(psycopg2, 'OperationalError') and isinstance(e, psycopg2.OperationalError):
                    last_error = e
                    if "locked" in str(e).lower() or "busy" in str(e).lower():
                        time.sleep(self.config.retry_delay * (2 ** attempt))
                    else:
                        self._monitor['errors'][str(e)] = self._monitor['errors'].get(str(e), 0) + 1
                        raise
                else:
                    self._monitor['errors'][str(e)] = self._monitor['errors'].get(str(e), 0) + 1
                    raise
        
        if last_error:
            raise last_error
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """Execute multiple queries efficiently"""
        rows_affected = 0
        
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for chunk in self._chunk_list(params_list, self.config.batch_size):
                    cursor.executemany(query, chunk)
                    rows_affected += cursor.rowcount
                conn.commit()
            finally:
                cursor.close()
        
        return rows_affected
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
        """Fetch single row as dictionary"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        
        if row:
            if self.config.db_type == DatabaseType.SQLITE:
                return dict(row)
            else:
                return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Fetch all rows as list of dictionaries"""
        cursor = self.execute(query, params)
        
        if self.config.db_type == DatabaseType.SQLITE:
            return [dict(row) for row in cursor.fetchall()]
        else:
            return [dict(zip([d[0] for d in cursor.description], row)) 
                   for row in cursor.fetchall()]
    
    def stream_results(self, query: str, params: Optional[Tuple] = None,
                      chunk_size: Optional[int] = None) -> Generator[Dict, None, None]:
        """Stream results for large datasets (memory efficient)"""
        chunk_size = chunk_size or self.config.chunk_size
        
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                
                for row in rows:
                    if self.config.db_type == DatabaseType.SQLITE:
                        yield dict(row)
                    else:
                        yield dict(zip([d[0] for d in cursor.description], row))
    
    def insert(self, table: str, data: Dict[str, Any], 
              returning: Optional[str] = None) -> Optional[Any]:
        """Insert data with optional RETURNING clause"""
        columns = list(data.keys())
        placeholders = ["?" if self.config.db_type == DatabaseType.SQLITE else "%s"] * len(columns)
        
        query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(placeholders)})"
        
        if returning:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                query += f" RETURNING {returning}"
                cursor = self.execute(query, tuple(data.values()))
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor = self.execute(query, tuple(data.values()))
                return cursor.lastrowid
        else:
            self.execute(query, tuple(data.values()))
            return None
    
    def update(self, table: str, data: Dict[str, Any], 
              where: str, where_params: Tuple) -> int:
        """Update data with WHERE clause"""
        set_clause = ", ".join([f"{k} = ?" if self.config.db_type == DatabaseType.SQLITE 
                               else f"{k} = %s" for k in data.keys()])
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params
        
        cursor = self.execute(query, params)
        return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple) -> int:
        """Delete data with WHERE clause"""
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(query, where_params)
        return cursor.rowcount
    
    def upsert(self, table: str, data: Dict[str, Any], 
              conflict_columns: List[str]) -> None:
        """Insert or update on conflict"""
        columns = list(data.keys())
        placeholders = ["?" if self.config.db_type == DatabaseType.SQLITE else "%s"] * len(columns)
        
        if self.config.db_type == DatabaseType.SQLITE:
            update_clause = ", ".join([f"{k} = excluded.{k}" for k in columns 
                                      if k not in conflict_columns])
            query = f"""
                INSERT INTO {table} ({','.join(columns)}) 
                VALUES ({','.join(placeholders)})
                ON CONFLICT ({','.join(conflict_columns)}) 
                DO UPDATE SET {update_clause}
            """
        else:
            update_clause = ", ".join([f"{k} = EXCLUDED.{k}" for k in columns 
                                      if k not in conflict_columns])
            query = f"""
                INSERT INTO {table} ({','.join(columns)}) 
                VALUES ({','.join(placeholders)})
                ON CONFLICT ({','.join(conflict_columns)}) 
                DO UPDATE SET {update_clause}
            """
        
        self.execute(query, tuple(data.values()))
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        if self.config.db_type == DatabaseType.SQLITE:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        else:
            query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema='public' AND table_name=%s
            """
        
        result = self.fetch_one(query, (table_name,))
        return result is not None
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get table column information"""
        if self.config.db_type == DatabaseType.SQLITE:
            query = f"PRAGMA table_info({table_name})"
            cursor = self.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        else:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
                ORDER BY ordinal_position
            """
            return self.fetch_all(query, (table_name,))
    
    def vacuum(self):
        """Optimize database (VACUUM)"""
        if self.config.db_type == DatabaseType.SQLITE:
            self.execute("VACUUM")
        else:
            # PostgreSQL requires autocommit mode for VACUUM
            with self.pool.get_connection() as conn:
                old_autocommit = conn.autocommit
                conn.autocommit = True
                cursor = conn.cursor()
                cursor.execute("VACUUM ANALYZE")
                conn.autocommit = old_autocommit
    
    def analyze(self):
        """Update database statistics"""
        if self.config.db_type == DatabaseType.SQLITE:
            self.execute("ANALYZE")
        else:
            self.execute("ANALYZE")
    
    def backup(self, backup_path: str):
        """Backup database"""
        if self.config.db_type == DatabaseType.SQLITE:
            import shutil
            shutil.copy2(self.config.sqlite_path, backup_path)
        else:
            # PostgreSQL backup using pg_dump
            import subprocess
            cmd = [
                'pg_dump',
                f'-h{self.config.pg_host}',
                f'-p{self.config.pg_port}',
                f'-U{self.config.pg_user}',
                f'-d{self.config.pg_database}',
                f'-f{backup_path}'
            ]
            subprocess.run(cmd, env={'PGPASSWORD': self.config.pg_password}, check=True)
    
    def get_size(self) -> int:
        """Get database size in bytes"""
        if self.config.db_type == DatabaseType.SQLITE:
            return os.path.getsize(self.config.sqlite_path)
        else:
            query = "SELECT pg_database_size(current_database())"
            result = self.fetch_one(query)
            return result['pg_database_size'] if result else 0
    
    def _monitor_query(self, query: str, elapsed: float):
        """Monitor query performance"""
        # Track query type
        query_type = query.strip().split()[0].upper()
        self._monitor['queries'][query_type] = self._monitor['queries'].get(query_type, 0) + 1
        
        # Track slow queries
        if elapsed > 1.0:
            self._monitor['slow_queries'].append({
                'query': query[:100],
                'elapsed': elapsed,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 100 slow queries
            if len(self._monitor['slow_queries']) > 100:
                self._monitor['slow_queries'] = self._monitor['slow_queries'][-100:]
    
    def _chunk_list(self, items: List, chunk_size: int) -> Generator[List, None, None]:
        """Split list into chunks"""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'database_type': self.config.db_type.value,
            'database_size': self.get_size(),
            'pool_stats': self.pool.get_stats(),
            'monitor': dict(self._monitor),
            'uptime': time.time() - self._monitor['start_time']
        }
        
        # Add table statistics
        if self.config.db_type == DatabaseType.SQLITE:
            tables = self.fetch_all(
                "SELECT name, sql FROM sqlite_master WHERE type='table'"
            )
            stats['tables'] = {}
            for table in tables:
                count = self.fetch_one(f"SELECT COUNT(*) as cnt FROM {table['name']}")
                stats['tables'][table['name']] = count['cnt'] if count else 0
        else:
            tables = self.fetch_all("""
                SELECT table_name, pg_relation_size(quote_ident(table_name)) as size
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            stats['tables'] = {t['table_name']: t['size'] for t in tables}
        
        return stats
    
    def close(self):
        """Close database connections"""
        self.pool.close_all()
        logger.info("Database connections closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    # Compatibility methods for existing code
    def cursor(self):
        """Get cursor (compatibility method)"""
        class CursorWrapper:
            def __init__(self, db):
                self.db = db
                self._conn = None
                self._cursor = None
            
            def __enter__(self):
                self._conn = self.db.pool.get_connection().__enter__()
                self._cursor = self._conn.cursor()
                return self._cursor
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self._cursor:
                    self._cursor.close()
                if self._conn:
                    self._conn.__exit__(exc_type, exc_val, exc_tb)
        
        return CursorWrapper(self)
    
    def commit(self):
        """Commit (compatibility method)"""
        pass  # Auto-commit handled in execute
    
    def rollback(self):
        """Rollback (compatibility method)"""
        self._monitor['rollbacks'] += 1