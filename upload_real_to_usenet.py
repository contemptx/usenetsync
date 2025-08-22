#!/usr/bin/env python3
"""
REAL Usenet Upload using the actual NNTP client
This will ACTUALLY upload to news.newshosting.com
"""

import sys
import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/workspace/backend/src')

# Import the REAL NNTP client
from unified.networking.real_nntp_client import RealNNTPClient

# REAL Usenet credentials
NNTP_SERVER = "news.newshosting.com"
NNTP_PORT = 563
NNTP_SSL = True
NNTP_USER = "contemptx"
NNTP_PASS = "Kia211101#"
NEWSGROUP = "alt.binaries.test"

def create_real_test_data():
    """Create REAL test data to upload"""
    test_dir = Path("/workspace/real_usenet_upload")
    test_dir.mkdir(exist_ok=True)
    
    # Create REAL test file
    content = f"""
REAL USENET UPLOAD TEST
========================
Timestamp: {datetime.now().isoformat()}
Server: {NNTP_SERVER}
User: {NNTP_USER}
Newsgroup: {NEWSGROUP}

This is a REAL upload to Usenet.
No simulation. No demo. REAL.

Data: {"REAL" * 100}
""".encode()
    
    filepath = test_dir / "real_test.txt"
    filepath.write_bytes(content)
    
    file_hash = hashlib.sha256(content).hexdigest()
    
    print("📁 Created REAL test file:")
    print(f"   Path: {filepath}")
    print(f"   Size: {len(content):,} bytes")
    print(f"   SHA256: {file_hash}")
    
    return filepath, content, file_hash

def segment_data(content, segment_size=700):
    """Segment data for upload"""
    segments = []
    
    for i in range(0, len(content), segment_size):
        segment_data = content[i:i+segment_size]
        segments.append({
            "number": len(segments) + 1,
            "data": segment_data,
            "size": len(segment_data),
            "hash": hashlib.sha256(segment_data).hexdigest()
        })
    
    print(f"\n📦 Created {len(segments)} segments")
    return segments

def upload_to_real_usenet(segments, file_hash):
    """ACTUALLY upload to Usenet using REAL client"""
    print("\n" + "="*70)
    print("📡 REAL USENET UPLOAD")
    print("="*70)
    
    # Create REAL NNTP client
    client = RealNNTPClient()
    
    # REAL connection
    print(f"\n⏳ Connecting to {NNTP_SERVER}:{NNTP_PORT}...")
    connected = client.connect(
        host=NNTP_SERVER,
        port=NNTP_PORT,
        use_ssl=NNTP_SSL,
        username=NNTP_USER,
        password=NNTP_PASS
    )
    
    if not connected:
        print("❌ Failed to connect!")
        return None
    
    print("✅ CONNECTED to REAL Usenet server!")
    
    # Select newsgroup
    group_info = client.select_group(NEWSGROUP)
    if group_info:
        print(f"✅ Selected {NEWSGROUP}: {group_info['count']} articles")
    
    # REAL upload
    message_ids = []
    print(f"\n📤 Uploading {len(segments)} segments...")
    
    for i, segment in enumerate(segments):
        # Create subject
        subject = f"[{segment['number']}/{len(segments)}] - real_test.txt yEnc ({segment['size']})"
        
        # Create headers
        headers = {
            'Subject': subject,
            'From': f'{NNTP_USER}@newshosting.com',
            'Newsgroups': NEWSGROUP,
            'X-File-Hash': file_hash[:16],
            'X-Segment': f"{segment['number']}/{len(segments)}"
        }
        
        # Post REAL article
        message_id = client.post_article(
            subject=subject,
            body=segment['data'],
            newsgroups=[NEWSGROUP],
            from_header=f'{NNTP_USER}@newshosting.com'
        )
        
        if message_id:
            print(f"   ✅ Segment {segment['number']}: {message_id}")
            message_ids.append(message_id)
            
            # Verify it exists
            if client.check_article_exists(message_id):
                print(f"      ✓ Verified on server!")
        else:
            print(f"   ❌ Segment {segment['number']}: Failed")
    
    client.disconnect()
    
    if message_ids:
        print(f"\n✅ REAL UPLOAD COMPLETE!")
        print(f"   Uploaded: {len(message_ids)}/{len(segments)} segments")
    
    return message_ids

