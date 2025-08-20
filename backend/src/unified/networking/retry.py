#!/usr/bin/env python3
"""
Unified Retry Logic - Exponential backoff and retry strategies
"""

import time
import random
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedRetry:
    """Retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0):
        """
        Initialize retry handler
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    
                    # Add jitter
                    delay *= (0.5 + random.random())
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        raise last_exception
    
    def with_custom_exceptions(self, func: Callable, 
                              retryable_exceptions: tuple,
                              *args, **kwargs) -> Any:
        """
        Execute with specific retryable exceptions
        
        Args:
            func: Function to execute
            retryable_exceptions: Tuple of exception types to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    delay *= (0.5 + random.random())
                    
                    logger.warning(f"Retryable error on attempt {attempt + 1}: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for retryable error")
                    
            except Exception as e:
                # Non-retryable exception, raise immediately
                logger.error(f"Non-retryable error: {e}")
                raise
        
        raise last_exception