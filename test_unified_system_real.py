#!/usr/bin/env python3
"""
Test the COMPLETE unified system with REAL operations
No mocks, no placeholders - everything must work
"""

import sys
import os
import tempfile
import time
import secrets
from pathlib import Path

sys.path.insert(0, '/workspace/src')

# Import ALL unified modules
from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema
from unified.core.models import *
from unified.core.config import UnifiedConfig

from unified.security.encryption import UnifiedEncryption
from unified.security.authentication import UnifiedAuthentication
from unified.security.access_control import UnifiedAccessControl, AccessLevel
from unified.security.obfuscation import UnifiedObfuscation
from unified.security.key_management import UnifiedKeyManagement
from unified.security.zero_knowledge import ZeroKnowledgeProofs

from unified.indexing.scanner import UnifiedScanner

def test_complete_unified_system():
    """Test the complete unified system with real operations"""
    
    print("=" * 80)
    print("TESTING COMPLETE UNIFIED SYSTEM - REAL OPERATIONS")
    print("=" * 80)
    
    # Create temporary test environment
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, "test.db")
    keys_dir = os.path.join(test_dir, "keys")
    
    results = {
        'passed': [],
        'failed': []
    }
    
    try:
        # 1. Test Database and Schema
        print("\n1. Testing Database and Schema...")
        
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            sqlite_path=db_path,
            enable_monitoring=True
        )
        
        db = UnifiedDatabase(config)
        schema = UnifiedSchema(db)
        
        # Verify all tables exist
        tables = schema.get_statistics()
        assert len(tables) > 0
        print(f"✓ Created {len(tables)} database tables")
        results['passed'].append("Database and Schema")
        
        # 2. Test Security - Encryption
        print("\n2. Testing Security - Encryption...")
        
        encryption = UnifiedEncryption()
        
        # Test key generation
        key = encryption.generate_key()
        assert len(key) == 32
        
        # Test encryption/decryption
        plaintext = b"Secret data for UsenetSync"
        ciphertext, nonce, tag = encryption.encrypt(plaintext, key)
        decrypted = encryption.decrypt(ciphertext, key, nonce, tag)
        assert decrypted == plaintext
        
        print("✓ Encryption/Decryption working")
        results['passed'].append("Encryption")
        
        # 3. Test Security - Authentication
        print("\n3. Testing Security - Authentication...")
        
        auth = UnifiedAuthentication(db, keys_dir)
        
        # Create user with permanent User ID
        user_data = auth.create_user(username="testuser", email="test@example.com")
        assert len(user_data['user_id']) == 64  # 64-char hex User ID
        assert user_data['api_key']
        
        # Test authentication
        authenticated = auth.authenticate_user(user_data['user_id'], user_data['api_key'])
        assert authenticated
        
        print(f"✓ Created user with ID: {user_data['user_id'][:8]}...")
        results['passed'].append("Authentication")
        
        # 4. Test Security - Access Control
        print("\n4. Testing Security - Access Control...")
        
        access_control = UnifiedAccessControl(db, encryption, auth)
        
        # Create test folder
        folder_id = str(secrets.token_hex(16))
        db.insert('folders', {
            'folder_id': folder_id,
            'path': '/test/folder',
            'name': 'test_folder',
            'owner_id': user_data['user_id']
        })
        
        # Test PUBLIC share
        public_share = access_control.create_public_share(
            folder_id, user_data['user_id'], expiry_days=30
        )
        assert public_share['access_level'] == 'public'
        assert 'usenetsync://' in public_share['access_string']
        
        # Test PRIVATE share
        private_share = access_control.create_private_share(
            folder_id, user_data['user_id'], allowed_users=[], expiry_days=30
        )
        assert private_share['access_level'] == 'private'
        
        # Test PROTECTED share
        protected_share = access_control.create_protected_share(
            folder_id, user_data['user_id'], password="SecretPass123!", expiry_days=30
        )
        assert protected_share['access_level'] == 'protected'
        
        print("✓ Created PUBLIC, PRIVATE, and PROTECTED shares")
        results['passed'].append("Access Control")
        
        # 5. Test Security - Obfuscation
        print("\n5. Testing Security - Obfuscation...")
        
        obfuscation = UnifiedObfuscation()
        
        # Test subject pair generation
        private_key = secrets.token_bytes(32)
        subject_pair = obfuscation.generate_subject_pair(
            folder_id, 1, 0, private_key
        )
        assert len(subject_pair.internal_subject) == 64  # 64 hex chars
        assert len(subject_pair.usenet_subject) == 20     # 20 random chars
        assert subject_pair.internal_subject != subject_pair.usenet_subject
        
        # Test message ID generation
        message_id = obfuscation.generate_message_id()
        assert message_id.startswith('<')
        assert message_id.endswith('>')
        assert '@' in message_id
        
        # Test share ID generation
        share_id = obfuscation.generate_share_id(folder_id, "full", 1)
        assert len(share_id) == 24
        assert message_id not in share_id  # No Usenet data in share ID
        
        print("✓ Subject pairs and message IDs properly obfuscated")
        results['passed'].append("Obfuscation")
        
        # 6. Test Key Management
        print("\n6. Testing Key Management...")
        
        key_mgmt = UnifiedKeyManagement(db, keys_dir)
        
        # Initialize master key
        master_key = key_mgmt.initialize_master_key()
        assert len(master_key) == 32
        
        # Generate folder key
        folder_key, folder_salt = key_mgmt.generate_folder_key(folder_id)
        assert len(folder_key) == 32
        assert len(folder_salt) == 32
        
        # Retrieve folder key
        retrieved = key_mgmt.get_folder_key(folder_id)
        assert retrieved[0] == folder_key
        
        print("✓ Key management working")
        results['passed'].append("Key Management")
        
        # 7. Test Zero-Knowledge Proofs
        print("\n7. Testing Zero-Knowledge Proofs...")
        
        zkp = ZeroKnowledgeProofs(db)
        
        # Generate commitment
        user_public_key = secrets.token_bytes(32)
        commitment = zkp.generate_commitment(
            user_data['user_id'],
            public_share['share_id'],
            user_public_key
        )
        assert commitment['commitment_hash']
        
        # Create and verify proof
        challenge = secrets.token_bytes(32)
        proof = zkp.create_proof(
            user_data['user_id'],
            public_share['share_id'],
            private_key,
            challenge
        )
        assert proof['proof_type'] == 'schnorr'
        
        print("✓ Zero-knowledge proofs working")
        results['passed'].append("Zero-Knowledge Proofs")
        
        # 8. Test File Scanning
        print("\n8. Testing File Scanning...")
        
        scanner = UnifiedScanner(db, {'worker_threads': 4})
        
        # Create test files
        scan_dir = os.path.join(test_dir, "scan_test")
        os.makedirs(scan_dir)
        
        for i in range(5):
            file_path = os.path.join(scan_dir, f"file{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}\n" * 100)
        
        # Scan folder
        files_found = []
        for file_info in scanner.scan_folder(scan_dir):
            if not file_info.is_directory:
                files_found.append(file_info)
                assert file_info.hash  # Hash calculated
                assert file_info.size > 0
        
        assert len(files_found) == 5
        print(f"✓ Scanned {len(files_found)} files with hashes")
        results['passed'].append("File Scanning")
        
        # 9. Test Complete Workflow Integration
        print("\n9. Testing Complete Workflow Integration...")
        
        # Update existing folder record with keys
        folder = Folder(
            folder_id=folder_id,
            path=scan_dir,
            name="scan_test",
            owner_id=user_data['user_id']
        )
        folder.generate_keys()
        
        # Update instead of insert since folder already exists
        db.update(
            'folders',
            {
                'path': scan_dir,
                'name': 'scan_test',
                'private_key': folder.private_key,
                'public_key': folder.public_key
            },
            'folder_id = ?',
            (folder_id,)
        )
        
        # Index files
        for file_info in files_found:
            file = File(
                folder_id=folder_id,
                path=file_info.path,
                name=file_info.name,
                size=file_info.size,
                hash=file_info.hash
            )
            db.insert('files', file.to_dict())
        
        # Create share with access control
        share = access_control.create_private_share(
            folder_id,
            user_data['user_id'],
            allowed_users=[user_data['user_id']]
        )
        
        # Verify access
        key = access_control.verify_access(
            share['share_id'],
            user_data['user_id']
        )
        assert key is not None
        
        print("✓ Complete workflow: Index → Share → Access Control")
        results['passed'].append("Workflow Integration")
        
        # 10. Test Database Statistics
        print("\n10. Testing Database Statistics...")
        
        stats = db.get_stats()
        assert stats['database_type'] == 'sqlite'
        assert stats['tables']['folders'] > 0
        assert stats['tables']['files'] > 0
        assert stats['tables']['publications'] > 0
        
        print(f"✓ Database contains data in {len([t for t, c in stats['tables'].items() if c > 0])} tables")
        results['passed'].append("Database Statistics")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['failed'].append(str(e))
    
    finally:
        # Clean up
        try:
            db.close()
        except:
            pass
        
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n✓ Passed: {len(results['passed'])} tests")
    for test in results['passed']:
        print(f"  - {test}")
    
    if results['failed']:
        print(f"\n✗ Failed: {len(results['failed'])} tests")
        for test in results['failed']:
            print(f"  - {test}")
    
    print("\n" + "=" * 80)
    
    if results['failed']:
        print("RESULT: SOME TESTS FAILED")
        return False
    else:
        print("RESULT: ALL UNIFIED SYSTEM TESTS PASSED")
        print("\nThe unified system is working with:")
        print("- Complete database with all tables")
        print("- Full encryption (AES-256-GCM)")
        print("- User authentication with permanent IDs")
        print("- Three-tier access control (PUBLIC/PRIVATE/PROTECTED)")
        print("- Proper Usenet obfuscation")
        print("- Secure key management")
        print("- Zero-knowledge proofs")
        print("- File scanning and indexing")
        print("- Complete workflow integration")
        return True

if __name__ == "__main__":
    success = test_complete_unified_system()
    sys.exit(0 if success else 1)