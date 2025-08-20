#!/usr/bin/env python3
"""
Unified Logger - Centralized logging
"""

import logging

class UnifiedLogger:
    """Centralized logger"""
    
    def __init__(self):
        self.logger = logging.getLogger('unified')
    
    def log(self, level, message):
        """Log message"""
        self.logger.log(level, message)