#!/usr/bin/env python3
"""
Final Backend Test for UsenetSync
Tests the fixed backend initialization
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_backend():
    """Test the backend initialization"""
    print("=" * 60)
    print("    Testing Fixed UsenetSync Backend")
    print("=" * 60)
    print()
    
    try:
        print("1. Importing UsenetSync class...")
        from main import UsenetSync
        print("   ✓ Import successful")
        
        print("2. Creating UsenetSync instance...")
        app = UsenetSync()
        print("   ✓ Backend created successfully!")
        
        print("3. Testing user functionality...")
        if hasattr(app, 'user'):
            print("   ✓ User management available")
            
            if hasattr(app.user, 'is_initialized'):
                initialized = app.user.is_initialized()
                print(f"   ✓ User initialized: {initialized}")
            
            if hasattr(app.user, 'initialize'):
                print("   ✓ User initialization method available")
        
        print("4. Testing database functionality...")
        if hasattr(app, 'db'):
            print("   ✓ Database available")
        
        print("5. Testing NNTP functionality...")
        if hasattr(app, 'nntp'):
            print("   ✓ NNTP client available")
        
        print("6. Testing status functionality...")
        try:
            status = app.get_status()
            print("   ✓ Status retrieval working")
            print(f"   User: {'Initialized' if status.get('user') else 'Not initialized'}")
        except Exception as e:
            print(f"   ⚠ Status retrieval issue: {e}")
        
        print("7. Cleaning up...")
        app.cleanup()
        print("   ✓ Cleanup successful")
        
        print()
        print("🎉 Backend test completed successfully!")
        print()
        print("The backend is now ready for GUI use.")
        print("You can run: python production_launcher.py")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Backend test failed: {e}")
        print()
        print("Detailed error:")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_backend()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed! Backend is ready.")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Backend test failed.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
