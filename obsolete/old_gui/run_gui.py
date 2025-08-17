#!/usr/bin/env python3
"""
Production GUI Launcher for UsenetSync
Simple, reliable launcher that bypasses complex validation
"""

import sys
import os
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Simple production launcher"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        print("=" * 50)
        print("    UsenetSync GUI - Production Launch")
        print("=" * 50)
        print()
        
        # Check Python version
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"ERROR: Python 3.8+ required, found {version.major}.{version.minor}")
            input("Press Enter to exit...")
            return 1
            
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        
        # Check tkinter
        try:
            import tkinter
            print("✓ GUI framework available")
        except ImportError:
            print("ERROR: tkinter not available")
            input("Press Enter to exit...")
            return 1
        
        # Create basic directories
        for dirname in ['data', 'temp', 'logs', 'downloads']:
            dirpath = current_dir / dirname
            dirpath.mkdir(exist_ok=True)
        print("✓ Directories created")
        
        # Check for config file
        config_file = current_dir / 'usenet_sync_config.json'
        if not config_file.exists():
            print("WARNING: Configuration file not found")
            print("Please edit usenet_sync_config.json with your NNTP server details")
        else:
            print("✓ Configuration file found")
        
        print()
        print("Starting GUI...")
        print()
        
        # Import and run GUI
        try:
            from usenetsync_gui_main import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"ERROR: Failed to import GUI: {e}")
            print("\nMake sure all GUI files are present:")
            print("- usenetsync_gui_main.py")
            print("- usenetsync_gui_user.py") 
            print("- usenetsync_gui_folder.py")
            print("- usenetsync_gui_download.py")
            input("Press Enter to exit...")
            return 1
        except Exception as e:
            print(f"ERROR: GUI failed to start: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to exit...")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nGUI closed by user")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
