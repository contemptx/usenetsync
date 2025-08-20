#!/usr/bin/env python3
"""Simple backend starter for testing"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# Just start the API server with defaults
from unified.api.server import UnifiedAPIServer

if __name__ == "__main__":
    print("Starting UsenetSync Backend API...")
    server = UnifiedAPIServer()
    
    # Run with uvicorn
    import uvicorn
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")