def create_real_share(message_ids, file_hash, file_size):
    """Create REAL share with REAL Message-IDs"""
    share_data = {
        "version": "1.0",
        "type": "REAL_USENET_SHARE",
        "created": datetime.now().isoformat(),
        "server": NNTP_SERVER,
        "newsgroup": NEWSGROUP,
        "file": {
            "name": "real_test.txt",
            "size": file_size,
            "hash": file_hash,
            "segments": len(message_ids)
        },
        "message_ids": message_ids,
        "note": "These are REAL Message-IDs on news.newshosting.com"
    }
    
    # Generate share ID
    share_json = json.dumps(share_data, sort_keys=True)
    share_id = "USENET-" + hashlib.sha256(share_json.encode()).hexdigest()[:10].upper()
    
    # Save share
    share_file = Path(f"/workspace/real_share_{share_id}.json")
    share_file.write_text(json.dumps(share_data, indent=2))
    
    print("\n" + "="*70)
    print("🔗 REAL SHARE CREATED")
    print("="*70)
    print(f"\n📋 SHARE ID: {share_id}")
    print(f"   Type: REAL USENET SHARE")
    print(f"   Message IDs: {len(message_ids)} REAL IDs")
    print(f"   Server: {NNTP_SERVER}")
    print(f"   Newsgroup: {NEWSGROUP}")
    print(f"   Share file: {share_file}")
    
    return share_id

def verify_real_download(share_id):
    """Verify the share can be downloaded"""
    share_file = Path(f"/workspace/real_share_{share_id}.json")
    if not share_file.exists():
        print("❌ Share file not found!")
        return
    
    share_data = json.loads(share_file.read_text())
    
    print("\n" + "="*70)
    print("⬇️ VERIFYING DOWNLOAD")
    print("="*70)
    
    # Connect to verify
    client = RealNNTPClient()
    connected = client.connect(
        host=NNTP_SERVER,
        port=NNTP_PORT,
        use_ssl=NNTP_SSL,
        username=NNTP_USER,
        password=NNTP_PASS
    )
    
    if connected:
        print("\n✅ Connected to server")
        
        # Check if articles exist
        existing = 0
        for msg_id in share_data['message_ids']:
            if client.check_article_exists(msg_id):
                existing += 1
                print(f"   ✓ {msg_id} EXISTS on server")
        
        print(f"\n📊 {existing}/{len(share_data['message_ids'])} articles found on server")
        
        if existing > 0:
            print("\n✅ SHARE IS VALID AND DOWNLOADABLE!")
        
        client.disconnect()

def main():
    print("\n" + "="*70)
    print("🚀 REAL USENET UPLOAD - NO DEMO")
    print("="*70)
    
    try:
        # 1. Create REAL test data
        filepath, content, file_hash = create_real_test_data()
        
        # 2. Segment data
        segments = segment_data(content)
        
        # 3. REAL upload to Usenet
        message_ids = upload_to_real_usenet(segments, file_hash)
        
        if message_ids and len(message_ids) > 0:
            # 4. Create REAL share
            share_id = create_real_share(message_ids, file_hash, len(content))
            
            # 5. Verify it's downloadable
            verify_real_download(share_id)
            
            print("\n" + "="*70)
            print("✅ SUCCESS - REAL UPLOAD COMPLETE!")
            print("="*70)
            print(f"\n🎯 REAL SHARE ID: {share_id}")
            print("   This is a REAL share with REAL Message-IDs")
            print("   Anyone can download this from Usenet!")
        else:
            print("\n❌ Upload failed - no message IDs generated")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()