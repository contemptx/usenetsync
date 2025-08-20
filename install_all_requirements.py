#!/usr/bin/env python3
"""
Install all required modules for UsenetSync
Ensures nothing is skipped
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_module(module_name):
    """Check if a module is installed"""
    try:
        if module_name == 'pynntp':
            # pynntp imports as nntp
            __import__('nntp')
        elif module_name == 'psycopg2-binary':
            __import__('psycopg2')
        else:
            __import__(module_name.replace('-', '_').split('==')[0])
        return True
    except ImportError:
        return False

def main():
    print("=" * 80)
    print("USENETSYNC REQUIREMENTS INSTALLATION")
    print("=" * 80)
    
    # Critical modules that MUST be installed
    critical_modules = {
        'psycopg2-binary': 'PostgreSQL database adapter (REQUIRED for production)',
        'pynntp': 'NNTP client for Usenet (CRITICAL for core functionality)',
        'cryptography': 'Encryption library (REQUIRED for security)',
        'PyNaCl': 'Ed25519 key support (REQUIRED for user keys)',
        'fastapi': 'API framework (REQUIRED for backend)',
        'redis': 'Caching system (REQUIRED for performance)',
    }
    
    print("\n📋 Checking critical modules...")
    missing = []
    
    for module, description in critical_modules.items():
        installed = check_module(module)
        if installed:
            print(f"✅ {module}: {description}")
        else:
            print(f"❌ {module}: {description} - NOT INSTALLED")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ MISSING CRITICAL MODULES: {', '.join(missing)}")
        print("\n🔧 Installing missing modules...")
        
        for module in missing:
            print(f"\nInstalling {module}...")
            success, out, err = run_command(f"{sys.executable} -m pip install {module}")
            if success:
                print(f"✅ {module} installed successfully")
            else:
                print(f"❌ Failed to install {module}")
                print(f"   Error: {err}")
    
    # Install from requirements file
    print("\n📦 Installing all requirements from requirements_complete.txt...")
    req_file = os.path.join(os.path.dirname(__file__), 'requirements_complete.txt')
    
    if os.path.exists(req_file):
        success, out, err = run_command(f"{sys.executable} -m pip install -r {req_file}")
        if success:
            print("✅ All requirements installed successfully")
        else:
            print("❌ Some requirements failed to install")
            print(f"   Error: {err}")
    else:
        print(f"❌ requirements_complete.txt not found at {req_file}")
    
    # Final verification
    print("\n🔍 Final verification...")
    all_good = True
    
    for module in critical_modules:
        if not check_module(module):
            print(f"❌ {module} still not working")
            all_good = False
    
    if all_good:
        print("\n✅ ALL CRITICAL MODULES ARE INSTALLED AND WORKING!")
        print("\n🎉 UsenetSync is ready to run with full functionality:")
        print("   - PostgreSQL support ✅")
        print("   - Usenet/NNTP support ✅")
        print("   - Encryption support ✅")
        print("   - API backend support ✅")
    else:
        print("\n❌ Some modules are still missing.")
        print("Please install them manually:")
        print("   pip install psycopg2-binary")
        print("   pip install pynntp")
        print("   pip install -r requirements_complete.txt")

if __name__ == '__main__':
    main()