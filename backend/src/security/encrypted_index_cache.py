#!/usr/bin/env python3
"""
Fixed Enhanced Encrypted Index Cache for UsenetSync
Compatible with your EnhancedDatabaseManager connection pool pattern
Transaction-safe initialization
"""

import os
import json
import zlib
import hashlib
import sqlite3
import time
import logging
import base64
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
from collections import OrderedDict
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Cryptography library not available - cache will be disabled")

logger = logging.getLogger(__name__)

class EnhancedEncryptedIndexCache:
    """
    Enhanced encrypted cache compatible with EnhancedDatabaseManager
    Uses connection pool pattern for database operations
    Transaction-safe initialization
    """
    
    def __init__(self, db_manager):
        """
        Initialize enhanced cache with memory optimization
        
        Args:
            db_manager: The EnhancedDatabaseManager instance
        """
        self.db = db_manager
        self.logger = logging.getLogger(f"{__name__}.EnhancedEncryptedIndexCache")
        self.enabled = CRYPTO_AVAILABLE
        
        if not self.enabled:
            self.logger.warning("Cache disabled - cryptography library not available")
            return
        
        # Memory cache for hot data (LRU with 100 entries max)
        self.memory_cache = OrderedDict()
        self.max_memory_entries = 100
        
        # Performance statistics
        self.stats = {
            'memory_hits': 0,
            'memory_misses': 0, 
            'db_hits': 0,
            'db_misses': 0,
            'total_requests': 0,
            'memory_evictions': 0,
            'cache_stores': 0,
            'cleanup_runs': 0,
            'last_cleanup': None
        }
        
        # Initialize database tables with optimizations
        self._init_cache_tables_optimized()
    
    def _init_cache_tables_optimized(self):
        """Initialize cache tables optimized for millions of entries - transaction safe"""
        if not self.enabled:
            return
            
        try:
            # Use the connection pool pattern from your database manager
            with self.db.pool.get_connection() as conn:
                # Main cache table optimized for scale
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS index_cache (
                        cache_key TEXT PRIMARY KEY,
                        folder_id TEXT NOT NULL,
                        share_type TEXT NOT NULL,
                        encrypted_data BLOB NOT NULL,
                        iv BLOB NOT NULL,
                        file_count INTEGER NOT NULL,
                        total_size INTEGER NOT NULL,
                        compressed_size INTEGER NOT NULL,
                        created_at INTEGER NOT NULL,
                        last_accessed INTEGER NOT NULL,
                        access_count INTEGER DEFAULT 0
                    )
                """)
                
                # Optimized indexes for large datasets
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_folder_type 
                    ON index_cache(folder_id, share_type)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_accessed_size 
                    ON index_cache(last_accessed DESC, compressed_size)
                """)
                
                # Cache statistics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        total_size INTEGER DEFAULT 0,
                        total_entries INTEGER DEFAULT 0,
                        total_hits INTEGER DEFAULT 0,
                        total_misses INTEGER DEFAULT 0,
                        memory_hits INTEGER DEFAULT 0,
                        memory_misses INTEGER DEFAULT 0,
                        last_cleanup TIMESTAMP,
                        largest_entry INTEGER DEFAULT 0,
                        avg_entry_size INTEGER DEFAULT 0
                    )
                """)
                
                # Initialize stats if not exists
                conn.execute("""
                    INSERT OR IGNORE INTO cache_stats (id, total_size, total_entries) 
                    VALUES (1, 0, 0)
                """)
                
                conn.commit()
            
            # Set PRAGMA settings in a separate connection to avoid transaction conflicts
            try:
                with self.db.pool.get_connection() as conn:
                    # These should be safe to set
                    conn.execute("PRAGMA temp_store = MEMORY")
                    conn.commit()
                    
            except Exception as pragma_error:
                # Non-critical if PRAGMA settings fail
                self.logger.debug(f"PRAGMA settings warning: {pragma_error}")
                
            self.logger.info("Enhanced cache tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced cache: {e}")
            self.enabled = False
    
    def generate_cache_key(self, folder_id: str, share_type: str, 
                          user_id: Optional[str] = None,
                          password_hash: Optional[str] = None) -> str:
        """Generate unique cache key based on share type"""
        if share_type == 'public':
            cache_key = f"public:{folder_id}"
        elif share_type == 'private' and user_id:
            user_hash = hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:16]
            cache_key = f"private:{folder_id}:{user_hash}"
        elif share_type == 'protected' and password_hash:
            cache_key = f"protected:{folder_id}:{password_hash[:16]}"
        else:
            cache_key = f"{share_type}:{folder_id}"
        
        return cache_key
    
    def store(self, folder_id: str, index_data: Dict, cache_key: str,
              share_type: str, encryption_key: bytes) -> bool:
        """Store parsed index data with memory + SQLite caching"""
        if not self.enabled:
            return False
            
        try:
            start_time = time.time()
            
            # Prepare data for caching
            cache_data = {
                'folder_id': folder_id,
                'name': index_data.get('name', ''),
                'files': index_data.get('files', []),
                'total_size': index_data.get('total_size', 0),
                'total_files': index_data.get('total_files', len(index_data.get('files', []))),
                'binary_index': index_data.get('binary_index', ''),
                'segments': index_data.get('segments', {}),
                'version': index_data.get('version', '3.0'),
                'created_at': datetime.now().isoformat(),
                'cached_at': datetime.now().isoformat()
            }
            
            # Serialize and compress
            json_data = json.dumps(cache_data, separators=(',', ':'))
            compressed = zlib.compress(json_data.encode('utf-8'), level=9)
            
            # Derive cache-specific encryption key
            cache_encryption_key = self._derive_cache_encryption_key(encryption_key)
            
            # Encrypt
            iv = os.urandom(16)
            encrypted = self._encrypt_data(compressed, cache_encryption_key, iv)
            
            current_time = int(time.time())
            
            # Store in SQLite using connection pool
            with self.db.pool.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO index_cache
                    (cache_key, folder_id, share_type, encrypted_data, iv, 
                     file_count, total_size, compressed_size, created_at, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key,
                    folder_id,
                    share_type,
                    encrypted,
                    iv,
                    cache_data['total_files'],
                    cache_data['total_size'],
                    len(encrypted),
                    current_time,
                    current_time
                ))
                conn.commit()
            
            # Add to memory cache
            self._add_to_memory_cache(cache_key, cache_data)
            
            # Update statistics
            self._update_cache_stats(len(encrypted), True)
            self.stats['cache_stores'] += 1
            
            elapsed = time.time() - start_time
            
            self.logger.info(
                f"Enhanced cache store: {folder_id} ({share_type}) - "
                f"{cache_data['total_files']:,} files, "
                f"{len(encrypted)/1024:.1f} KB, {elapsed*1000:.1f}ms"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Enhanced cache store failed for {folder_id}: {e}")
            return False
    
    def get(self, cache_key: str, encryption_key: bytes) -> Optional[Dict]:
        """Retrieve cached index data with memory-first lookup"""
        if not self.enabled:
            self._record_cache_miss()
            return None
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # Layer 1: Check memory cache first (fastest - ~0.001ms)
            if cache_key in self.memory_cache:
                # Move to end (LRU update)
                self.memory_cache.move_to_end(cache_key)
                data = self.memory_cache[cache_key]
                
                self.stats['memory_hits'] += 1
                self._record_cache_hit()
                
                elapsed = time.time() - start_time
                self.logger.debug(f"Memory cache HIT: {cache_key[:20]}... ({elapsed*1000:.2f}ms)")
                
                return data
            
            self.stats['memory_misses'] += 1
            
            # Layer 2: Check SQLite database using connection pool
            with self.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT encrypted_data, iv, file_count, total_size, folder_id, share_type
                    FROM index_cache
                    WHERE cache_key = ?
                """, (cache_key,))
                
                result = cursor.fetchone()
                
                if not result:
                    self._record_cache_miss()
                    elapsed = time.time() - start_time
                    self.logger.debug(f"Cache MISS: {cache_key[:20]}... ({elapsed*1000:.2f}ms)")
                    return None
                
                encrypted_data, iv, file_count, total_size, folder_id, share_type = result
                
                # Update access statistics in database
                current_time = int(time.time())
                conn.execute("""
                    UPDATE index_cache
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE cache_key = ?
                """, (current_time, cache_key))
                conn.commit()
            
            # Decrypt
            cache_encryption_key = self._derive_cache_encryption_key(encryption_key)
            decrypted = self._decrypt_data(encrypted_data, cache_encryption_key, iv)
            
            # Decompress and parse
            decompressed = zlib.decompress(decrypted)
            cache_data = json.loads(decompressed.decode('utf-8'))
            
            # Promote to memory cache
            self._add_to_memory_cache(cache_key, cache_data)
            
            self.stats['db_hits'] += 1
            self._record_cache_hit()
            
            elapsed = time.time() - start_time
            self.logger.info(
                f"Database cache HIT: {folder_id} ({share_type}) - "
                f"{file_count:,} files, {total_size/1024/1024:.1f} MB ({elapsed*1000:.1f}ms)"
            )
            
            return cache_data
            
        except Exception as e:
            self.logger.debug(f"Enhanced cache retrieval failed for {cache_key[:20]}...: {e}")
            self._record_cache_miss()
            
            # Clean up corrupted entry
            try:
                with self.db.pool.get_connection() as conn:
                    conn.execute("DELETE FROM index_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()
            except:
                pass
            
            return None
    
    def _add_to_memory_cache(self, cache_key: str, data: Dict):
        """Add entry to memory cache with LRU eviction"""
        # Add/update entry
        self.memory_cache[cache_key] = data
        self.memory_cache.move_to_end(cache_key)
        
        # Evict oldest entries if over limit
        while len(self.memory_cache) > self.max_memory_entries:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
            self.stats['memory_evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics with performance metrics"""
        if not self.enabled:
            return {'enabled': False, 'reason': 'Cryptography library not available'}
            
        try:
            # Get database statistics using connection pool
            with self.db.pool.get_connection() as conn:
                # Database statistics
                cursor = conn.execute("""
                    SELECT total_size, total_entries, total_hits, total_misses
                    FROM cache_stats WHERE id = 1
                """)
                
                db_stats = cursor.fetchone()
                if db_stats:
                    db_total_size, db_total_entries, db_total_hits, db_total_misses = db_stats
                else:
                    db_total_size = db_total_entries = db_total_hits = db_total_misses = 0
                
                # Current cache statistics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT folder_id) as unique_folders,
                        COUNT(*) as current_entries,
                        SUM(compressed_size) as current_size,
                        SUM(file_count) as total_files,
                        AVG(compressed_size) as avg_size,
                        MAX(compressed_size) as max_size,
                        MIN(compressed_size) as min_size,
                        AVG(access_count) as avg_access_count,
                        MAX(access_count) as max_access_count
                    FROM index_cache
                """)
                
                cache_stats = cursor.fetchone()
                if cache_stats and cache_stats[0]:
                    (unique_folders, current_entries, current_size, total_files, 
                     avg_size, max_size, min_size, avg_access, max_access) = cache_stats
                else:
                    unique_folders = current_entries = current_size = total_files = 0
                    avg_size = max_size = min_size = avg_access = max_access = 0
            
            # Calculate hit rates
            total_hits = self.stats['memory_hits'] + self.stats['db_hits'] 
            total_misses = self.stats['memory_misses'] + self.stats['db_misses']
            total_requests = total_hits + total_misses
            
            overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            memory_hit_rate = (self.stats['memory_hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'enabled': True,
                'unique_folders': unique_folders or 0,
                'current_entries': current_entries or 0,
                'current_size_mb': (current_size / 1024 / 1024) if current_size else 0,
                'total_files_cached': total_files or 0,
                'avg_entry_size_kb': (avg_size / 1024) if avg_size else 0,
                'max_entry_size_kb': (max_size / 1024) if max_size else 0,
                'min_entry_size_kb': (min_size / 1024) if min_size else 0,
                
                # Performance metrics
                'total_requests': self.stats['total_requests'],
                'memory_hits': self.stats['memory_hits'],
                'memory_misses': self.stats['memory_misses'],
                'db_hits': self.stats['db_hits'],
                'db_misses': self.stats['db_misses'],
                'overall_hit_rate': round(overall_hit_rate, 1),
                'memory_hit_rate': round(memory_hit_rate, 1),
                
                # Memory cache status
                'memory_cache_entries': len(self.memory_cache),
                'memory_cache_max': self.max_memory_entries,
                'memory_evictions': self.stats['memory_evictions'],
                
                # Access patterns
                'avg_access_count': round(avg_access, 1) if avg_access else 0,
                'max_access_count': max_access if max_access else 0,
                
                # Maintenance
                'cache_stores': self.stats['cache_stores'],
                'cleanup_runs': self.stats['cleanup_runs'],
                'last_cleanup': self.stats['last_cleanup']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced cache stats: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def clear(self, folder_id: Optional[str] = None, older_than_days: Optional[int] = None):
        """Clear cache entries with memory cache coordination"""
        if not self.enabled:
            return
            
        try:
            with self.db.pool.get_connection() as conn:
                if folder_id:
                    # Clear specific folder from both memory and database
                    keys_to_remove = [k for k in self.memory_cache.keys() 
                                    if folder_id in k]
                    for key in keys_to_remove:
                        del self.memory_cache[key]
                    
                    # Clear from database
                    cursor = conn.execute("""
                        SELECT SUM(compressed_size), COUNT(*)
                        FROM index_cache WHERE folder_id = ?
                    """, (folder_id,))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        total_size, count = result
                        conn.execute(
                            "DELETE FROM index_cache WHERE folder_id = ?",
                            (folder_id,)
                        )
                        conn.commit()
                        self._update_cache_stats(-total_size, False, count)
                        self.logger.info(f"Cleared {count} cache entries for folder {folder_id}")
                        
                else:
                    # Clear all
                    self.memory_cache.clear()
                    conn.execute("DELETE FROM index_cache")
                    conn.execute("""
                        UPDATE cache_stats 
                        SET total_size = 0, total_entries = 0, last_cleanup = ?
                        WHERE id = 1
                    """, (int(time.time()),))
                    conn.commit()
                    self.logger.info("Cleared all cache entries")
                    
                self.stats['cleanup_runs'] += 1
                self.stats['last_cleanup'] = datetime.now().isoformat()
                    
        except Exception as e:
            self.logger.error(f"Enhanced cache clear failed: {e}")
    
    def _derive_cache_encryption_key(self, base_key: bytes) -> bytes:
        """Derive cache-specific encryption key from base key"""
        if not CRYPTO_AVAILABLE:
            return base_key
            
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'usenet_index_cache_salt_v1',
            info=b'enhanced_cache_encryption_key',
            backend=default_backend()
        )
        
        return hkdf.derive(base_key)
    
    def _encrypt_data(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """Encrypt data using AES-CBC with PKCS7 padding"""
        if not CRYPTO_AVAILABLE:
            return data
            
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()
    
    def _decrypt_data(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt data using AES-CBC with PKCS7 unpadding"""
        if not CRYPTO_AVAILABLE:
            return data
            
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
    
    def _update_cache_stats(self, size_change: int, is_add: bool, count: int = 1):
        """Update cache statistics atomically"""
        try:
            with self.db.pool.get_connection() as conn:
                if is_add:
                    conn.execute("""
                        UPDATE cache_stats
                        SET total_size = total_size + ?,
                            total_entries = total_entries + ?
                        WHERE id = 1
                    """, (size_change, count))
                else:
                    conn.execute("""
                        UPDATE cache_stats
                        SET total_size = total_size + ?,
                            total_entries = total_entries - ?
                        WHERE id = 1
                    """, (size_change, count))
                conn.commit()
        except Exception as e:
            self.logger.debug(f"Failed to update cache stats: {e}")
    
    def _record_cache_hit(self):
        """Record a cache hit for statistics"""
        try:
            with self.db.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE cache_stats
                    SET total_hits = total_hits + 1
                    WHERE id = 1
                """)
                conn.commit()
        except Exception as e:
            self.logger.debug(f"Failed to record cache hit: {e}")
    
    def _record_cache_miss(self):
        """Record a cache miss for statistics"""
        try:
            with self.db.pool.get_connection() as conn:
                conn.execute("""
                    UPDATE cache_stats
                    SET total_misses = total_misses + 1
                    WHERE id = 1
                """)
                conn.commit()
        except Exception as e:
            self.logger.debug(f"Failed to record cache miss: {e}")

# Backward compatibility alias
EncryptedIndexCache = EnhancedEncryptedIndexCache
