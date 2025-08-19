#!/usr/bin/env python3
"""
Complete test of unified system
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, '/workspace/src')

from unified.main import UnifiedSystem
from unified.security.access_control import AccessLevel

def test():
    print("=" * 80)
    print("TESTING UNIFIED SYSTEM")
    print("=" * 80)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        print("\n1. Initializing...")
        system = UnifiedSystem()
        print("✓ System initialized")
        
        print("\n2. Creating user...")
        user = system.create_user("testuser")
        print(f"✓ User ID: {user['user_id'][:16]}...")
        
        print("\n3. Creating test files...")
        test_folder = Path(test_dir) / "data"
        test_folder.mkdir()
        
        for i in range(3):
            (test_folder / f"file{i}.txt").write_text(f"Content {i}\n" * 100)
        
        print("\n4. Indexing...")
        results = system.index_folder(str(test_folder), user['user_id'])
        print(f"✓ Indexed {results['files_indexed']} files")
        
        print("\n5. Creating share...")
        share = system.create_share(results['folder_id'], user['user_id'])
        print(f"✓ Share: {share['share_id']}")
        
        print("\n6. Verifying access...")
        assert system.verify_access(share['share_id'], user['user_id'])
        print("✓ Access verified")
        
        print("\n✓ ALL TESTS PASSED")
        return True
        
    finally:
        try:
            system.close()
        except:
            pass
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(0 if test() else 1)
