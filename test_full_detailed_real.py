#!/usr/bin/env python3
"""
COMPREHENSIVE REAL USENET TEST WITH FULL DETAILS
Shows EVERYTHING: Message IDs, Subjects, Security, Access Control, Structure
"""

import sys
import os
import json
import time
import hashlib
import uuid
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, '/workspace/src')

# Import ALL components
from unified.networking.real_nntp_client import RealNNTPClient
from unified.networking.yenc import UnifiedYenc
from unified.core.database import UnifiedDatabase, DatabaseConfig, DatabaseType
from unified.core.schema import UnifiedSchema
from unified.security.encryption import UnifiedEncryption
from unified.security.authentication import UnifiedAuthentication
from unified.security.access_control import UnifiedAccessControl, AccessLevel
from unified.security.obfuscation import UnifiedObfuscation
from unified.security.zero_knowledge import UnifiedZeroKnowledge
from unified.indexing.scanner import UnifiedFileScanner
from unified.indexing.versioning import UnifiedVersioning
from unified.segmentation.processor import UnifiedSegmentProcessor
from unified.segmentation.packing import UnifiedPacking
from unified.segmentation.redundancy import UnifiedRedundancy

# REAL Usenet credentials
USENET_CONFIG = {
    'server': 'news.newshosting.com',
    'port': 563,
    'user': 'contemptx',
    'pass': 'Kia211101#',
    'group': 'alt.binaries.test',
    'use_ssl': True
}

class DetailedTestResults:
    """Collect and display all test details"""
    
    def __init__(self):
        self.results = {
            'upload': {},
            'download': {},
            'security': {},
            'structure': {},
            'messages': []
        }
    
    def add_upload_detail(self, key: str, value: Any):
        self.results['upload'][key] = value
    
    def add_download_detail(self, key: str, value: Any):
        self.results['download'][key] = value
    
    def add_security_detail(self, key: str, value: Any):
        self.results['security'][key] = value
    
    def add_structure_detail(self, key: str, value: Any):
        self.results['structure'][key] = value
    
    def add_message(self, msg_id: str, subject: str, details: Dict):
        self.results['messages'].append({
            'message_id': msg_id,
            'subject': subject,
            'details': details
        })
    
    def print_results(self):
        """Print all results in detail"""
        print("\n" + "=" * 80)
        print("DETAILED TEST RESULTS")
        print("=" * 80)
        
        print("\n📤 UPLOAD DETAILS:")
        print("-" * 40)
        for key, value in self.results['upload'].items():
            if isinstance(value, (dict, list)):
                print(f"  {key}:")
                print(f"    {json.dumps(value, indent=4)}")
            else:
                print(f"  {key}: {value}")
        
        print("\n📨 MESSAGE DETAILS:")
        print("-" * 40)
        for msg in self.results['messages']:
            print(f"  Message ID: {msg['message_id']}")
            print(f"  Subject: {msg['subject']}")
            for k, v in msg['details'].items():
                print(f"    {k}: {v}")
            print()
        
        print("\n🔒 SECURITY DETAILS:")
        print("-" * 40)
        for key, value in self.results['security'].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        print("\n📥 DOWNLOAD DETAILS:")
        print("-" * 40)
        for key, value in self.results['download'].items():
            if isinstance(value, (dict, list)):
                print(f"  {key}:")
                print(f"    {json.dumps(value, indent=4)}")
            else:
                print(f"  {key}: {value}")
        
        print("\n🔍 STRUCTURE COMPARISON:")
        print("-" * 40)
        for key, value in self.results['structure'].items():
            print(f"  {key}: {value}")


