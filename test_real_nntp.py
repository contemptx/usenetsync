#!/usr/bin/env python3
"""
Test NNTP connection with real Newshosting credentials
"""

import nntplib
import ssl
import json
from datetime import datetime

def test_nntp_connection():
    """Test connection to Newshosting"""
    
    print("="*60)
    print(" TESTING REAL NNTP CONNECTION TO NEWSHOSTING")
    print("="*60)
    
    # Load config
    with open('/workspace/nntp_config.json', 'r') as f:
        config = json.load(f)
    
    server_config = config['servers'][0]
    
    print(f"\n1. Connecting to {server_config['host']}:{server_config['port']}")
    print(f"   Username: {server_config['username']}")
    print(f"   SSL: {server_config['ssl']}")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect to server
        if server_config['ssl']:
            nntp = nntplib.NNTP_SSL(
                server_config['host'],
                port=server_config['port'],
                user=server_config['username'],
                password=server_config['password'],
                ssl_context=context,
                timeout=30
            )
        else:
            nntp = nntplib.NNTP(
                server_config['host'],
                port=server_config['port'],
                user=server_config['username'],
                password=server_config['password'],
                timeout=30
            )
        
        print("   ✓ Connected successfully!")
        
        # Get server info
        print("\n2. Server Information:")
        welcome = nntp.getwelcome()
        print(f"   Welcome: {welcome.decode() if isinstance(welcome, bytes) else welcome}")
        
        # Test newsgroup access
        print("\n3. Testing Newsgroup Access:")
        for group in config['default_newsgroups']:
            try:
                resp, count, first, last, name = nntp.group(group)
                print(f"   ✓ {group}: {count} articles (range: {first}-{last})")
            except Exception as e:
                print(f"   ✗ {group}: {str(e)}")
        
        # Test posting capability
        print("\n4. Testing Post Capability:")
        test_message = f"""From: test@usenetsync.local
Newsgroups: alt.binaries.test
Subject: UsenetSync Test Post - {datetime.now().isoformat()}
Message-ID: <test_{datetime.now().timestamp()}@usenetsync.local>

This is a test post from UsenetSync.
Testing NNTP connectivity.
Timestamp: {datetime.now()}
"""
        
        try:
            # Try to post (this might fail on some servers/groups)
            response = nntp.post(test_message.encode())
            print(f"   ✓ Posting capability confirmed")
            print(f"   Response: {response}")
        except nntplib.NNTPError as e:
            if "read-only" in str(e).lower():
                print(f"   ⚠ Server/group is read-only")
            else:
                print(f"   ⚠ Posting test failed: {e}")
        
        # Get server capabilities
        print("\n5. Server Capabilities:")
        try:
            resp, caps = nntp.capabilities()
            for cap in list(caps.keys())[:10]:  # Show first 10 capabilities
                print(f"   - {cap}")
        except:
            print("   ⚠ Could not retrieve capabilities")
        
        # Close connection
        nntp.quit()
        print("\n✓ Connection test complete!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {str(e)}")
        return False

def test_upload_download():
    """Test actual upload and download"""
    
    print("\n" + "="*60)
    print(" TESTING UPLOAD/DOWNLOAD FUNCTIONALITY")
    print("="*60)
    
    with open('/workspace/nntp_config.json', 'r') as f:
        config = json.load(f)
    
    server_config = config['servers'][0]
    
    try:
        # Connect
        context = ssl.create_default_context()
        nntp = nntplib.NNTP_SSL(
            server_config['host'],
            port=server_config['port'],
            user=server_config['username'],
            password=server_config['password'],
            ssl_context=context,
            timeout=30
        )
        
        print("\n1. Uploading test article...")
        
        # Create a test article
        test_data = b"This is test data for UsenetSync segment upload test."
        timestamp = datetime.now().timestamp()
        
        article = f"""From: usenetsync@test.local
Newsgroups: alt.binaries.test
Subject: [UsenetSync] Test Segment {timestamp}
Message-ID: <{timestamp}@usenetsync.local>
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64

{test_data.hex()}
"""
        
        try:
            # Post the article
            response = nntp.post(article.encode())
            message_id = f"<{timestamp}@usenetsync.local>"
            print(f"   ✓ Article posted successfully")
            print(f"   Message-ID: {message_id}")
            
            # Try to retrieve it
            print("\n2. Retrieving posted article...")
            try:
                resp, info = nntp.article(message_id)
                print(f"   ✓ Article retrieved successfully")
                print(f"   Response: {resp}")
            except Exception as e:
                print(f"   ⚠ Could not retrieve (may need propagation time): {e}")
                
        except Exception as e:
            print(f"   ✗ Upload failed: {e}")
        
        nntp.quit()
        
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    # Test connection
    if test_nntp_connection():
        # Test upload/download
        test_upload_download()
    
    print("\n" + "="*60)
    print(" TEST COMPLETE")
    print("="*60)