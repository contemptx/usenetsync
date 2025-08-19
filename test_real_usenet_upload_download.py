#!/usr/bin/env python3
"""
REAL Usenet Upload and Download Test
Tests the complete flow with actual Usenet server
"""

import sys
import os
import time
import hashlib
import uuid
from pathlib import Path

sys.path.insert(0, '/workspace/src')

from unified.networking.real_nntp_client import RealNNTPClient
from unified.networking.yenc import UnifiedYenc

# REAL credentials
SERVER = "news.newshosting.com"
PORT = 563
USER = "contemptx"
PASS = "Kia211101#"
GROUP = "alt.binaries.test"

def test_real_upload_download():
    """Test REAL upload and download to/from Usenet"""
    
    print("\n" + "=" * 80)
    print("REAL USENET UPLOAD/DOWNLOAD TEST")
    print("=" * 80)
    
    nntp = RealNNTPClient()
    yenc = UnifiedYenc()
    
    try:
        # 1. Connect
        print("\n1. Connecting to Usenet...")
        if not nntp.connect(SERVER, PORT, True, USER, PASS):
            print("   ❌ Connection failed")
            return False
        print("   ✅ Connected and authenticated")
        
        # 2. Create test data
        print("\n2. Creating test data...")
        test_data = b"This is REAL test data for Usenet!\n" * 100
        test_data += os.urandom(10000)  # Add some binary data
        test_hash = hashlib.sha256(test_data).hexdigest()
        print(f"   Data size: {len(test_data)} bytes")
        print(f"   Hash: {test_hash[:32]}...")
        
        # 3. Encode with yEnc
        print("\n3. Encoding with yEnc...")
        yenc_data = yenc.wrap_data(test_data, "test_file.dat", 1, 1)
        print(f"   Encoded size: {len(yenc_data)} bytes")
        
        # 4. Upload to Usenet
        print("\n4. Uploading to Usenet...")
        subject = f"Test Upload {uuid.uuid4().hex[:8]} yEnc (1/1)"
        
        message_id = nntp.post_article(
            subject=subject,
            body=yenc_data,
            newsgroups=[GROUP]
        )
        
        if not message_id:
            print("   ❌ Upload failed")
            return False
        
        print(f"   ✅ Uploaded with Message-ID: {message_id}")
        
        # 5. Wait for propagation
        print("\n5. Waiting for server propagation...")
        time.sleep(3)
        
        # 6. Verify it exists
        print("\n6. Verifying on server...")
        if nntp.check_article_exists(message_id):
            print("   ✅ Article exists on server")
        else:
            print("   ⚠️  Article not found (may need more time)")
        
        # 7. Download it back
        print("\n7. Downloading from Usenet...")
        result = nntp.retrieve_article(message_id)
        
        if not result:
            print("   ❌ Download failed")
            return False
        
        article_num, lines = result
        print(f"   ✅ Downloaded article #{article_num} ({len(lines)} lines)")
        
        # 8. Extract and decode yEnc
        print("\n8. Decoding yEnc data...")
        yenc_lines = []
        in_yenc = False
        
        for line in lines:
            if line.startswith('=ybegin'):
                in_yenc = True
            elif line.startswith('=yend'):
                break
            elif in_yenc and not line.startswith('=ypart'):
                yenc_lines.append(line)
        
        if not yenc_lines:
            print("   ❌ No yEnc data found")
            return False
        
        encoded = '\n'.join(yenc_lines).encode('latin-1')
        decoded = yenc.decode(encoded)
        
        print(f"   Decoded size: {len(decoded)} bytes")
        
        # 9. Verify integrity
        print("\n9. Verifying integrity...")
        decoded_hash = hashlib.sha256(decoded).hexdigest()
        
        print(f"   Original hash:  {test_hash[:32]}...")
        print(f"   Downloaded hash: {decoded_hash[:32]}...")
        
        if decoded_hash == test_hash:
            print("   ✅ DATA INTEGRITY VERIFIED - PERFECT MATCH!")
        else:
            print("   ❌ Hash mismatch")
            print(f"   Original size: {len(test_data)}, Downloaded size: {len(decoded)}")
            return False
        
        print("\n" + "=" * 80)
        print("✅ REAL USENET UPLOAD/DOWNLOAD TEST PASSED!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        nntp.disconnect()

if __name__ == "__main__":
    success = test_real_upload_download()
    sys.exit(0 if success else 1)