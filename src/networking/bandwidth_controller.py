"""
Bandwidth Controller for UsenetSync
Implements rate limiting for upload and download operations
"""

import time
import threading
import asyncio
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
            
            # Add new tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if tokens <= self.tokens:
                # Enough tokens available
                self.tokens -= tokens
                return 0.0
            else:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                return wait_time
    
    def update_rate(self, new_rate: int):
        """Update the rate limit"""
        with self.lock:
            self.rate = new_rate
            self.capacity = new_rate * 2

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
        
        if self.config.max_upload_speed > 0:
            self.upload_bucket = TokenBucket(
                self.config.max_upload_speed,
                int(self.config.max_upload_speed * self.config.burst_size)
            )
        
        if self.config.max_download_speed > 0:
            self.download_bucket = TokenBucket(
                self.config.max_download_speed,
                int(self.config.max_download_speed * self.config.burst_size)
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
    
    def throttle_upload(self, data: bytes) -> bytes:
        """
        Throttle upload data
        
        Args:
            data: Data to upload
            
        Returns:
            Same data (after appropriate delay)
        """
        if not self.upload_bucket:
            # No throttling
            self._record_transfer('upload', len(data))
            return data
        
        # Calculate wait time
        wait_time = self.upload_bucket.consume(len(data))
        
        if wait_time > 0:
            logger.debug(f"Throttling upload: waiting {wait_time:.3f}s")
            time.sleep(wait_time)
        
        self._record_transfer('upload', len(data))
        return data
    
    def throttle_download(self, data: bytes) -> bytes:
        """
        Throttle download data
        
        Args:
            data: Downloaded data
            
        Returns:
            Same data (after appropriate delay)
        """
        if not self.download_bucket:
            # No throttling
            self._record_transfer('download', len(data))
            return data
        
        # Calculate wait time
        wait_time = self.download_bucket.consume(len(data))
        
        if wait_time > 0:
            logger.debug(f"Throttling download: waiting {wait_time:.3f}s")
            time.sleep(wait_time)
        
        self._record_transfer('download', len(data))
        return data
    
    def throttle_upload_chunk(self, chunk_size: int) -> float:
        """
        Get wait time for uploading a chunk
        
        Args:
            chunk_size: Size of chunk in bytes
            
        Returns:
            Wait time in seconds
        """
        if not self.upload_bucket:
            return 0.0
        
        wait_time = self.upload_bucket.consume(chunk_size)
        if wait_time == 0:
            self._record_transfer('upload', chunk_size)
        return wait_time
    
    def throttle_download_chunk(self, chunk_size: int) -> float:
        """
        Get wait time for downloading a chunk
        
        Args:
            chunk_size: Size of chunk in bytes
            
        Returns:
            Wait time in seconds
        """
        if not self.download_bucket:
            return 0.0
        
        wait_time = self.download_bucket.consume(chunk_size)
        if wait_time == 0:
            self._record_transfer('download', chunk_size)
        return wait_time
    
    def _record_transfer(self, direction: str, bytes_count: int):
        """Record bytes transferred for statistics"""
        with self.stats_lock:
            self.stats[direction]['bytes_transferred'] += bytes_count
    
    def set_upload_limit(self, bytes_per_second: int):
        """
        Set upload speed limit
        
        Args:
            bytes_per_second: Maximum upload speed (0 = unlimited)
        """
        self.config.max_upload_speed = bytes_per_second
        
        if bytes_per_second > 0:
            if self.upload_bucket:
                self.upload_bucket.update_rate(bytes_per_second)
            else:
                self.upload_bucket = TokenBucket(
                    bytes_per_second,
                    int(bytes_per_second * self.config.burst_size)
                )
        else:
            self.upload_bucket = None
        
        logger.info(f"Upload limit set to {self._format_speed(bytes_per_second)}")
    
    def set_download_limit(self, bytes_per_second: int):
        """
        Set download speed limit
        
        Args:
            bytes_per_second: Maximum download speed (0 = unlimited)
        """
        self.config.max_download_speed = bytes_per_second
        
        if bytes_per_second > 0:
            if self.download_bucket:
                self.download_bucket.update_rate(bytes_per_second)
            else:
                self.download_bucket = TokenBucket(
                    bytes_per_second,
                    int(bytes_per_second * self.config.burst_size)
                )
        else:
            self.download_bucket = None
        
        logger.info(f"Download limit set to {self._format_speed(bytes_per_second)}")
    
    def get_limits(self) -> Dict[str, int]:
        """Get current bandwidth limits"""
        return {
            'upload': self.config.max_upload_speed,
            'download': self.config.max_download_speed
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bandwidth statistics"""
        with self.stats_lock:
            return {
                'upload': {
                    'current_speed': self.stats['upload']['current_speed'],
                    'limit': self.config.max_upload_speed,
                    'utilization': self._calculate_utilization('upload')
                },
                'download': {
                    'current_speed': self.stats['download']['current_speed'],
                    'limit': self.config.max_download_speed,
                    'utilization': self._calculate_utilization('download')
                }
            }
    
    def _calculate_utilization(self, direction: str) -> float:
        """Calculate bandwidth utilization percentage"""
        limit = (self.config.max_upload_speed if direction == 'upload' 
                else self.config.max_download_speed)
        
        if limit == 0:
            return 0.0
        
        current_speed = self.stats[direction]['current_speed']
        return min(100.0, (current_speed / limit) * 100)
    
    def _format_speed(self, bytes_per_second: int) -> str:
        """Format speed for display"""
        if bytes_per_second == 0:
            return "Unlimited"
        
        units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
        speed = float(bytes_per_second)
        unit_index = 0
        
        while speed >= 1024 and unit_index < len(units) - 1:
            speed /= 1024
            unit_index += 1
        
        return f"{speed:.2f} {units[unit_index]}"

# Global bandwidth controller instance
_bandwidth_controller: Optional[BandwidthController] = None

def get_bandwidth_controller() -> BandwidthController:
    """Get or create global bandwidth controller"""
    global _bandwidth_controller
    if _bandwidth_controller is None:
        _bandwidth_controller = BandwidthController()
    return _bandwidth_controller
    async def consume_upload_tokens(self, bytes_count: int) -> bool:
        """Consume upload tokens asynchronously"""
        if not self.upload_limit_enabled:
            return True
        wait_time = self.consume_upload(bytes_count)
        if wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)
            return False
        return True
    
    async def consume_download_tokens(self, bytes_count: int) -> bool:
        """Consume download tokens asynchronously"""
        if not self.download_limit_enabled:
            return True
        wait_time = self.consume_download(bytes_count)
        if wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)
            return False
        return True


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
# Add async methods to the first BandwidthController class
# These are added at module level and will be attached to the class
def _async_consume_upload(self, bytes_count):
    import asyncio
    async def _consume():
        if not self.upload_bucket:
            return True
        wait_time = self.upload_bucket.consume(bytes_count) if hasattr(self.upload_bucket, 'consume') else 0
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        return wait_time == 0
    return _consume()

def _async_consume_download(self, bytes_count):
    import asyncio
    async def _consume():
        if not self.download_bucket:
            return True
        wait_time = self.download_bucket.consume(bytes_count) if hasattr(self.download_bucket, 'consume') else 0
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        return wait_time == 0
    return _consume()

# Attach to class
BandwidthController.consume_upload_tokens = _async_consume_upload
BandwidthController.consume_download_tokens = _async_consume_download
