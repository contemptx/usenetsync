"""
Cache Management System for UsenetSync
Implements LRU cache with TTL support for improved performance
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import pickle
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata"""
    key: str
    value: Any
    size: int
    created_at: float
    accessed_at: float
    access_count: int
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """Update access time and count"""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory = 0
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0
        }
        
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of a value in bytes"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value).encode())
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if entry.is_expired():
                    self._remove(key)
                    self.stats['expired'] += 1
                    self.stats['misses'] += 1
                    return default
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.update_access()
                self.stats['hits'] += 1
                return entry.value
            
            self.stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successfully cached
        """
        with self.lock:
            size = self._calculate_size(value)
            
            # Check if value is too large
            if size > self.max_memory_bytes:
                logger.warning(f"Value too large for cache: {size} bytes")
                return False
            
            # Remove existing entry if present
            if key in self.cache:
                self._remove(key)
            
            # Evict entries if necessary
            while self._needs_eviction(size):
                self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=0,
                ttl=ttl
            )
            
            self.cache[key] = entry
            self.current_memory += size
            return True
    
    def _needs_eviction(self, additional_size: int) -> bool:
        """Check if eviction is needed"""
        return (len(self.cache) >= self.max_size or 
                self.current_memory + additional_size > self.max_memory_bytes)
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.current_memory -= entry.size
            self.stats['evictions'] += 1
            logger.debug(f"Evicted cache entry: {key}")
    
    def _remove(self, key: str):
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.current_memory -= entry.size
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted
        """
        with self.lock:
            if key in self.cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.current_memory = 0
            logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove(key)
                self.stats['expired'] += 1
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self.cache),
                'memory_used_mb': self.current_memory / (1024 * 1024),
                'memory_limit_mb': self.max_memory_bytes / (1024 * 1024),
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': f"{hit_rate:.1f}%",
                'evictions': self.stats['evictions'],
                'expired': self.stats['expired']
            }


class CacheManager:
    """Manages multiple cache instances for different data types"""
    
    def __init__(self):
        """Initialize cache manager with different cache types"""
        self.caches = {
            'files': LRUCache(max_size=500, max_memory_mb=200),
            'shares': LRUCache(max_size=1000, max_memory_mb=50),
            'metadata': LRUCache(max_size=2000, max_memory_mb=20),
            'thumbnails': LRUCache(max_size=100, max_memory_mb=100),
            'search': LRUCache(max_size=100, max_memory_mb=10),
            'api': LRUCache(max_size=200, max_memory_mb=20)
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for cleaning expired entries"""
        def cleanup_worker():
            while True:
                time.sleep(300)  # Run every 5 minutes
                for cache in self.caches.values():
                    cache.cleanup_expired()
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    def get_cache(self, cache_type: str) -> Optional[LRUCache]:
        """Get specific cache instance"""
        return self.caches.get(cache_type)
    
    def cache_file(self, file_path: str, content: bytes, ttl: float = 3600) -> bool:
        """Cache file content"""
        cache = self.caches['files']
        key = self._generate_key('file', file_path)
        return cache.set(key, content, ttl)
    
    def get_cached_file(self, file_path: str) -> Optional[bytes]:
        """Get cached file content"""
        cache = self.caches['files']
        key = self._generate_key('file', file_path)
        return cache.get(key)
    
    def cache_share(self, share_id: str, data: Dict, ttl: float = 7200) -> bool:
        """Cache share data"""
        cache = self.caches['shares']
        return cache.set(share_id, data, ttl)
    
    def get_cached_share(self, share_id: str) -> Optional[Dict]:
        """Get cached share data"""
        cache = self.caches['shares']
        return cache.get(share_id)
    
    def cache_search_results(self, query: str, results: list, ttl: float = 600) -> bool:
        """Cache search results"""
        cache = self.caches['search']
        key = self._generate_key('search', query)
        return cache.set(key, results, ttl)
    
    def get_cached_search(self, query: str) -> Optional[list]:
        """Get cached search results"""
        cache = self.caches['search']
        key = self._generate_key('search', query)
        return cache.get(key)
    
    def cache_api_response(self, endpoint: str, params: Dict, response: Any, ttl: float = 300) -> bool:
        """Cache API response"""
        cache = self.caches['api']
        key = self._generate_key('api', endpoint, json.dumps(params, sort_keys=True))
        return cache.set(key, response, ttl)
    
    def get_cached_api_response(self, endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached API response"""
        cache = self.caches['api']
        key = self._generate_key('api', endpoint, json.dumps(params, sort_keys=True))
        return cache.get(key)
    
    def _generate_key(self, *args) -> str:
        """Generate cache key from arguments"""
        combined = '|'.join(str(arg) for arg in args)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache entries matching pattern"""
        for cache_type, cache in self.caches.items():
            with cache.lock:
                keys_to_delete = [
                    key for key in cache.cache.keys() 
                    if pattern in key
                ]
                for key in keys_to_delete:
                    cache.delete(key)
                
                if keys_to_delete:
                    logger.info(f"Invalidated {len(keys_to_delete)} entries in {cache_type}")
    
    def clear_all(self):
        """Clear all caches"""
        for cache in self.caches.values():
            cache.clear()
        logger.info("All caches cleared")
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all caches"""
        stats = {}
        for name, cache in self.caches.items():
            stats[name] = cache.get_stats()
        
        # Calculate totals
        total_entries = sum(s['entries'] for s in stats.values())
        total_memory = sum(s['memory_used_mb'] for s in stats.values())
        total_hits = sum(s['hits'] for s in stats.values())
        total_misses = sum(s['misses'] for s in stats.values())
        
        stats['total'] = {
            'entries': total_entries,
            'memory_used_mb': total_memory,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'overall_hit_rate': f"{(total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0:.1f}%"
        }
        
        return stats


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager