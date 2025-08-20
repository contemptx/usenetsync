#!/usr/bin/env python3
"""
Unified Bandwidth Control - Rate limiting for uploads/downloads
"""

import time
import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedBandwidth:
    """Bandwidth control with rate limiting"""
    
    def __init__(self, max_rate_mbps: Optional[float] = None):
        """
        Initialize bandwidth controller
        
        Args:
            max_rate_mbps: Maximum rate in megabits per second
        """
        self.max_rate_mbps = max_rate_mbps
        self.max_rate_bytes = (max_rate_mbps * 1024 * 1024 / 8) if max_rate_mbps else None
        self._lock = threading.Lock()
        self._last_time = time.time()
        self._bytes_sent = 0
    
    def throttle(self, bytes_count: int):
        """
        Throttle bandwidth by sleeping if necessary
        
        Args:
            bytes_count: Number of bytes being sent
        """
        if not self.max_rate_bytes:
            return
        
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._last_time
            
            # Calculate current rate
            if elapsed > 0:
                current_rate = self._bytes_sent / elapsed
                
                # If exceeding limit, sleep
                if current_rate > self.max_rate_bytes:
                    sleep_time = (self._bytes_sent / self.max_rate_bytes) - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        current_time = time.time()
            
            # Reset counter every second
            if current_time - self._last_time >= 1.0:
                self._last_time = current_time
                self._bytes_sent = bytes_count
            else:
                self._bytes_sent += bytes_count
    
    def get_current_rate(self) -> float:
        """Get current transfer rate in Mbps"""
        with self._lock:
            elapsed = time.time() - self._last_time
            if elapsed > 0:
                rate_bytes = self._bytes_sent / elapsed
                return rate_bytes * 8 / (1024 * 1024)  # Convert to Mbps
            return 0.0
    
    def set_limit(self, max_rate_mbps: Optional[float]):
        """Update rate limit"""
        self.max_rate_mbps = max_rate_mbps
        self.max_rate_bytes = (max_rate_mbps * 1024 * 1024 / 8) if max_rate_mbps else None