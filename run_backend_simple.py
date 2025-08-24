#!/usr/bin/env python3
"""Simplified backend runner that starts quickly"""
import os
import sys

# Add backend src to path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

from unified.api.server import UnifiedAPIServer
import uvicorn

# Create server without full system initialization
server = UnifiedAPIServer()

# Run
print("Starting simplified backend on port 8000...")
uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")