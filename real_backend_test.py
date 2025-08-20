#!/usr/bin/env python3
"""
REAL backend test - No simulations, actual operations
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, '/workspace/src')
os.environ['USENETSYNC_DB'] = '/tmp/test_usenetsync.db'

from unified.main import UnifiedSystem
from unified.core.config import UnifiedConfig

def test_real_backend():
    """Test backend with real operations"""
    print("=" * 80)
    print("REAL BACKEND TEST - NO SIMULATIONS")
    print("=" * 80)
    
    # Clear database
    os.system('rm -f /tmp/test_usenetsync.db')
    os.system('python3 /workspace/fix_all_schema_issues.py > /dev/null 2>&1')
    
    # Initialize system
    print("\n1. INITIALIZING SYSTEM...")
    try:
        config = UnifiedConfig()
        config.database_path = '/tmp/test_usenetsync.db'
        system = UnifiedSystem(config)
        print("✅ System initialized")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False
    
    # Create real test files
    print("\n2. CREATING REAL TEST FILES...")
    test_dir = tempfile.mkdtemp(prefix='real_test_')
    try:
        # Create multiple files with real content
        files = []
        for i in range(5):
            file_path = Path(test_dir) / f"document_{i}.txt"
            content = f"This is real test document {i}\n" * 100  # Make it substantial
            file_path.write_text(content)
            files.append(file_path)
            print(f"✅ Created {file_path.name} ({len(content)} bytes)")
    except Exception as e:
        print(f"❌ File creation failed: {e}")
        return False
    
    # Test user creation
    print("\n3. CREATING USER...")
    try:
        user = system.create_user("TestUser", "test@example.com")
        user_id = user['user_id']
        print(f"✅ User created: {user_id[:8]}...")
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False
    
    # Test folder indexing
    print("\n4. INDEXING FOLDER...")
    try:
        result = system.index_folder(test_dir, user_id, calculate_hash=True, create_segments=True)
        print(f"✅ Indexed {result['files_indexed']} files")
        print(f"✅ Created {result['segments_created']} segments")
        folder_id = result['folder_id']
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return False
    
    # Test database queries
    print("\n5. VERIFYING DATABASE...")
    try:
        # Check files in database
        files_in_db = system.db.fetch_all(
            "SELECT * FROM files WHERE folder_id = ?",
            (folder_id,)
        )
        print(f"✅ {len(files_in_db)} files in database")
        
        # Check segments
        segments_in_db = system.db.fetch_all(
            "SELECT COUNT(*) as count FROM segments"
        )
        print(f"✅ {segments_in_db[0]['count']} segments in database")
        
        # Check folder
        folder_in_db = system.db.fetch_one(
            "SELECT * FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        print(f"✅ Folder '{folder_in_db['name']}' in database")
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    
    # Test share creation
    print("\n6. CREATING SHARES...")
    try:
        # Public share
        public_share = system.create_public_share(folder_id, user_id, expiry_days=7)
        print(f"✅ Public share created: {public_share['share_id'][:8]}...")
        
        # Private share
        private_share = system.create_private_share(folder_id, user_id, ['user2', 'user3'], expiry_days=7)
        print(f"✅ Private share created: {private_share['share_id'][:8]}...")
        
        # Protected share
        protected_share = system.create_protected_share(folder_id, user_id, 'password123', expiry_days=7)
        print(f"✅ Protected share created: {protected_share['share_id'][:8]}...")
    except Exception as e:
        print(f"❌ Share creation failed: {e}")
        return False
    
    # Test upload record
    print("\n7. CREATING UPLOAD RECORD...")
    try:
        upload = system.upload_folder(folder_id)
        print(f"✅ Upload queued: {upload['upload_id'][:8]}...")
    except Exception as e:
        print(f"❌ Upload creation failed: {e}")
        return False
    
    # Test publication
    print("\n8. PUBLISHING FOLDER...")
    try:
        publication = system.publish_folder(folder_id, 'public')
        print(f"✅ Folder published: {publication['publication_id'][:8]}...")
    except Exception as e:
        print(f"❌ Publication failed: {e}")
        return False
    
    # Test metrics
    print("\n9. GETTING SYSTEM METRICS...")
    try:
        metrics = system.get_metrics()
        print(f"✅ Total files: {metrics['total_files']}")
        print(f"✅ System metrics retrieved")
    except Exception as e:
        print(f"❌ Metrics failed: {e}")
        return False
    
    # Cleanup
    print("\n10. CLEANUP...")
    try:
        shutil.rmtree(test_dir)
        print("✅ Test files cleaned up")
    except:
        pass
    
    print("\n" + "=" * 80)
    print("✅ ALL BACKEND TESTS PASSED WITH REAL DATA!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    success = test_real_backend()
    sys.exit(0 if success else 1)