#!/usr/bin/env python3
"""Test NNTP connection with real credentials"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networking.production_nntp_client import ProductionNNTPClient
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_real_connection():
    """Test connection with real Newshosting credentials"""
    print("\n=== Testing Real NNTP Connection ===")
    
    # Real credentials
    client = ProductionNNTPClient(
        host="news.newshosting.com",
        port=563,
        username="contemptx",
        password="Kia211101#",
        use_ssl=True,
        max_connections=2,  # Start small for testing
        timeout=30
    )
    
    print("✓ Client initialized")
    
    # Test posting a small message
    test_subject = f"Test_{int(time.time())}"
    test_data = b"This is a test message from UsenetSync unification testing"
    
    print(f"\nPosting test article with subject: {test_subject}")
    success, response = client.post_data(
        subject=test_subject,
        data=test_data,
        newsgroup="alt.binaries.test",
        from_user="test@usenetsync.com"
    )
    
    if success:
        print(f"✓ Successfully posted article")
        print(f"  Response: {response}")
        
        # Get stats
        stats = client.connection_pool.get_stats()
        print(f"\nConnection Pool Stats:")
        print(f"  Posts successful: {stats['posts_successful']}")
        print(f"  Posts failed: {stats['posts_failed']}")
        print(f"  Connections created: {stats['connections_created']}")
        print(f"  Pool size: {stats['pool_size']}")
        
        return True
    else:
        print(f"✗ Failed to post article: {response}")
        return False

if __name__ == "__main__":
    try:
        if test_real_connection():
            print("\n✓ NNTP connection test PASSED")
            sys.exit(0)
        else:
            print("\n✗ NNTP connection test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)