#!/usr/bin/env python3
"""
Setup script for UsenetSync Python dependencies
"""
import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    print("Installing Python dependencies for UsenetSync...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, 'requirements.txt')
    
    try:
        # Try to install with pip3
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file
        ])
        print("✓ Python dependencies installed successfully")
    except subprocess.CalledProcessError:
        # If that fails, try with --user flag
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user', '-r', requirements_file
            ])
            print("✓ Python dependencies installed successfully (user install)")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            print("\nPlease install manually with:")
            print(f"  pip install -r {requirements_file}")
            sys.exit(1)

def verify_pynntp():
    """Verify pynntp is installed correctly"""
    try:
        from nntp import NNTPClient
        print("✓ pynntp module verified - import successful")
        return True
    except ImportError:
        print("✗ pynntp module not found")
        print("\nTrying to install pynntp specifically...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 'pynntp'
            ])
            print("✓ pynntp installed successfully")
            return True
        except:
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--user', 'pynntp'
                ])
                print("✓ pynntp installed successfully (user install)")
                return True
            except:
                print("✗ Failed to install pynntp")
                print("\nPlease install manually with:")
                print("  pip install pynntp")
                return False

def main():
    print("=" * 60)
    print("UsenetSync Python Setup")
    print("=" * 60)
    
    # Install requirements
    install_requirements()
    
    # Verify critical pynntp module
    print("\nVerifying critical modules...")
    if not verify_pynntp():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Setup complete! Python backend is ready.")
    print("=" * 60)

if __name__ == "__main__":
    main()