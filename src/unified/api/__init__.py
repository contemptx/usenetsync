"""
Unified API Module - FastAPI server with WebSocket support
Production-ready REST API and real-time updates
"""

from .server import UnifiedAPIServer
from .routes import UnifiedRoutes
from .websocket import UnifiedWebSocket
from .middleware import UnifiedMiddleware
from .authentication import UnifiedAPIAuth
from .responses import UnifiedResponses

__all__ = [
    'UnifiedAPIServer',
    'UnifiedRoutes',
    'UnifiedWebSocket',
    'UnifiedMiddleware',
    'UnifiedAPIAuth',
    'UnifiedResponses'
]