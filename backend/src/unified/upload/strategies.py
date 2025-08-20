#!/usr/bin/env python3
"""
Unified Strategies Module - Upload strategies
"""

from enum import Enum
import logging

logger = logging.getLogger(__name__)

class UploadStrategy(Enum):
    """Upload strategies"""
    SIMPLE = "simple"
    OPTIMIZED = "optimized"
    REDUNDANT = "redundant"
    COMPRESSED = "compressed"

class UnifiedStrategies:
    """Upload strategy management"""
    
    def __init__(self):
        self.default_strategy = UploadStrategy.OPTIMIZED
    
    def select_strategy(self, file_size: int, file_type: str) -> UploadStrategy:
        """Select best upload strategy"""
        if file_size < 100000:  # Small files
            return UploadStrategy.SIMPLE
        elif file_type in ['.zip', '.rar', '.7z']:  # Already compressed
            return UploadStrategy.REDUNDANT
        else:
            return UploadStrategy.OPTIMIZED