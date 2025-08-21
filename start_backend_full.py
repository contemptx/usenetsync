#!/usr/bin/env python3
"""Full backend starter with system initialization"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from unified.main import UnifiedSystem
from unified.api.server import UnifiedAPIServer
from unified.core.config import load_config

if __name__ == "__main__":
    print("Starting UsenetSync Backend with full system...")
    
    # Initialize the unified system
    config = load_config()
    system = UnifiedSystem(config)
    
    # Create API server with the system
    server = UnifiedAPIServer()
    server.system = system  # Attach the system
    
    # Run with uvicorn
    import uvicorn
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")