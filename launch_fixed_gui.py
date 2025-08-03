#!/usr/bin/env python3
"""
Simple Launcher for Fixed UsenetSync GUI
"""

import os
import sys
import subprocess

def main():
    """Launch the fixed GUI"""
    
    print("UsenetSync GUI Launcher")
    print("=" * 40)
    
    # Check if the complete GUI exists
    if os.path.exists('usenetsync_gui_main_complete.py'):
        print("✓ Found complete GUI file")
        print("🚀 Launching UsenetSync GUI...")
        
        try:
            # Launch the GUI
            subprocess.run([sys.executable, 'usenetsync_gui_main_complete.py'])
        except Exception as e:
            print(f"✗ Error launching GUI: {e}")
            input("Press Enter to exit...")
    else:
        print("✗ Complete GUI file not found")
        print("Please run the deployment script first")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