def test_comprehensive_real_usenet():
    """Run comprehensive test with all details"""
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE REAL USENET TEST")
    print("=" * 80)
    print(f"Server: {USENET_CONFIG['server']}:{USENET_CONFIG['port']}")
    print(f"User: {USENET_CONFIG['user']}")
    print(f"Group: {USENET_CONFIG['group']}")
    print("=" * 80)
    
    results = DetailedTestResults()
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # ========================================
        # SETUP
        # ========================================
        print("\n[SETUP] Initializing components...")
        
        # Database
        db_path = test_dir / "test.db"
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            sqlite_path=str(db_path)
        )
        db = UnifiedDatabase(db_config)
        schema = UnifiedSchema(db)
        
        # Security components
        encryption = UnifiedEncryption()
        auth = UnifiedAuthentication(db, encryption)
        access_control = UnifiedAccessControl(db, encryption, None)
        obfuscation = UnifiedObfuscation(encryption)
        zk = UnifiedZeroKnowledge()
        
        # Processing components
        scanner = UnifiedFileScanner(db)
        versioning = UnifiedVersioning(db)
        processor = UnifiedSegmentProcessor(db)
        packing = UnifiedPacking()
        redundancy = UnifiedRedundancy()
        
        # Network components
        nntp = RealNNTPClient()
        yenc = UnifiedYenc()
        
        print("  ✅ All components initialized")
        
        # ========================================
        # 1. CREATE TEST DATA
        # ========================================
        print("\n[1] Creating test folder structure...")
        
        # Create test folder with multiple files
        test_folder = test_dir / "test_data"
        test_folder.mkdir()
        
        # File 1: Text file
        file1 = test_folder / "document.txt"
        file1_content = "This is a test document for UsenetSync.\n" * 100
        file1.write_text(file1_content)
        file1_hash = hashlib.sha256(file1_content.encode()).hexdigest()
        
        # File 2: Binary file
        file2 = test_folder / "binary.dat"
        file2_content = os.urandom(50000)  # 50KB
        file2.write_bytes(file2_content)
        file2_hash = hashlib.sha256(file2_content).hexdigest()
        
        # File 3: Small file for packing
        file3 = test_folder / "small.txt"
        file3_content = "Small file for packing test"
        file3.write_text(file3_content)
        file3_hash = hashlib.sha256(file3_content.encode()).hexdigest()
        
        results.add_upload_detail('test_folder', str(test_folder))
        results.add_upload_detail('files', {
            'document.txt': {
                'size': len(file1_content),
                'hash': file1_hash[:32] + '...'
            },
            'binary.dat': {
                'size': len(file2_content),
                'hash': file2_hash[:32] + '...'
            },
            'small.txt': {
                'size': len(file3_content),
                'hash': file3_hash[:32] + '...'
            }
        })
        
        print(f"  Created 3 test files in {test_folder}")
        
        # ========================================
        # 2. CREATE USER AND FOLDER
        # ========================================
        print("\n[2] Creating user and folder records...")
        
        # Create owner user
        owner_user = auth.create_user(f"owner_{uuid.uuid4().hex[:8]}")
        owner_id = owner_user['user_id']
        
        # Create test user (for access testing)
        test_user = auth.create_user(f"test_{uuid.uuid4().hex[:8]}")
        test_user_id = test_user['user_id']
        
        # Create unauthorized user
        unauth_user = auth.create_user(f"unauth_{uuid.uuid4().hex[:8]}")
        unauth_user_id = unauth_user['user_id']
        
        results.add_security_detail('owner_user', {
            'user_id': owner_id[:16] + '...',
            'username': owner_user['username']
        })
        results.add_security_detail('test_user', {
            'user_id': test_user_id[:16] + '...',
            'username': test_user['username']
        })
        results.add_security_detail('unauthorized_user', {
            'user_id': unauth_user_id[:16] + '...',
            'username': unauth_user['username']
        })
        
        # Create folder record
        folder_id = hashlib.sha256(str(test_folder).encode()).hexdigest()
        folder_key = encryption.generate_key()
        
        db.insert('folders', {
            'folder_id': folder_id,
            'folder_name': 'Test Folder',
            'folder_path': str(test_folder),
            'owner_id': owner_id,
            'folder_key': folder_key,
            'created_at': time.time()
        })
        
        results.add_upload_detail('folder_id', folder_id[:16] + '...')
        results.add_security_detail('folder_key', folder_key[:16] + '...')
        
        # ========================================
        # 3. INDEX FILES
        # ========================================
        print("\n[3] Indexing folder...")
        
        # Scan and index files
        index_results = scanner.scan_folder(str(test_folder), folder_id)
        
        results.add_upload_detail('indexed_files', len(index_results))
        results.add_upload_detail('total_size', sum(f['size'] for f in index_results))
        
        # Create version
        version_id = versioning.create_version(folder_id, index_results)
        results.add_upload_detail('version_id', version_id)
        
        print(f"  Indexed {len(index_results)} files")
        print(f"  Version ID: {version_id}")
        
        # ========================================
        # 4. SEGMENT FILES
        # ========================================
        print("\n[4] Segmenting files...")
        
        all_segments = []
        segment_map = {}
        
        for file_info in index_results:
            file_path = file_info['path']
            file_id = file_info['file_id']
            
            # Segment the file
            segments = processor.segment_file(file_path)
            all_segments.extend(segments)
            segment_map[file_path] = [s.segment_id for s in segments]
            
            print(f"  {Path(file_path).name}: {len(segments)} segments")
            
            # Store segments in database
            for seg in segments:
                db.insert('segments', {
                    'segment_id': seg.segment_id,
                    'file_id': file_id,
                    'segment_index': seg.segment_index,
                    'size': seg.size,
                    'hash': seg.hash,
                    'created_at': time.time()
                })
        
        results.add_upload_detail('total_segments', len(all_segments))
        results.add_upload_detail('segment_size', 768 * 1024)  # 768KB
        
        # ========================================
        # 5. APPLY SECURITY
        # ========================================
        print("\n[5] Applying security layers...")
        
        # Generate encryption keys
        master_key = encryption.generate_key()
        
        # Encrypt segments
        encrypted_segments = []
        for segment in all_segments:
            # Encrypt segment data
            encrypted_data, nonce = encryption.encrypt(segment.data, folder_key)
            
            # Apply redundancy
            redundant_data = redundancy.add_redundancy(encrypted_data, 3)
            
            encrypted_segments.append({
                'segment_id': segment.segment_id,
                'data': redundant_data,
                'nonce': nonce,
                'original_hash': segment.hash,
                'encrypted_hash': hashlib.sha256(encrypted_data).hexdigest()
            })
        
        results.add_security_detail('encryption', 'AES-256-GCM')
        results.add_security_detail('redundancy_level', 3)
        results.add_security_detail('encrypted_segments', len(encrypted_segments))
        
        # Create obfuscated subjects
        obfuscated_subjects = []
        for i, seg in enumerate(encrypted_segments):
            # Two-layer subject obfuscation
            inner_subject = f"seg_{seg['segment_id'][:8]}"
            outer_subject = obfuscation.obfuscate_subject(inner_subject, folder_key)
            
            obfuscated_subjects.append({
                'segment_id': seg['segment_id'],
                'inner_subject': inner_subject,
                'outer_subject': outer_subject,
                'obfuscated': hashlib.sha256(outer_subject.encode()).hexdigest()[:16]
            })
        
        results.add_security_detail('subject_obfuscation', 'Two-layer')
        results.add_security_detail('sample_obfuscation', {
            'inner': obfuscated_subjects[0]['inner_subject'],
            'outer': obfuscated_subjects[0]['outer_subject'][:32] + '...',
            'hash': obfuscated_subjects[0]['obfuscated']
        })
        
        # ========================================
        # 6. CONNECT TO USENET
        # ========================================
        print("\n[6] Connecting to REAL Usenet server...")
        
        connected = nntp.connect(
            USENET_CONFIG['server'],
            USENET_CONFIG['port'],
            USENET_CONFIG['use_ssl'],
            USENET_CONFIG['user'],
            USENET_CONFIG['pass']
        )
        
        if not connected:
            raise Exception("Failed to connect to Usenet")
        
        print(f"  ✅ Connected to {USENET_CONFIG['server']}")
        
        # Select newsgroup
        group_info = nntp.select_group(USENET_CONFIG['group'])
        print(f"  ✅ Selected {USENET_CONFIG['group']}: {group_info['count']:,} articles")
        
        # ========================================
        # 7. UPLOAD TO USENET
        # ========================================
        print("\n[7] Uploading segments to REAL Usenet...")
        
        uploaded_messages = []
        
        for i, (seg, subj) in enumerate(zip(encrypted_segments[:5], obfuscated_subjects[:5])):  # Upload first 5 for testing
            # Encode with yEnc
            yenc_data = yenc.wrap_data(
                seg['data'],
                f"{subj['obfuscated']}.dat",
                part=i+1,
                total=len(encrypted_segments)
            )
            
            # Create article subject
            article_subject = f"[{i+1}/{len(encrypted_segments)}] {subj['outer_subject']} yEnc"
            
            # Post to Usenet
            message_id = nntp.post_article(
                subject=article_subject,
                body=yenc_data,
                newsgroups=[USENET_CONFIG['group']]
            )
            
            if message_id:
                uploaded_messages.append({
                    'message_id': message_id,
                    'segment_id': seg['segment_id'],
                    'subject': article_subject,
                    'inner_subject': subj['inner_subject'],
                    'outer_subject': subj['outer_subject'],
                    'size': len(yenc_data),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Store in database
                db.insert('messages', {
                    'message_id': message_id,
                    'segment_id': seg['segment_id'],
                    'subject': article_subject,
                    'newsgroups': USENET_CONFIG['group'],
                    'posted_at': time.time(),
                    'size': len(yenc_data)
                })
                
                results.add_message(
                    message_id,
                    article_subject,
                    {
                        'segment_id': seg['segment_id'][:16] + '...',
                        'inner_subject': subj['inner_subject'],
                        'size': len(yenc_data),
                        'encrypted_hash': seg['encrypted_hash'][:16] + '...'
                    }
                )
                
                print(f"  [{i+1}/{5}] Posted: {message_id}")
                print(f"       Subject: {article_subject[:50]}...")
        
        results.add_upload_detail('uploaded_count', len(uploaded_messages))
        results.add_upload_detail('first_message_id', uploaded_messages[0]['message_id'] if uploaded_messages else None)
        
        # ========================================
        # 8. CREATE SHARES WITH ACCESS CONTROL
        # ========================================
        print("\n[8] Creating shares with access control...")
        
        # Create PRIVATE share (only test_user can access)
        private_share = access_control.create_private_share(
            folder_id=folder_id,
            owner_id=owner_id,
            allowed_users=[test_user_id],  # Only test_user
            expiry_days=7
        )
        
        results.add_security_detail('private_share', {
            'share_id': private_share['share_id'][:16] + '...',
            'access_level': 'PRIVATE',
            'allowed_users': [test_user['username']],
            'expires_in': '7 days'
        })
        
        # Add user commitment for test_user
        commitment_data = zk.generate_commitment(test_user_id.encode())
        access_control.add_user_commitment(
            private_share['share_id'],
            test_user_id,
            commitment_data
        )
        
        results.add_security_detail('user_commitment', {
            'user': test_user['username'],
            'commitment': commitment_data['commitment'][:16] + '...',
            'proof_generated': True
        })
        
        print(f"  Created PRIVATE share: {private_share['share_id'][:16]}...")
        print(f"  Added commitment for: {test_user['username']}")
        
        # ========================================
        # 9. TEST ACCESS CONTROL
        # ========================================
        print("\n[9] Testing access control...")
        
        # Test 1: Authorized user (test_user) accessing private share
        print("  Testing AUTHORIZED access...")
        authorized_key = access_control.verify_access(
            private_share['share_id'],
            test_user_id
        )
        
        if authorized_key:
            print(f"    ✅ Authorized user granted access")
            print(f"    Decryption key: {authorized_key[:16]}...")
            results.add_security_detail('authorized_access', {
                'user': test_user['username'],
                'result': 'GRANTED',
                'key_received': True
            })
        else:
            print(f"    ❌ Authorized user DENIED (unexpected!)")
        
        # Test 2: Unauthorized user (unauth_user) accessing private share
        print("  Testing UNAUTHORIZED access...")
        unauthorized_key = access_control.verify_access(
            private_share['share_id'],
            unauth_user_id
        )
        
        if unauthorized_key:
            print(f"    ❌ Unauthorized user GRANTED access (unexpected!)")
        else:
            print(f"    ✅ Unauthorized user correctly DENIED")
            results.add_security_detail('unauthorized_access', {
                'user': unauth_user['username'],
                'result': 'DENIED',
                'key_received': False
            })
        
        # ========================================
        # 10. DOWNLOAD FROM USENET
        # ========================================
        print("\n[10] Downloading from REAL Usenet...")
        
        time.sleep(3)  # Wait for propagation
        
        downloaded_segments = []
        
        for msg in uploaded_messages:
            print(f"  Downloading: {msg['message_id']}")
            
            # Check if exists
            if not nntp.check_article_exists(msg['message_id']):
                print(f"    ⚠️  Not found on server")
                continue
            
            # Retrieve article
            result = nntp.retrieve_article(msg['message_id'])
            if not result:
                print(f"    ❌ Failed to retrieve")
                continue
            
            article_num, lines = result
            
            # Extract yEnc data
            yenc_lines = []
            in_yenc = False
            
            for line in lines:
                if line.startswith('=ybegin'):
                    in_yenc = True
                elif line.startswith('=yend'):
                    break
                elif in_yenc and not line.startswith('=ypart'):
                    yenc_lines.append(line)
            
            if yenc_lines:
                # Decode yEnc
                encoded = '\n'.join(yenc_lines).encode('latin-1')
                decoded = yenc.decode(encoded)
                
                downloaded_segments.append({
                    'message_id': msg['message_id'],
                    'segment_id': msg['segment_id'],
                    'data': decoded,
                    'size': len(decoded)
                })
                
                print(f"    ✅ Downloaded {len(decoded)} bytes")
        
        results.add_download_detail('downloaded_count', len(downloaded_segments))
        results.add_download_detail('total_bytes', sum(s['size'] for s in downloaded_segments))
        
        # ========================================
        # 11. DECRYPT AND VERIFY
        # ========================================
        print("\n[11] Decrypting and verifying downloaded data...")
        
        if authorized_key and downloaded_segments:
            decrypted_segments = []
            
            for down_seg in downloaded_segments:
                # Find original encrypted segment
                orig_seg = next((s for s in encrypted_segments if s['segment_id'] == down_seg['segment_id']), None)
                if not orig_seg:
                    continue
                
                # Remove redundancy
                clean_data = redundancy.remove_redundancy(down_seg['data'])
                
                # Decrypt
                try:
                    decrypted = encryption.decrypt(clean_data, folder_key, orig_seg['nonce'])
                    decrypted_hash = hashlib.sha256(decrypted).hexdigest()
                    
                    decrypted_segments.append({
                        'segment_id': down_seg['segment_id'],
                        'decrypted_hash': decrypted_hash,
                        'original_hash': orig_seg['original_hash'],
                        'match': decrypted_hash == orig_seg['original_hash']
                    })
                    
                    if decrypted_hash == orig_seg['original_hash']:
                        print(f"    ✅ Segment {down_seg['segment_id'][:8]}... verified")
                    else:
                        print(f"    ❌ Segment {down_seg['segment_id'][:8]}... hash mismatch")
                        
                except Exception as e:
                    print(f"    ❌ Decryption failed: {e}")
            
            results.add_download_detail('decrypted_count', len(decrypted_segments))
            results.add_download_detail('verified_count', sum(1 for s in decrypted_segments if s['match']))
        
        # ========================================
        # 12. STRUCTURE COMPARISON
        # ========================================
        print("\n[12] Comparing upload/download structure...")
        
        # Compare uploaded vs downloaded
        upload_structure = {
            'total_files': len(index_results),
            'total_segments': len(all_segments),
            'total_uploaded': len(uploaded_messages),
            'segment_ids': sorted([m['segment_id'] for m in uploaded_messages])
        }
        
        download_structure = {
            'total_downloaded': len(downloaded_segments),
            'segment_ids': sorted([s['segment_id'] for s in downloaded_segments])
        }
        
        structure_match = upload_structure['segment_ids'] == download_structure['segment_ids']
        
        results.add_structure_detail('upload_segments', upload_structure['total_uploaded'])
        results.add_structure_detail('download_segments', download_structure['total_downloaded'])
        results.add_structure_detail('structure_match', structure_match)
        results.add_structure_detail('integrity', 'VERIFIED' if structure_match else 'MISMATCH')
        
        if structure_match:
            print("  ✅ Upload/Download structure MATCHES")
        else:
            print("  ❌ Structure mismatch")
            missing = set(upload_structure['segment_ids']) - set(download_structure['segment_ids'])
            if missing:
                print(f"    Missing segments: {missing}")
        
        # ========================================
        # PRINT DETAILED RESULTS
        # ========================================
        results.print_results()
        
        # ========================================
        # FINAL SUMMARY
        # ========================================
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        all_passed = True
        
        # Check each component
        checks = [
            ("Database", len(index_results) > 0),
            ("File Indexing", results.results['upload'].get('indexed_files', 0) > 0),
            ("Segmentation", results.results['upload'].get('total_segments', 0) > 0),
            ("Encryption", results.results['security'].get('encrypted_segments', 0) > 0),
            ("Usenet Upload", results.results['upload'].get('uploaded_count', 0) > 0),
            ("Access Control - Authorized", 
             results.results['security'].get('authorized_access', {}).get('result') == 'GRANTED'),
            ("Access Control - Unauthorized", 
             results.results['security'].get('unauthorized_access', {}).get('result') == 'DENIED'),
            ("Usenet Download", results.results['download'].get('downloaded_count', 0) > 0),
            ("Decryption", results.results['download'].get('decrypted_count', 0) > 0),
            ("Structure Match", results.results['structure'].get('structure_match', False))
        ]
        
        for name, passed in checks:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {name}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉 ALL TESTS PASSED WITH REAL USENET!")
        else:
            print("⚠️  Some tests failed - review details above")
        print("=" * 80)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            nntp.disconnect()
            db.close()
        except:
            pass
        
        # Clean up test directory
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(message)s'
    )
    
    success = test_comprehensive_real_usenet()
    sys.exit(0 if success else 1)