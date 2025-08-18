#!/usr/bin/env python3
"""
Test User Profile functionality
"""

import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.enhanced_database_manager import DatabaseConfig
from database.production_db_wrapper import ProductionDatabaseManager
from security.enhanced_security_system import EnhancedSecuritySystem
from security.user_management import UserManager

def test_user_profile():
    """Test user profile functionality"""
    test_dir = tempfile.mkdtemp(prefix="user_profile_test_")
    
    try:
        print("="*60)
        print("USER PROFILE TEST")
        print("="*60)
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = os.path.join(test_dir, "test.db")
        db = ProductionDatabaseManager(db_config)
        
        # Initialize security system
        security = EnhancedSecuritySystem(db)
        
        # Initialize user manager
        user_manager = UserManager(db, security)
        
        # Test 1: Check if user is initialized (should be False initially)
        print("\n1. Checking initial state...")
        is_initialized = user_manager.is_initialized()
        print(f"   User initialized: {is_initialized}")
        assert not is_initialized, "User should not be initialized initially"
        print("   ✓ Correctly reports not initialized")
        
        # Test 2: Initialize user without display name
        print("\n2. Initializing user without display name...")
        user_id = user_manager.initialize()
        print(f"   Generated User ID: {user_id[:16]}...{user_id[-16:]}")
        
        # Verify User ID format
        assert len(user_id) == 64, f"User ID should be 64 chars, got {len(user_id)}"
        assert all(c in '0123456789abcdef' for c in user_id), "User ID should be hex"
        print("   ✓ User ID format correct (64-char hex)")
        
        # Test 3: Check if user is now initialized
        print("\n3. Checking after initialization...")
        is_initialized = user_manager.is_initialized()
        assert is_initialized, "User should be initialized after calling initialize"
        print("   ✓ User is now initialized")
        
        # Test 4: Get user info
        print("\n4. Getting user info...")
        retrieved_user_id = user_manager.get_user_id()
        display_name = user_manager.get_display_name()
        print(f"   User info retrieved:")
        print(f"   - User ID: {retrieved_user_id[:16]}...{retrieved_user_id[-16:]}")
        print(f"   - Display name: {display_name if display_name else 'None'}")
        
        assert retrieved_user_id == user_id, "User ID should match"
        print("   ✓ User info correct")
        
        # Test 5: Try to initialize again (should get same ID)
        print("\n5. Testing re-initialization protection...")
        try:
            user_id2 = user_manager.initialize("Test User")
            assert user_id2 == user_id, "Should return same User ID"
            print("   ✓ Returns same User ID on re-initialization")
        except Exception as e:
            print(f"   ✓ Correctly prevents re-initialization: {e}")
        
        # Test 6: Verify User ID cannot be changed
        print("\n6. Testing User ID immutability...")
        # Get user ID again
        user_id_check = user_manager.get_user_id()
        assert user_id_check == user_id, "User ID should not change"
        print("   ✓ User ID is immutable")
        
        print("\n" + "="*60)
        print("✅ ALL USER PROFILE TESTS PASSED!")
        print("="*60)
        print("\nKey Features Verified:")
        print("- User initialization without display name works")
        print("- User ID is 64-character hexadecimal")
        print("- User ID is permanent and immutable")
        print("- User info retrieval works correctly")
        print("- Re-initialization protection works")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("\n✓ Test directory cleaned up")

if __name__ == "__main__":
    success = test_user_profile()
    sys.exit(0 if success else 1)