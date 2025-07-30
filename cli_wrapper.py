#!/usr/bin/env python3 
import sys 
import os 
from pathlib import Path 
 
# Add project root to Python path 
project_root = Path(__file__).parent.absolute() 
sys.path.insert(0, str(project_root)) 
 
if __name__ == '__main__': 
    try: 
        from cli import cli 
        cli() 
    except ImportError as e: 
        print(f"Import error: {e}") 
        print("Please ensure all dependencies are installed") 
        sys.exit(1) 
