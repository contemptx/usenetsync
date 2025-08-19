"""
Unified GUI Bridge Module - Tauri integration for React frontend
Production-ready bridge between Python backend and Tauri/React GUI
"""

from .tauri_bridge import UnifiedTauriBridge
from .command_handler import UnifiedCommandHandler
from .event_emitter import UnifiedEventEmitter
from .state_sync import UnifiedStateSync
from .file_watcher import UnifiedFileWatcher
from .progress_stream import UnifiedProgressStream

__all__ = [
    'UnifiedTauriBridge',
    'UnifiedCommandHandler',
    'UnifiedEventEmitter',
    'UnifiedStateSync',
    'UnifiedFileWatcher',
    'UnifiedProgressStream'
]