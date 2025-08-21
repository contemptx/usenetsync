"""
Bandwidth Controller for UsenetSync - Fixed Version
Implements rate limiting for upload and download operations
"""

import asyncio
import time
import threading
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BandwidthConfig:
    """Bandwidth configuration"""
    max_upload_speed: int  # bytes per second, 0 = unlimited
    max_download_speed: int  # bytes per second, 0 = unlimited
    burst_size: float = 1.5  # Allow burst up to 1.5x for short periods
    measurement_window: float = 1.0  # seconds

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: int, capacity: Optional[int] = None):
        """
        Initialize token bucket
        
        Args:
            rate: Tokens per second (bytes per second)
            capacity: Maximum bucket capacity (default: rate * 2)
        """
        self.rate = rate
        self.capacity = capacity or rate * 2
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int) -> float:
        """
        Consume tokens from bucket, return wait time if not enough tokens
        
        Args:
            tokens: Number of tokens to consume (bytes)
            
        Returns:
            Wait time in seconds (0 if tokens available immediately)
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Add new tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0  # No wait needed
            else:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                return wait_time
    
    def reset(self):
        """Reset bucket to full capacity"""
        with self.lock:
            self.tokens = self.capacity
            self.last_update = time.time()

class BandwidthController:
    """Controls bandwidth for all network operations"""
    
    def __init__(self, config: Optional[BandwidthConfig] = None):
        """Initialize bandwidth controller"""
        self.config = config or BandwidthConfig(
            max_upload_speed=0,  # Unlimited by default
            max_download_speed=0
        )
        
        # Create token buckets for rate limiting
        self.upload_bucket = None
        self.download_bucket = None
        
        # Upload/Download state
        self.upload_limit = self.config.max_upload_speed
        self.download_limit = self.config.max_download_speed
        self.upload_limit_enabled = self.config.max_upload_speed > 0
        self.download_limit_enabled = self.config.max_download_speed > 0
        
        # Initialize buckets if limits are set
        if self.upload_limit_enabled:
            self.upload_bucket = TokenBucket(
                self.upload_limit,
                int(self.upload_limit * self.config.burst_size)
            )
        
        if self.download_limit_enabled:
            self.download_bucket = TokenBucket(
                self.download_limit,
                int(self.download_limit * self.config.burst_size)
            )
        
        # Statistics
        self.stats = {
            'upload': {
                'bytes_transferred': 0,
                'start_time': time.time(),
                'current_speed': 0
            },
            'download': {
                'bytes_transferred': 0,
                'start_time': time.time(),
                'current_speed': 0
            }
        }
        self.stats_lock = threading.Lock()
        
        # Additional stats for compatibility
        self.upload_bytes_sent = 0
        self.download_bytes_received = 0
        self.upload_start_time = time.time()
        self.download_start_time = time.time()
        
        # Start statistics updater
        self._start_stats_updater()
    
    def _start_stats_updater(self):
        """Start background thread to update speed statistics"""
        def updater():
            while True:
                time.sleep(1)
                self._update_speeds()
        
        thread = threading.Thread(target=updater, daemon=True)
        thread.start()
    
    def _update_speeds(self):
        """Update current transfer speeds"""
        with self.stats_lock:
            now = time.time()
            
            for direction in ['upload', 'download']:
                stats = self.stats[direction]
                elapsed = now - stats['start_time']
                if elapsed > 0:
                    stats['current_speed'] = stats['bytes_transferred'] / elapsed
                
                # Reset counters every minute to get recent speed
                if elapsed > 60:
                    stats['bytes_transferred'] = 0
                    stats['start_time'] = now
    
    def set_upload_limit(self, bytes_per_second: int):
        """Set upload bandwidth limit"""
        self.upload_limit = bytes_per_second
        self.upload_limit_enabled = bytes_per_second > 0
        
        if self.upload_limit_enabled:
            self.upload_bucket = TokenBucket(
                bytes_per_second,
                int(bytes_per_second * self.config.burst_size)
            )
        else:
            self.upload_bucket = None
        
        logger.info(f"Upload limit set to {bytes_per_second} bytes/sec")
    
    def set_download_limit(self, bytes_per_second: int):
        """Set download bandwidth limit"""
        self.download_limit = bytes_per_second
        self.download_limit_enabled = bytes_per_second > 0
        
        if self.download_limit_enabled:
            self.download_bucket = TokenBucket(
                bytes_per_second,
                int(bytes_per_second * self.config.burst_size)
            )
        else:
            self.download_bucket = None
        
        logger.info(f"Download limit set to {bytes_per_second} bytes/sec")
    
    def throttle_upload(self, data: bytes) -> bytes:
        """Throttle upload data"""
        if not self.upload_bucket:
            return data
        
        wait_time = self.upload_bucket.consume(len(data))
        if wait_time > 0:
            time.sleep(wait_time)
        
        with self.stats_lock:
            self.stats['upload']['bytes_transferred'] += len(data)
            self.upload_bytes_sent += len(data)
        
        return data
    
    def throttle_download(self, data: bytes) -> bytes:
        """Throttle download data"""
        if not self.download_bucket:
            return data
        
        wait_time = self.download_bucket.consume(len(data))
        if wait_time > 0:
            time.sleep(wait_time)
        
        with self.stats_lock:
            self.stats['download']['bytes_transferred'] += len(data)
            self.download_bytes_received += len(data)
        
        return data
    
    def consume_upload(self, bytes_count: int) -> float:
        """Consume upload bandwidth and return wait time"""
        if not self.upload_bucket:
            return 0
        return self.upload_bucket.consume(bytes_count)
    
    def consume_download(self, bytes_count: int) -> float:
        """Consume download bandwidth and return wait time"""
        if not self.download_bucket:
            return 0
        return self.download_bucket.consume(bytes_count)
    
    async def consume_upload_tokens(self, bytes_count: int) -> bool:
        """Async version - consume upload tokens for rate limiting"""
        if not self.upload_limit_enabled or not self.upload_bucket:
            return True
        
        wait_time = self.upload_bucket.consume(bytes_count)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            return False
        
        with self.stats_lock:
            self.stats['upload']['bytes_transferred'] += bytes_count
            self.upload_bytes_sent += bytes_count
        
        return True
    
    async def consume_download_tokens(self, bytes_count: int) -> bool:
        """Async version - consume download tokens for rate limiting"""
        if not self.download_limit_enabled or not self.download_bucket:
            return True
        
        wait_time = self.download_bucket.consume(bytes_count)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            return False
        
        with self.stats_lock:
            self.stats['download']['bytes_transferred'] += bytes_count
            self.download_bytes_received += bytes_count
        
        return True
    
    def throttle_upload_chunk(self, chunk: bytes, chunk_size: int = 8192) -> bytes:
        """Throttle upload with chunking"""
        result = bytearray()
        for i in range(0, len(chunk), chunk_size):
            sub_chunk = chunk[i:i + chunk_size]
            result.extend(self.throttle_upload(sub_chunk))
        return bytes(result)
    
    def throttle_download_chunk(self, chunk: bytes, chunk_size: int = 8192) -> bytes:
        """Throttle download with chunking"""
        result = bytearray()
        for i in range(0, len(chunk), chunk_size):
            sub_chunk = chunk[i:i + chunk_size]
            result.extend(self.throttle_download(sub_chunk))
        return bytes(result)
    
    def get_upload_speed(self) -> float:
        """Get current upload speed in bytes/sec"""
        with self.stats_lock:
            return self.stats['upload']['current_speed']
    
    def get_download_speed(self) -> float:
        """Get current download speed in bytes/sec"""
        with self.stats_lock:
            return self.stats['download']['current_speed']
    
    def get_limits(self) -> Dict[str, Any]:
        """Get current bandwidth limits"""
        return {
            'upload_limit': self.upload_limit,
            'download_limit': self.download_limit,
            'upload_enabled': self.upload_limit_enabled,
            'download_enabled': self.download_limit_enabled
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bandwidth statistics"""
        with self.stats_lock:
            return self.stats.copy()
    
    def get_bandwidth_stats(self) -> Dict[str, Any]:
        """Get comprehensive bandwidth statistics"""
        return {
            'upload': {
                'current_speed': self.get_upload_speed(),
                'limit': self.upload_limit,
                'enabled': self.upload_limit_enabled,
                'bytes_sent': self.upload_bytes_sent,
                'start_time': self.upload_start_time
            },
            'download': {
                'current_speed': self.get_download_speed(),
                'limit': self.download_limit,
                'enabled': self.download_limit_enabled,
                'bytes_received': self.download_bytes_received,
                'start_time': self.download_start_time
            }
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        with self.stats_lock:
            now = time.time()
            self.stats = {
                'upload': {
                    'bytes_transferred': 0,
                    'start_time': now,
                    'current_speed': 0
                },
                'download': {
                    'bytes_transferred': 0,
                    'start_time': now,
                    'current_speed': 0
                }
            }
            self.upload_bytes_sent = 0
            self.download_bytes_received = 0
            self.upload_start_time = now
            self.download_start_time = now

# Global instance
_controller_instance = None

def get_bandwidth_controller() -> BandwidthController:
    """Get or create global bandwidth controller instance"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = BandwidthController()
    return _controller_instance

def set_bandwidth_limits(upload_mbps: float = 0, download_mbps: float = 0):
    """
    Set bandwidth limits in Mbps
    
    Args:
        upload_mbps: Upload limit in Mbps (0 = unlimited)
        download_mbps: Download limit in Mbps (0 = unlimited)
    """
    controller = get_bandwidth_controller()
    
    # Convert Mbps to bytes per second
    upload_bps = int(upload_mbps * 1024 * 1024 / 8) if upload_mbps > 0 else 0
    download_bps = int(download_mbps * 1024 * 1024 / 8) if download_mbps > 0 else 0
    
    controller.set_upload_limit(upload_bps)
    controller.set_download_limit(download_bps)