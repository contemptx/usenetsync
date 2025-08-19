"""
Unified Indexing Module - Complete file indexing with streaming
Production-ready with versioning and large dataset support
"""

from .scanner import UnifiedScanner
from .versioning import UnifiedVersioning  
from .binary_index import UnifiedBinaryIndex
from .streaming import UnifiedStreaming
from .change_detection import UnifiedChangeDetection
from .folder_stats import UnifiedFolderStats

__all__ = [
    'UnifiedScanner',
    'UnifiedVersioning',
    'UnifiedBinaryIndex', 
    'UnifiedStreaming',
    'UnifiedChangeDetection',
    'UnifiedFolderStats'
]