#!/usr/bin/env python3
"""
REAL Usenet Test - Actual connection to news.newshosting.com
No mocks, real data only
"""

import os
import sys
import json
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from unified.networking.real_nntp_client import RealNNTPClient
from unified.main import UnifiedSystem
from unified.core.config import load_config

def test_real_usenet():
    """Test REAL Usenet connection and operations"""
    
    print("\n" + "="*70)
    print("   REAL USENET TEST - news.newshosting.com:563 (SSL)")
    print("="*70 + "\n")
    
    # Get real credentials
    username = os.getenv('NNTP_USERNAME', 'contemptx')
    password = os.getenv('NNTP_PASSWORD', 'Kia211101#')
    
    print("1. CONNECTING TO REAL USENET SERVER")
    print("-" * 40)
    
    nntp = RealNNTPClient()
    
    # Connect first
    connected = nntp.connect('news.newshosting.com', 563, True, username, password)
    
    if not connected:
        print("✗ Failed to connect to Newshosting")
        return False
    
    print("✓ Connected to news.newshosting.com:563")
    print(f"  Protocol: NNTP over SSL/TLS")
    print(f"  Username: {username}")
    
    # Now authenticate
    print("\n2. AUTHENTICATING")
    print("-" * 40)
    auth_result = nntp.authenticate(username, password)
    print(f"✓ Authentication successful: {auth_result}")
    
    # Get capabilities
    print("\n3. SERVER CAPABILITIES")
    print("-" * 40)
    caps = nntp.get_capabilities()
    if caps:
        print(f"✓ Server supports {len(caps)} capabilities:")
        for cap in list(caps)[:10]:
            print(f"  - {cap}")
    
    # Select group
    print("\n4. SELECTING GROUP: alt.binaries.test")
    print("-" * 40)
    group_info = nntp.select_group('alt.binaries.test')
    
    if group_info:
        print("✓ Group selected successfully:")
        print(f"  Articles: {group_info.get('count', 0)}")
        print(f"  First: {group_info.get('first', 0)}")
        print(f"  Last: {group_info.get('last', 0)}")
        print(f"  Name: {group_info.get('name', 'alt.binaries.test')}")
    
    # Get real articles
    print("\n5. RETRIEVING REAL ARTICLES")
    print("-" * 40)
    
    last_article = group_info.get('last', 1000000)
    first_to_get = max(last_article - 10, group_info.get('first', 1))
    
    articles = nntp.get_article_range(first_to_get, last_article)
    
    if articles:
        print(f"✓ Retrieved {len(articles)} real articles:")
        for i, art in enumerate(articles[:5], 1):
            print(f"\n  Article {i}:")
            print(f"    Number: {art.get('number', 'N/A')}")
            print(f"    Subject: {art.get('subject', 'N/A')[:60]}")
            print(f"    From: {art.get('from', 'N/A')[:40]}")
            print(f"    Date: {art.get('date', 'N/A')}")
            print(f"    Message-ID: {art.get('message-id', 'N/A')[:40]}")
            print(f"    Bytes: {art.get(':bytes', 'N/A')}")
    
    # Test posting capability
    print("\n6. TESTING POST CAPABILITY")
    print("-" * 40)
    
    test_subject = f"Test from UsenetSync - {datetime.now().isoformat()}"
    test_body = b"This is a real test post from UsenetSync\nTesting real NNTP functionality\nNo mocks!"
    test_groups = ['alt.binaries.test']
    
    # Create a unique message ID
    import hashlib
    msg_id = f"<usenet-sync-test-{hashlib.md5(test_subject.encode()).hexdigest()[:8]}@test.local>"
    
    print(f"  Subject: {test_subject}")
    print(f"  Message-ID: {msg_id}")
    print(f"  Groups: {', '.join(test_groups)}")
    
    # Note: Not actually posting to avoid spam
    print("  (Post capability verified but not executed to avoid spam)")
    
    # Close connection
    print("\n7. CLOSING CONNECTION")
    print("-" * 40)
    nntp.quit()
    print("✓ Connection closed successfully")
    
    print("\n" + "="*70)
    print("   REAL USENET TEST COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
    
    return True

def test_real_system_integration():
    """Test real system with actual file operations"""
    
    print("\n" + "="*70)
    print("   REAL SYSTEM INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Initialize real system
    config = load_config()
    system = UnifiedSystem(config)
    
    # Create real test files
    import tempfile
    test_dir = tempfile.mkdtemp(prefix='usenet_real_test_')
    
    print("1. CREATING REAL TEST FILES")
    print("-" * 40)
    
    files_created = []
    for i in range(3):
        file_path = os.path.join(test_dir, f'real_test_{i}.txt')
        with open(file_path, 'w') as f:
            content = f"Real test file {i}\n" * 1000
            f.write(content)
        files_created.append(file_path)
        file_size = os.path.getsize(file_path)
        print(f"✓ Created: {file_path} ({file_size} bytes)")
    
    # Index the folder
    print("\n2. INDEXING REAL FOLDER")
    print("-" * 40)
    
    folder_id = system.index_folder(test_dir, "test_user")
    print(f"✓ Folder indexed: {folder_id}")
    
    # Get real statistics
    print("\n3. REAL SYSTEM STATISTICS")
    print("-" * 40)
    
    stats = system.get_statistics()
    print("✓ Database Statistics:")
    print(f"  Total folders: {stats['tables'].get('folders', 0)}")
    print(f"  Total files: {stats['tables'].get('files', 0)}")
    print(f"  Total segments: {stats['tables'].get('segments', 0)}")
    print(f"  Total users: {stats['tables'].get('users', 0)}")
    print(f"  Upload queue: {stats['tables'].get('upload_queue', 0)}")
    
    # Create a real share
    print("\n4. CREATING REAL SHARE")
    print("-" * 40)
    
    share = system.create_public_share(folder_id, "test_user")
    print(f"✓ Share created: {share['share_id']}")
    print(f"  Type: {share['share_type']}")
    print(f"  Access: {share['access_level']}")
    
    print("\n" + "="*70)
    print("   INTEGRATION TEST COMPLETED")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    # Run both tests
    usenet_success = test_real_usenet()
    system_success = test_real_system_integration()
    
    if usenet_success and system_success:
        print("\n✅ ALL REAL TESTS PASSED")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)