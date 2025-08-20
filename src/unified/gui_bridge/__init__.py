"""
Unified GUI Bridge Module - Tauri integration for React frontend
Production-ready bridge between Python backend and Tauri/React GUI
"""

from .tauri_bridge import UnifiedTauriBridge
from .complete_tauri_bridge import CompleteTauriBridge

__all__ = [
    'UnifiedTauriBridge',
    'CompleteTauriBridge'
]