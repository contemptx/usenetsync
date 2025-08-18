#!/usr/bin/env python3
"""
Build script to bundle Python backend with PyInstaller
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required = ['pyinstaller', 'pynntp']
    missing = []
    
    for package in required:
        try:
            __import__(package if package != 'pynntp' else 'nntp')
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Installing missing packages...")
        for package in missing:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def build_executable():
    """Build the Python backend executable"""
    print("Building Python backend executable...")
    
    # Change to src directory
    src_dir = Path(__file__).parent / 'src'
    os.chdir(src_dir)
    
    # Run PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--onefile',
        '--name', 'usenetsync-backend',
        '--distpath', '../usenet-sync-app/src-tauri/resources',
        '--workpath', '../build/pyinstaller',
        '--specpath', '../build',
        'cli.py'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Build failed: {result.stderr}")
        return False
    
    print("✓ Python backend built successfully")
    return True

def main():
    print("=" * 60)
    print("Building Python Backend for UsenetSync")
    print("=" * 60)
    
    # Check and install requirements
    check_requirements()
    
    # Build executable
    if build_executable():
        print("\n✓ Build complete!")
        print("Executable location: usenet-sync-app/src-tauri/resources/usenetsync-backend[.exe]")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()