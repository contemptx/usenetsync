#!/usr/bin/env python3
"""Simple backend runner"""
import os
import sys

# Add backend src to path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

print(f"Python path: {sys.path}")
print(f"Starting backend from: {backend_src}")

try:
    from unified.main import UnifiedSystem
    from unified.api.server import UnifiedAPIServer
    from unified.core.config import load_config
    import uvicorn
    
    print("Imports successful")
    
    # Initialize
    config = load_config()
    print("Config loaded")
    
    system = UnifiedSystem(config)
    print("System initialized")
    
    server = UnifiedAPIServer()
    server.system = system
    print("Server created")
    
    # Run
    print("Starting uvicorn on port 8000...")
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)