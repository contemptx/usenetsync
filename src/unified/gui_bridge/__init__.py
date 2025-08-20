"""
Unified GUI Bridge - Handles all GUI communication
"""

# Main bridge
from .complete_tauri_bridge import CompleteTauriBridge

# Alias for compatibility
TauriBridge = CompleteTauriBridge

__all__ = ['CompleteTauriBridge', 'TauriBridge']
