#!/usr/bin/env python3
"""
Enhanced NNTP Retry System
Implements intelligent retry logic with rate limiting and exponential backoff
"""

import time
import random
import logging
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    rate_limit_window: int = 60  # seconds
    max_requests_per_window: int = 10
    rate_limit_retry_delay: float = 30.0  # delay when rate limited
    
    # Error-specific configurations
    error_configs: Dict[int, Dict] = None
    
    def __post_init__(self):
        if self.error_configs is None:
            self.error_configs = {
                502: {  # Rate limiting error
                    'max_retries': 10,
                    'initial_delay': 30.0,
                    'backoff_multiplier': 1.5
                },
                441: {  # Article refused
                    'max_retries': 3,
                    'initial_delay': 5.0,
                    'backoff_multiplier': 2.0
                },
                500: {  # Server error
                    'max_retries': 5,
                    'initial_delay': 10.0,
                    'backoff_multiplier': 2.0
                }
            }


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()
        
    def can_proceed(self) -> bool:
        """Check if request can proceed without exceeding rate limit"""
        with self.lock:
            now = time.time()
            # Remove old requests outside the window
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
            
    def get_wait_time(self) -> float:
        """Get time to wait before next request can proceed"""
        with self.lock:
            if not self.requests:
                return 0.0
            
            now = time.time()
            # Clean old requests
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()
                
            if len(self.requests) < self.max_requests:
                return 0.0
                
            # Calculate wait time until oldest request expires
            oldest = self.requests[0]
            wait_time = (oldest + self.window_seconds) - now
            return max(0.0, wait_time)


class RetryStatistics:
    """Track retry statistics for monitoring"""
    
    def __init__(self):
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.retry_counts = {}
        self.error_counts = {}
        self.last_error = None
        self.last_success_time = None
        
    def record_attempt(self, success: bool, retries: int = 0, error: Optional[Exception] = None):
        """Record an attempt"""
        self.total_attempts += 1
        
        if success:
            self.successful_attempts += 1
            self.last_success_time = datetime.now()
        else:
            self.failed_attempts += 1
            if error:
                self.last_error = str(error)
                error_type = type(error).__name__
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
                
        self.retry_counts[retries] = self.retry_counts.get(retries, 0) + 1
        
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100
        
    def get_stats(self) -> Dict:
        """Get statistics summary"""
        return {
            'total_attempts': self.total_attempts,
            'successful': self.successful_attempts,
            'failed': self.failed_attempts,
            'success_rate': self.get_success_rate(),
            'retry_distribution': self.retry_counts,
            'error_types': self.error_counts,
            'last_error': self.last_error,
            'last_success': self.last_success_time.isoformat() if self.last_success_time else None
        }


