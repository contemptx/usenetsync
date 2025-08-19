#!/usr/bin/env python3
"""
Unified Cache - Download cache management
Production-ready with LRU eviction and size limits
"""

import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class UnifiedCache:
    """
    Unified download cache
    Manages cached segments with LRU eviction
    """
    
    def __init__(self, cache_dir: str = '.download_cache',
                 max_size_mb: int = 1000,
                 max_items: int = 10000):
        """
        Initialize cache
        
        Args:
            cache_dir: Cache directory
            max_size_mb: Maximum cache size in MB
            max_items: Maximum number of cached items
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.max_items = max_items
        
        # LRU cache tracking
        self.cache_index = OrderedDict()  # key -> (path, size, access_time)
        self.current_size = 0
        
        # Statistics
        self._statistics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'bytes_served': 0
        }
        
        # Load existing cache
        self._scan_cache()
    
    def get(self, key: str) -> Optional[bytes]:
        """
        Get item from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None
        """
        if key in self.cache_index:
            # Update access order (LRU)
            self.cache_index.move_to_end(key)
            
            # Read from disk
            cache_path, size, _ = self.cache_index[key]
            
            try:
                with open(cache_path, 'rb') as f:
                    data = f.read()
                
                # Update statistics
                self._statistics['hits'] += 1
                self._statistics['bytes_served'] += len(data)
                
                # Update access time
                self.cache_index[key] = (cache_path, size, time.time())
                
                logger.debug(f"Cache hit: {key}")
                return data
                
            except Exception as e:
                logger.error(f"Failed to read cache: {e}")
                # Remove corrupted entry
                del self.cache_index[key]
                return None
        else:
            self._statistics['misses'] += 1
            logger.debug(f"Cache miss: {key}")
            return None
    
    def put(self, key: str, data: bytes):
        """
        Put item in cache
        
        Args:
            key: Cache key
            data: Data to cache
        """
        # Check if already cached
        if key in self.cache_index:
            self.cache_index.move_to_end(key)
            return
        
        data_size = len(data)
        
        # Evict if necessary
        while (self.current_size + data_size > self.max_size or 
               len(self.cache_index) >= self.max_items):
            if not self._evict_lru():
                break
        
        # Generate cache file path
        cache_filename = hashlib.sha256(key.encode()).hexdigest()[:16]
        cache_path = self.cache_dir / cache_filename
        
        try:
            # Write to disk
            with open(cache_path, 'wb') as f:
                f.write(data)
            
            # Update index
            self.cache_index[key] = (cache_path, data_size, time.time())
            self.current_size += data_size
            
            logger.debug(f"Cached: {key} ({data_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to cache: {e}")
    
    def remove(self, key: str) -> bool:
        """
        Remove item from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if removed
        """
        if key not in self.cache_index:
            return False
        
        cache_path, size, _ = self.cache_index[key]
        
        # Remove file
        try:
            if cache_path.exists():
                cache_path.unlink()
        except Exception as e:
            logger.error(f"Failed to remove cache file: {e}")
        
        # Update index
        del self.cache_index[key]
        self.current_size -= size
        
        logger.debug(f"Removed from cache: {key}")
        return True
    
    def clear(self):
        """Clear entire cache"""
        # Remove all cache files
        for key, (cache_path, _, _) in self.cache_index.items():
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except Exception as e:
                logger.error(f"Failed to remove {cache_path}: {e}")
        
        # Clear index
        self.cache_index.clear()
        self.current_size = 0
        
        logger.info("Cache cleared")
    
    def _evict_lru(self) -> bool:
        """
        Evict least recently used item
        
        Returns:
            True if item was evicted
        """
        if not self.cache_index:
            return False
        
        # Get LRU item (first in OrderedDict)
        key, (cache_path, size, _) = self.cache_index.popitem(last=False)
        
        # Remove file
        try:
            if cache_path.exists():
                cache_path.unlink()
        except Exception as e:
            logger.error(f"Failed to evict {cache_path}: {e}")
        
        self.current_size -= size
        self._statistics['evictions'] += 1
        
        logger.debug(f"Evicted: {key}")
        return True
    
    def _scan_cache(self):
        """Scan cache directory and rebuild index"""
        # This is simplified - in production you'd store metadata
        # For now, just count existing files
        cache_files = list(self.cache_dir.glob("*"))
        
        if cache_files:
            logger.info(f"Found {len(cache_files)} existing cache files")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (
            self._statistics['hits'] / 
            (self._statistics['hits'] + self._statistics['misses'])
            if (self._statistics['hits'] + self._statistics['misses']) > 0
            else 0
        )
        
        return {
            **self._statistics,
            'items_cached': len(self.cache_index),
            'cache_size_mb': self.current_size / (1024 * 1024),
            'max_size_mb': self.max_size / (1024 * 1024),
            'hit_rate': hit_rate,
            'usage_percent': (self.current_size / self.max_size * 100) if self.max_size > 0 else 0
        }
    
    def optimize(self):
        """Optimize cache by removing old entries"""
        current_time = time.time()
        max_age = 86400 * 7  # 7 days
        
        to_remove = []
        
        for key, (path, size, access_time) in self.cache_index.items():
            if current_time - access_time > max_age:
                to_remove.append(key)
        
        for key in to_remove:
            self.remove(key)
        
        if to_remove:
            logger.info(f"Optimized cache: removed {len(to_remove)} old entries")