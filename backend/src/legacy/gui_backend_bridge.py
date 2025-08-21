#!/usr/bin/env python3
"""
GUI Backend Bridge - Connects Tauri GUI to Unified System
This replaces the old cli.py with unified system calls
Supports both old CLI format and new unified format
"""

import sys
import os
import json
import asyncio
import argparse
from pathlib import Path

# Add unified system to path
sys.path.insert(0, os.path.dirname(__file__))

from unified.main import UnifiedSystem
from unified.gui_bridge.complete_tauri_bridge import CompleteTauriBridge
from unified.api.server import UnifiedAPIServer

# Global system instance
SYSTEM = None
BRIDGE = None

def initialize_system():
    """Initialize the unified system"""
    global SYSTEM, BRIDGE
    
    if SYSTEM is None:
        SYSTEM = UnifiedSystem()
        BRIDGE = CompleteTauriBridge(SYSTEM)
    
    return SYSTEM, BRIDGE

def handle_command(command_data: str) -> str:
    """
    Handle command from Tauri GUI
    
    Args:
        command_data: JSON string with command and args
    
    Returns:
        JSON string with response
    """
    try:
        # Parse command
        data = json.loads(command_data)
        command = data.get('command')
        args = data.get('args', {})
        
        # Initialize system if needed
        system, bridge = initialize_system()
        
        # Handle command through bridge
        result = asyncio.run(bridge.handle_command(command, args))
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e)
        })

def main():
    """Main entry point for GUI backend"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['cli', 'api', 'command'], default='api')
    parser.add_argument('--command', help='Command to execute (JSON)')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    
    args = parser.parse_args()
    
    if args.mode == 'command':
        # Single command mode (for Tauri)
        if args.command:
            result = handle_command(args.command)
            print(result)
        else:
            print(json.dumps({'success': False, 'error': 'No command provided'}))
    
    elif args.mode == 'api':
        # API server mode
        system, _ = initialize_system()
        api = UnifiedAPIServer(system)
        
        print(f"Starting Unified API Server on {args.host}:{args.port}")
        api.run(host=args.host, port=args.port)
    
    else:
        # CLI mode
        from unified.main import main as unified_main
        unified_main()

if __name__ == "__main__":
    main()