"""
Auto-Retry Manager with Exponential Backoff
Handles automatic retries for failed network operations
"""

import time
import random
import asyncio
import logging
from typing import Optional, Callable, Any, TypeVar, Union
from dataclasses import dataclass
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    FIXED = "fixed"

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomization to prevent thundering herd
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retry_on: tuple = (Exception,)  # Exceptions to retry on
    on_retry: Optional[Callable[[int, float, Exception], None]] = None
    on_giveup: Optional[Callable[[Exception], None]] = None

class RetryManager:
    """Manages retry logic with various strategies"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry manager"""
        self.config = config or RetryConfig()
        self._retry_counts = {}
        
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for next retry based on strategy
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (self.config.exponential_base ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci_delay(attempt)
        else:  # FIXED
            delay = self.config.initial_delay
        
        # Apply max delay cap
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if enabled
        if self.config.jitter:
            delay = self._add_jitter(delay)
        
        return delay
    
    def _fibonacci_delay(self, attempt: int) -> float:
        """Calculate Fibonacci-based delay"""
        if attempt == 0:
            return self.config.initial_delay
        elif attempt == 1:
            return self.config.initial_delay * 2
        
        a, b = self.config.initial_delay, self.config.initial_delay * 2
        for _ in range(2, attempt + 1):
            a, b = b, a + b
        return b
    
    def _add_jitter(self, delay: float) -> float:
        """Add random jitter to delay (±25%)"""
        jitter_range = delay * 0.25
        return delay + random.uniform(-jitter_range, jitter_range)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_retries:
            return False
        
        # Check if exception type should be retried
        for exc_type in self.config.retry_on:
            if isinstance(exception, exc_type):
                return True
        
        return False
    
    async def execute_with_retry_async(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    if self.config.on_giveup:
                        self.config.on_giveup(e)
                    raise
                
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    
                    if self.config.on_retry:
                        self.config.on_retry(attempt + 1, delay, e)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{self.config.max_retries}: "
                        f"{str(e)}. Waiting {delay:.2f}s before next attempt."
                    )
                    
                    await asyncio.sleep(delay)
        
        if self.config.on_giveup:
            self.config.on_giveup(last_exception)
        
        raise last_exception
    
    def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute sync function with retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    if self.config.on_giveup:
                        self.config.on_giveup(e)
                    raise
                
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    
                    if self.config.on_retry:
                        self.config.on_retry(attempt + 1, delay, e)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{self.config.max_retries}: "
                        f"{str(e)}. Waiting {delay:.2f}s before next attempt."
                    )
                    
                    time.sleep(delay)
        
        if self.config.on_giveup:
            self.config.on_giveup(last_exception)
        
        raise last_exception

def retry(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retry_on: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
    on_giveup: Optional[Callable] = None
):
    """
    Decorator for adding retry logic to functions
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        strategy: Retry strategy to use
        retry_on: Tuple of exceptions to retry on
        on_retry: Callback when retrying
        on_giveup: Callback when giving up
    """
    def decorator(func):
        config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            strategy=strategy,
            retry_on=retry_on,
            on_retry=on_retry,
            on_giveup=on_giveup
        )
        
        manager = RetryManager(config)
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await manager.execute_with_retry_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return manager.execute_with_retry(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator

class NetworkRetryManager(RetryManager):
    """Specialized retry manager for network operations"""
    
    def __init__(self):
        """Initialize with network-specific configuration"""
        super().__init__(RetryConfig(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True,
            strategy=RetryStrategy.EXPONENTIAL,
            retry_on=(
                ConnectionError,
                TimeoutError,
                OSError,
                IOError,
            ),
            on_retry=self._log_retry,
            on_giveup=self._log_giveup
        ))
        
        self.stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_operations': 0,
            'total_delay_time': 0.0
        }
    
    def _log_retry(self, attempt: int, delay: float, exception: Exception):
        """Log retry attempt"""
        self.stats['total_retries'] += 1
        self.stats['total_delay_time'] += delay
        logger.info(f"Network retry {attempt}: {exception.__class__.__name__} - waiting {delay:.2f}s")
    
    def _log_giveup(self, exception: Exception):
        """Log when giving up"""
        self.stats['failed_operations'] += 1
        logger.error(f"Network operation failed after all retries: {exception}")
    
    def get_stats(self) -> dict:
        """Get retry statistics"""
        return {
            **self.stats,
            'average_delay': (
                self.stats['total_delay_time'] / self.stats['total_retries']
                if self.stats['total_retries'] > 0 else 0
            )
        }

# Global network retry manager
_network_retry_manager = NetworkRetryManager()

def get_network_retry_manager() -> NetworkRetryManager:
    """Get global network retry manager"""
    return _network_retry_manager

# Convenience decorator for network operations
network_retry = retry(
    max_retries=5,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
    strategy=RetryStrategy.EXPONENTIAL,
    retry_on=(ConnectionError, TimeoutError, OSError, IOError)
)