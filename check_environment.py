#!/usr/bin/env python3
"""
Check what's actually available in the environment
"""

import sys
import os

with open('/workspace/ENVIRONMENT_CHECK.txt', 'w') as f:
    f.write("ENVIRONMENT CHECK\n")
    f.write("=" * 50 + "\n\n")
    
    # Python version
    f.write(f"Python: {sys.version}\n")
    f.write(f"Executable: {sys.executable}\n\n")
    
    # Python path
    f.write("Python Path:\n")
    for p in sys.path:
        f.write(f"  {p}\n")
    f.write("\n")
    
    # Check for key modules
    modules_to_check = [
        'nntp',
        'pynntp', 
        'nntplib',
        'psycopg2',
        'cryptography',
        'fastapi',
        'sqlite3'
    ]
    
    f.write("Module Availability:\n")
    for module in modules_to_check:
        try:
            __import__(module)
            f.write(f"  {module}: AVAILABLE\n")
        except ImportError as e:
            f.write(f"  {module}: NOT FOUND ({e})\n")
    
    # Check for production client
    f.write("\nProduction Client Check:\n")
    try:
        sys.path.insert(0, '/workspace/src')
        from networking.production_nntp_client import ProductionNNTPClient
        f.write("  production_nntp_client: AVAILABLE\n")
        
        # Check what it imports
        import inspect
        import networking.production_nntp_client as prod
        imports = [name for name in dir(prod) if not name.startswith('_')]
        f.write(f"  Exports: {', '.join(imports[:10])}...\n")
        
    except Exception as e:
        f.write(f"  production_nntp_client: ERROR ({e})\n")
    
    # Check venv
    f.write("\nVirtual Environment:\n")
    f.write(f"  VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Not set')}\n")
    f.write(f"  Which python3: {os.popen('which python3').read().strip()}\n")
    
    # List packages in venv if it exists
    venv_site = '/workspace/venv/lib/python3.*/site-packages'
    import glob
    venv_packages = glob.glob(venv_site)
    if venv_packages:
        f.write(f"\nVenv packages directory: {venv_packages[0]}\n")
        # Check for nntp/pynntp
        import os
        if os.path.exists(venv_packages[0]):
            for item in ['nntp', 'pynntp', 'nntplib']:
                check_path = os.path.join(venv_packages[0], item)
                if os.path.exists(check_path):
                    f.write(f"  Found: {check_path}\n")

print("Check complete - see ENVIRONMENT_CHECK.txt")