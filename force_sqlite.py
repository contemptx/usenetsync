#!/usr/bin/env python3
"""
Force UsenetSync to use SQLite instead of PostgreSQL
"""

import os
import json
from pathlib import Path

def force_sqlite_mode():
    """Configure UsenetSync to use SQLite"""
    
    # Get config directory
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync'
    else:
        config_dir = Path.home() / '.usenetsync'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / 'config.json'
    
    # Load existing config or create new
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {}
    
    # Force SQLite mode
    config['database'] = {
        'type': 'sqlite',
        'force_sqlite': True
    }
    
    # Save config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("=" * 60)
    print("SQLite Mode Activated")
    print("=" * 60)
    print(f"\nConfiguration saved to: {config_file}")
    print("\nUsenetSync will now use SQLite database.")
    print("This avoids PostgreSQL connection issues.")
    print("\nTo switch back to PostgreSQL later:")
    print("1. Fix PostgreSQL using diagnose_postgresql.py")
    print("2. Delete the config.json file")
    print("3. Restart UsenetSync")

if __name__ == '__main__':
    force_sqlite_mode()