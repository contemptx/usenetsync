"""Data management system for UsenetSync."""

import asyncio
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import aiofiles
import json

class SecureDeleteMethod(Enum):
    """Secure file deletion methods."""
    SIMPLE = "simple"  # Regular delete
    ZERO_OVERWRITE = "zero"  # Overwrite with zeros
    RANDOM_OVERWRITE = "random"  # Overwrite with random data
    DOD_3PASS = "dod_3pass"  # DoD 3-pass overwrite
    DOD_7PASS = "dod_7pass"  # DoD 7-pass overwrite
    GUTMANN = "gutmann"  # Gutmann 35-pass

@dataclass
class StorageQuota:
    """Storage quota configuration."""
    user_id: str
    max_storage_bytes: int
    max_files: int
    max_share_size: int
    current_usage_bytes: int
    current_file_count: int
    warning_threshold: float = 0.8
    
@dataclass
class CacheEntry:
    """Cache entry metadata."""
    key: str
    size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int] = None

class DataManager:
    """Comprehensive data management system."""
    
    def __init__(self, db_manager, cache_dir: Path = None, temp_dir: Path = None):
        self.db = db_manager
        self.cache_dir = cache_dir or Path.home() / ".usenetsync" / "cache"
        self.temp_dir = temp_dir or Path("/tmp/usenetsync")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata
        self.cache_metadata: Dict[str, CacheEntry] = {}
        self.max_cache_size = 500 * 1024 * 1024  # 500 MB default
        
        # Quota management
        self.quotas: Dict[str, StorageQuota] = {}
        
    async def initialize(self):
        """Initialize data management system."""
        await self._create_tables()
        await self._load_cache_metadata()
        await self._load_quotas()
        
    async def _create_tables(self):
        """Create necessary database tables."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS storage_quotas (
                user_id TEXT PRIMARY KEY,
                max_storage_bytes INTEGER,
                max_files INTEGER,
                max_share_size INTEGER,
                current_usage_bytes INTEGER DEFAULT 0,
                current_file_count INTEGER DEFAULT 0,
                warning_threshold REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                size INTEGER,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                ttl_seconds INTEGER,
                file_path TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cleanup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cleanup_type TEXT,
                items_removed INTEGER,
                space_freed INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT,
                details TEXT
            )
            """
        ]
        
        for query in queries:
            await self.db.execute(query)
            
    # ==================== Database Cleanup ====================
    
    async def cleanup_database(
        self,
        older_than_days: int = 30,
        cleanup_orphans: bool = True,
        vacuum: bool = True,
        analyze: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive database cleanup.
        
        Args:
            older_than_days: Remove data older than this many days
            cleanup_orphans: Remove orphaned records
            vacuum: Run VACUUM to reclaim space
            analyze: Run ANALYZE to update statistics
            
        Returns:
            Cleanup statistics
        """
        start_time = datetime.now()
        stats = {
            'started_at': start_time,
            'removed_records': {},
            'space_before': await self._get_database_size(),
            'errors': []
        }
        
        try:
            # Remove old logs
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            # Clean old logs
            result = await self.db.execute(
                "DELETE FROM logs WHERE timestamp < ?",
                (cutoff_date,)
            )
            stats['removed_records']['logs'] = result.rowcount if hasattr(result, 'rowcount') else 0
            
            # Clean old shares
            result = await self.db.execute(
                "DELETE FROM shares WHERE expires_at < ? AND expires_at IS NOT NULL",
                (datetime.now(),)
            )
            stats['removed_records']['expired_shares'] = result.rowcount if hasattr(result, 'rowcount') else 0
            
            # Clean old file versions (keep latest 5 per file)
            await self._cleanup_old_versions()
            
            # Clean orphaned records
            if cleanup_orphans:
                stats['removed_records']['orphans'] = await self._cleanup_orphans()
            
            # Clean failed uploads/downloads
            result = await self.db.execute(
                "DELETE FROM uploads WHERE status = 'failed' AND created_at < ?",
                (cutoff_date,)
            )
            stats['removed_records']['failed_uploads'] = result.rowcount if hasattr(result, 'rowcount') else 0
            
            # Vacuum database
            if vacuum:
                await self.db.execute("VACUUM")
                stats['vacuum_completed'] = True
            
            # Analyze database
            if analyze:
                await self.db.execute("ANALYZE")
                stats['analyze_completed'] = True
            
            stats['space_after'] = await self._get_database_size()
            stats['space_freed'] = stats['space_before'] - stats['space_after']
            stats['completed_at'] = datetime.now()
            stats['duration'] = (stats['completed_at'] - start_time).total_seconds()
            
            # Log cleanup history
            await self._log_cleanup_history('database', stats)
            
        except Exception as e:
            stats['errors'].append(str(e))
            
        return stats
    
    async def _cleanup_old_versions(self):
        """Keep only the latest N versions of each file."""
        query = """
            DELETE FROM file_versions
            WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY file_hash ORDER BY version_number DESC
                    ) as rn
                    FROM file_versions
                ) WHERE rn <= 5
            )
        """
        await self.db.execute(query)
    
    async def _cleanup_orphans(self) -> int:
        """Remove orphaned database records."""
        count = 0
        
        # Remove file records without corresponding data
        result = await self.db.execute("""
            DELETE FROM files 
            WHERE id NOT IN (SELECT file_id FROM file_data)
        """)
        count += result.rowcount if hasattr(result, 'rowcount') else 0
        
        # Remove share items without shares
        result = await self.db.execute("""
            DELETE FROM share_items 
            WHERE share_id NOT IN (SELECT id FROM shares)
        """)
        count += result.rowcount if hasattr(result, 'rowcount') else 0
        
        return count
    
    # ==================== Cache Management ====================
    
    async def cache_get(self, key: str) -> Optional[bytes]:
        """Get item from cache."""
        if key not in self.cache_metadata:
            return None
            
        entry = self.cache_metadata[key]
        
        # Check TTL
        if entry.ttl_seconds:
            age = (datetime.now() - entry.created_at).total_seconds()
            if age > entry.ttl_seconds:
                await self.cache_delete(key)
                return None
        
        # Update access metadata
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        await self._update_cache_metadata(entry)
        
        # Read from file
        cache_file = self.cache_dir / key
        if cache_file.exists():
            async with aiofiles.open(cache_file, 'rb') as f:
                return await f.read()
        
        return None
    
    async def cache_set(
        self,
        key: str,
        data: bytes,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Store item in cache."""
        try:
            # Check cache size limit
            if await self._get_cache_size() + len(data) > self.max_cache_size:
                await self._evict_cache_entries(len(data))
            
            # Write to file
            cache_file = self.cache_dir / key
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(data)
            
            # Update metadata
            entry = CacheEntry(
                key=key,
                size=len(data),
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                ttl_seconds=ttl_seconds
            )
            
            self.cache_metadata[key] = entry
            await self._save_cache_metadata(entry)
            
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def cache_delete(self, key: str) -> bool:
        """Delete item from cache."""
        try:
            cache_file = self.cache_dir / key
            if cache_file.exists():
                cache_file.unlink()
            
            if key in self.cache_metadata:
                del self.cache_metadata[key]
                await self.db.execute(
                    "DELETE FROM cache_metadata WHERE key = ?",
                    (key,)
                )
            
            return True
            
        except Exception:
            return False
    
    async def clear_cache(
        self,
        older_than_days: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clear cache with optional filters."""
        stats = {
            'removed_items': 0,
            'space_freed': 0
        }
        
        keys_to_remove = []
        
        for key, entry in self.cache_metadata.items():
            should_remove = False
            
            # Check age
            if older_than_days:
                age_days = (datetime.now() - entry.created_at).days
                if age_days > older_than_days:
                    should_remove = True
            
            # Check pattern
            if pattern and pattern in key:
                should_remove = True
            
            if should_remove:
                keys_to_remove.append(key)
                stats['space_freed'] += entry.size
        
        # Remove items
        for key in keys_to_remove:
            await self.cache_delete(key)
            stats['removed_items'] += 1
        
        return stats
    
    async def _evict_cache_entries(self, needed_space: int):
        """Evict cache entries using LRU strategy."""
        # Sort by last accessed time
        sorted_entries = sorted(
            self.cache_metadata.values(),
            key=lambda x: x.last_accessed
        )
        
        freed_space = 0
        for entry in sorted_entries:
            if freed_space >= needed_space:
                break
            
            freed_space += entry.size
            await self.cache_delete(entry.key)
    
    # ==================== Quota Management ====================
    
    async def set_quota(
        self,
        user_id: str,
        max_storage_gb: float,
        max_files: int,
        max_share_size_gb: float
    ) -> StorageQuota:
        """Set storage quota for a user."""
        quota = StorageQuota(
            user_id=user_id,
            max_storage_bytes=int(max_storage_gb * 1024 * 1024 * 1024),
            max_files=max_files,
            max_share_size=int(max_share_size_gb * 1024 * 1024 * 1024),
            current_usage_bytes=0,
            current_file_count=0
        )
        
        await self.db.execute("""
            INSERT OR REPLACE INTO storage_quotas
            (user_id, max_storage_bytes, max_files, max_share_size)
            VALUES (?, ?, ?, ?)
        """, (user_id, quota.max_storage_bytes, quota.max_files, quota.max_share_size))
        
        self.quotas[user_id] = quota
        return quota
    
    async def check_quota(
        self,
        user_id: str,
        additional_bytes: int = 0,
        additional_files: int = 0
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has available quota.
        
        Returns:
            (allowed, reason_if_denied)
        """
        if user_id not in self.quotas:
            return True, None  # No quota set
        
        quota = self.quotas[user_id]
        
        # Check storage limit
        if quota.current_usage_bytes + additional_bytes > quota.max_storage_bytes:
            return False, f"Storage quota exceeded (limit: {quota.max_storage_bytes / (1024**3):.2f} GB)"
        
        # Check file count limit
        if quota.current_file_count + additional_files > quota.max_files:
            return False, f"File count quota exceeded (limit: {quota.max_files} files)"
        
        # Check if approaching limit
        usage_ratio = (quota.current_usage_bytes + additional_bytes) / quota.max_storage_bytes
        if usage_ratio > quota.warning_threshold:
            print(f"Warning: User {user_id} at {usage_ratio*100:.1f}% of storage quota")
        
        return True, None
    
    async def update_quota_usage(
        self,
        user_id: str,
        bytes_delta: int,
        files_delta: int
    ):
        """Update quota usage for a user."""
        if user_id not in self.quotas:
            return
        
        quota = self.quotas[user_id]
        quota.current_usage_bytes = max(0, quota.current_usage_bytes + bytes_delta)
        quota.current_file_count = max(0, quota.current_file_count + files_delta)
        
        await self.db.execute("""
            UPDATE storage_quotas
            SET current_usage_bytes = ?, current_file_count = ?, updated_at = ?
            WHERE user_id = ?
        """, (quota.current_usage_bytes, quota.current_file_count, datetime.now(), user_id))
    
    # ==================== Secure Delete ====================
    
    async def secure_delete(
        self,
        file_path: Path,
        method: SecureDeleteMethod = SecureDeleteMethod.ZERO_OVERWRITE
    ) -> bool:
        """
        Securely delete a file.
        
        Args:
            file_path: Path to file to delete
            method: Deletion method to use
            
        Returns:
            Success status
        """
        if not file_path.exists():
            return False
        
        try:
            file_size = file_path.stat().st_size
            
            if method == SecureDeleteMethod.SIMPLE:
                file_path.unlink()
                
            elif method == SecureDeleteMethod.ZERO_OVERWRITE:
                await self._overwrite_file(file_path, b'\x00' * 4096, 1)
                file_path.unlink()
                
            elif method == SecureDeleteMethod.RANDOM_OVERWRITE:
                await self._overwrite_file(file_path, None, 1)  # Random data
                file_path.unlink()
                
            elif method == SecureDeleteMethod.DOD_3PASS:
                # DoD 5220.22-M (3 passes)
                await self._overwrite_file(file_path, b'\x00' * 4096, 1)
                await self._overwrite_file(file_path, b'\xFF' * 4096, 1)
                await self._overwrite_file(file_path, None, 1)  # Random
                file_path.unlink()
                
            elif method == SecureDeleteMethod.DOD_7PASS:
                # DoD 5220.22-M (7 passes)
                for pattern in [b'\x00', b'\xFF', b'\x00', b'\xFF', b'\x00', b'\xFF', None]:
                    if pattern is None:
                        await self._overwrite_file(file_path, None, 1)
                    else:
                        await self._overwrite_file(file_path, pattern * 4096, 1)
                file_path.unlink()
                
            elif method == SecureDeleteMethod.GUTMANN:
                # Gutmann method (35 passes) - simplified version
                for _ in range(35):
                    await self._overwrite_file(file_path, None, 1)
                file_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Secure delete failed: {e}")
            return False
    
    async def _overwrite_file(
        self,
        file_path: Path,
        pattern: Optional[bytes],
        passes: int
    ):
        """Overwrite file with pattern."""
        file_size = file_path.stat().st_size
        
        for _ in range(passes):
            async with aiofiles.open(file_path, 'r+b') as f:
                position = 0
                while position < file_size:
                    if pattern is None:
                        # Random data
                        chunk = os.urandom(min(4096, file_size - position))
                    else:
                        chunk = pattern[:min(len(pattern), file_size - position)]
                    
                    await f.seek(position)
                    await f.write(chunk)
                    position += len(chunk)
                
                await f.flush()
                os.fsync(f.fileno())
    
    # ==================== Temporary Files ====================
    
    async def cleanup_temp_files(self, older_than_hours: int = 24) -> Dict[str, Any]:
        """Clean up temporary files."""
        stats = {
            'removed_files': 0,
            'space_freed': 0
        }
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        for temp_file in self.temp_dir.iterdir():
            if temp_file.is_file():
                if datetime.fromtimestamp(temp_file.stat().st_mtime) < cutoff_time:
                    stats['space_freed'] += temp_file.stat().st_size
                    temp_file.unlink()
                    stats['removed_files'] += 1
        
        return stats
    
    # ==================== Helper Methods ====================
    
    async def _get_database_size(self) -> int:
        """Get database file size."""
        # This would need to be adapted based on your database location
        db_path = Path("usenetsync.db")  # Adjust path
        if db_path.exists():
            return db_path.stat().st_size
        return 0
    
    async def _get_cache_size(self) -> int:
        """Get total cache size."""
        return sum(entry.size for entry in self.cache_metadata.values())
    
    async def _load_cache_metadata(self):
        """Load cache metadata from database."""
        rows = await self.db.fetch_all("SELECT * FROM cache_metadata")
        for row in rows:
            self.cache_metadata[row['key']] = CacheEntry(
                key=row['key'],
                size=row['size'],
                created_at=row['created_at'],
                last_accessed=row['last_accessed'],
                access_count=row['access_count'],
                ttl_seconds=row['ttl_seconds']
            )
    
    async def _save_cache_metadata(self, entry: CacheEntry):
        """Save cache metadata to database."""
        await self.db.execute("""
            INSERT OR REPLACE INTO cache_metadata
            (key, size, created_at, last_accessed, access_count, ttl_seconds, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.key, entry.size, entry.created_at,
            entry.last_accessed, entry.access_count,
            entry.ttl_seconds, str(self.cache_dir / entry.key)
        ))
    
    async def _update_cache_metadata(self, entry: CacheEntry):
        """Update cache metadata in database."""
        await self.db.execute("""
            UPDATE cache_metadata
            SET last_accessed = ?, access_count = ?
            WHERE key = ?
        """, (entry.last_accessed, entry.access_count, entry.key))
    
    async def _load_quotas(self):
        """Load quotas from database."""
        rows = await self.db.fetch_all("SELECT * FROM storage_quotas")
        for row in rows:
            self.quotas[row['user_id']] = StorageQuota(
                user_id=row['user_id'],
                max_storage_bytes=row['max_storage_bytes'],
                max_files=row['max_files'],
                max_share_size=row['max_share_size'],
                current_usage_bytes=row['current_usage_bytes'],
                current_file_count=row['current_file_count'],
                warning_threshold=row['warning_threshold']
            )
    
    async def _log_cleanup_history(self, cleanup_type: str, stats: Dict[str, Any]):
        """Log cleanup operation to history."""
        await self.db.execute("""
            INSERT INTO cleanup_history
            (cleanup_type, items_removed, space_freed, started_at, completed_at, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cleanup_type,
            sum(stats.get('removed_records', {}).values()),
            stats.get('space_freed', 0),
            stats.get('started_at'),
            stats.get('completed_at'),
            'success' if not stats.get('errors') else 'partial',
            json.dumps(stats)
        ))
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        return {
            'database_size': await self._get_database_size(),
            'cache_size': await self._get_cache_size(),
            'temp_size': sum(f.stat().st_size for f in self.temp_dir.iterdir() if f.is_file()),
            'cache_entries': len(self.cache_metadata),
            'quotas': {
                user_id: {
                    'used': quota.current_usage_bytes,
                    'total': quota.max_storage_bytes,
                    'percentage': (quota.current_usage_bytes / quota.max_storage_bytes * 100) if quota.max_storage_bytes > 0 else 0,
                    'files': quota.current_file_count,
                    'max_files': quota.max_files
                }
                for user_id, quota in self.quotas.items()
            }
        }