class EnhancedNNTPRetry:
    """Enhanced retry system for NNTP operations"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.rate_limiter = RateLimiter(
            self.config.max_requests_per_window,
            self.config.rate_limit_window
        )
        self.statistics = RetryStatistics()
        
    def calculate_delay(self, attempt: int, error_code: Optional[int] = None) -> float:
        """Calculate delay before next retry"""
        # Use error-specific config if available
        if error_code and error_code in self.config.error_configs:
            error_config = self.config.error_configs[error_code]
            initial_delay = error_config.get('initial_delay', self.config.initial_delay)
            multiplier = error_config.get('backoff_multiplier', self.config.exponential_base)
        else:
            initial_delay = self.config.initial_delay
            multiplier = self.config.exponential_base
            
        # Calculate exponential backoff
        delay = min(
            initial_delay * (multiplier ** attempt),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            delay *= (0.5 + random.random())
            
        return delay
        
    def execute_with_retry(self, 
                          func: Callable,
                          *args,
                          on_retry: Optional[Callable] = None,
                          **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Arguments for function
            on_retry: Optional callback for retry events
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            # Check rate limit
            if not self.rate_limiter.can_proceed():
                wait_time = self.rate_limiter.get_wait_time()
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                
            try:
                # Execute function
                result = func(*args, **kwargs)
                self.statistics.record_attempt(True, attempt)
                
                if attempt > 0:
                    logger.info(f"Succeeded after {attempt} retries")
                    
                return result
                
            except Exception as e:
                last_exception = e
                error_code = self._extract_error_code(e)
                
                # Check if we should retry
                if attempt >= self.config.max_retries:
                    logger.error(f"Max retries ({self.config.max_retries}) exhausted")
                    self.statistics.record_attempt(False, attempt, e)
                    raise
                    
                # Special handling for specific errors
                if error_code == 502:  # Rate limiting
                    logger.warning(f"Rate limiting detected (502), using extended delay")
                    delay = self.config.rate_limit_retry_delay
                elif error_code == 441:  # Article refused
                    logger.warning(f"Article refused (441), may need content adjustment")
                    delay = self.calculate_delay(attempt, error_code)
                else:
                    delay = self.calculate_delay(attempt, error_code)
                    
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                
                # Call retry callback if provided
                if on_retry:
                    on_retry(attempt, delay, e)
                    
                time.sleep(delay)
                
        # Should not reach here, but for safety
        self.statistics.record_attempt(False, self.config.max_retries, last_exception)
        raise last_exception
        
    def _extract_error_code(self, exception: Exception) -> Optional[int]:
        """Extract error code from exception"""
        error_str = str(exception)
        
        # Try to extract NNTP error code
        if error_str.startswith('502'):
            return 502
        elif error_str.startswith('441'):
            return 441
        elif error_str.startswith('500'):
            return 500
            
        # Try to parse from tuple response
        if hasattr(exception, 'args') and len(exception.args) > 0:
            try:
                if isinstance(exception.args[0], int):
                    return exception.args[0]
            except:
                pass
                
        return None
        
    def get_statistics(self) -> Dict:
        """Get retry statistics"""
        return self.statistics.get_stats()
        
    def reset_statistics(self):
        """Reset statistics"""
        self.statistics = RetryStatistics()


class SmartUploadQueue:
    """Smart upload queue with retry management"""
    
    def __init__(self, retry_system: EnhancedNNTPRetry):
        self.retry_system = retry_system
        self.queue = deque()
        self.failed_items = []
        self.lock = threading.Lock()
        
    def add_item(self, item: Dict):
        """Add item to upload queue"""
        with self.lock:
            item['attempts'] = 0
            item['added_at'] = datetime.now()
            self.queue.append(item)
            
    def process_item(self, upload_func: Callable) -> Optional[Dict]:
        """Process next item in queue"""
        with self.lock:
            if not self.queue:
                return None
            item = self.queue.popleft()
            
        try:
            # Use retry system for upload
            result = self.retry_system.execute_with_retry(
                upload_func,
                item,
                on_retry=lambda a, d, e: self._on_retry(item, a, d, e)
            )
            
            item['result'] = result
            item['completed_at'] = datetime.now()
            return item
            
        except Exception as e:
            logger.error(f"Failed to upload item after retries: {e}")
            item['error'] = str(e)
            item['failed_at'] = datetime.now()
            
            with self.lock:
                self.failed_items.append(item)
            return None
            
    def _on_retry(self, item: Dict, attempt: int, delay: float, error: Exception):
        """Handle retry event"""
        item['attempts'] = attempt + 1
        item['last_error'] = str(error)
        logger.info(f"Retrying item {item.get('id', 'unknown')} - attempt {attempt + 1}")
        
    def requeue_failed(self):
        """Requeue failed items for retry"""
        with self.lock:
            for item in self.failed_items:
                item['requeued'] = True
                self.queue.append(item)
            self.failed_items.clear()
            
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        with self.lock:
            return {
                'pending': len(self.queue),
                'failed': len(self.failed_items),
                'retry_stats': self.retry_system.get_statistics()
            }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create retry system with custom config
    config = RetryConfig(
        max_retries=5,
        initial_delay=2.0,
        max_delay=30.0,
        rate_limit_window=60,
        max_requests_per_window=5
    )
    
    retry_system = EnhancedNNTPRetry(config)
    
    # Simulate NNTP operations
