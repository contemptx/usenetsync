#!/usr/bin/env python3
"""
Retrieve the segments we uploaded earlier to verify propagation
"""

import os
import sys
import base64
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from unified.networking.real_nntp_client import RealNNTPClient

print("="*80)
print("RETRIEVING PREVIOUSLY UPLOADED SEGMENTS FROM USENET")
print("="*80)

# Message IDs from our previous upload
uploaded_message_ids = [
    "<zqjdtb4yc872awyc@ngPost.com>",
    "<z1ux2nbb82spjvr2@ngPost.com>",
    "<scdbo2ffokmz5g6s@ngPost.com>",
    "<8czj1happ28kv8kt@ngPost.com>",
    "<ouiu7k6sbi6fr62e@ngPost.com>",
    "<ml6i0venxn6dgj1o@ngPost.com>"
]

print(f"\nMessage IDs to retrieve: {len(uploaded_message_ids)}")
for msg_id in uploaded_message_ids:
    print(f"  • {msg_id}")

# Connect to Usenet
print("\nConnecting to news.newshosting.com...")
nntp_client = RealNNTPClient()

connected = nntp_client.connect(
    os.getenv('NNTP_HOST', 'news.newshosting.com'),
    int(os.getenv('NNTP_PORT', '563')),
    os.getenv('NNTP_SSL', 'true').lower() == 'true',
    os.getenv('NNTP_USERNAME', 'contemptx'),
    os.getenv('NNTP_PASSWORD', 'Kia211101#')
)

if not connected:
    print("❌ Failed to connect to Usenet")
    sys.exit(1)

print(f"✓ Connected to {os.getenv('NNTP_HOST', 'news.newshosting.com')}")

# Select newsgroup
group_info = nntp_client.select_group(os.getenv('NNTP_GROUP', 'alt.binaries.test'))
print(f"✓ Selected {os.getenv('NNTP_GROUP', 'alt.binaries.test')}")
print(f"  Articles in group: {group_info['count']:,}")

# Try to retrieve each segment
print("\n" + "="*80)
print("RETRIEVING SEGMENTS")
print("="*80)

retrieved_count = 0
retrieved_segments = []

for i, message_id in enumerate(uploaded_message_ids):
    print(f"\n{i+1}. Retrieving: {message_id}")
    print("-"*60)
    
    try:
        # Use the raw connection for article retrieval
        if hasattr(nntp_client, 'connection') and nntp_client.connection:
            # Try different methods to retrieve
            
            # Method 1: Direct article command
            try:
                article_resp = nntp_client.connection.article(message_id)
                
                if article_resp and len(article_resp) > 0:
                    response_code = article_resp[0]
                    
                    if response_code == 220:  # Article retrieved
                        print(f"  ✅ ARTICLE FOUND! (Response: {response_code})")
                        retrieved_count += 1
                        
                        # Parse the article
                        if len(article_resp) > 1:
                            # Headers might be in article_resp[1]
                            headers = article_resp[1] if len(article_resp) > 1 else {}
                            body = article_resp[2] if len(article_resp) > 2 else []
                            
                            # Show headers
                            print("\n  Headers:")
                            if hasattr(headers, 'items'):
                                for key, value in list(headers.items())[:5]:
                                    print(f"    {key}: {value[:80] if len(str(value)) > 80 else value}")
                            
                            # Extract segment data from body
                            if body:
                                print(f"\n  Body: {len(body)} lines")
                                
                                # Look for our segment markers
                                in_segment = False
                                segment_data = []
                                segment_info = {}
                                
                                for line in body:
                                    if isinstance(line, bytes):
                                        line = line.decode('utf-8', errors='replace')
                                    
                                    if 'BEGIN USENETSYNC SEGMENT' in line:
                                        in_segment = True
                                        continue
                                    elif 'END USENETSYNC SEGMENT' in line:
                                        break
                                    elif in_segment:
                                        # Parse metadata
                                        if line.startswith('Segment-ID:'):
                                            segment_info['id'] = line.split(':', 1)[1].strip()
                                        elif line.startswith('Size:'):
                                            segment_info['size'] = line.split(':', 1)[1].strip()
                                        elif line.startswith('Hash:'):
                                            segment_info['hash'] = line.split(':', 1)[1].strip()
                                        elif line.startswith('Index:'):
                                            segment_info['index'] = line.split(':', 1)[1].strip()
                                        elif line.strip() and not line.startswith(('File-ID:', 'Folder-ID:', 'Encrypted:', 'Owner:')):
                                            # This is the base64 data
                                            segment_data.append(line.strip())
                                
                                if segment_info:
                                    print("\n  Segment Info:")
                                    for key, value in segment_info.items():
                                        print(f"    {key}: {value}")
                                
                                if segment_data:
                                    # Decode the base64 data
                                    try:
                                        encoded = ''.join(segment_data)
                                        decoded = base64.b64decode(encoded)
                                        print(f"\n  ✓ Decoded segment data: {len(decoded)} bytes")
                                        
                                        retrieved_segments.append({
                                            'message_id': message_id,
                                            'info': segment_info,
                                            'data_size': len(decoded)
                                        })
                                    except Exception as e:
                                        print(f"  ⚠️ Could not decode base64: {e}")
                    
                    elif response_code == 430:
                        print(f"  ❌ Article not found (430)")
                    elif response_code == 423:
                        print(f"  ❌ No such article number (423)")
                    else:
                        print(f"  ⚠️ Unexpected response: {response_code}")
                else:
                    print(f"  ❌ No response received")
                    
            except Exception as e:
                print(f"  ❌ Error with article command: {e}")
                
                # Method 2: Try HEAD command first
                try:
                    print("\n  Trying HEAD command...")
                    head_resp = nntp_client.connection.head(message_id)
                    if head_resp and head_resp[0] == 221:
                        print(f"    ✓ Headers found! Article exists")
                        
                        # Now try BODY
                        print("    Trying BODY command...")
                        body_resp = nntp_client.connection.body(message_id)
                        if body_resp and body_resp[0] == 222:
                            print(f"    ✓ Body retrieved: {len(body_resp[1])} lines")
                            retrieved_count += 1
                    else:
                        print(f"    ❌ HEAD failed: {head_resp[0] if head_resp else 'No response'}")
                except Exception as e2:
                    print(f"    ❌ HEAD/BODY failed: {e2}")
                
                # Method 3: Try STAT to check existence
                try:
                    print("\n  Trying STAT command...")
                    stat_resp = nntp_client.connection.stat(message_id)
                    if stat_resp and stat_resp[0] == 223:
                        print(f"    ✓ Article exists! (STAT successful)")
                        # Article exists but we couldn't retrieve it
                    else:
                        print(f"    ❌ STAT failed: {stat_resp[0] if stat_resp else 'No response'}")
                except Exception as e3:
                    print(f"    ❌ STAT failed: {e3}")
                    
    except Exception as e:
        print(f"  ❌ General error: {e}")

# Summary
print("\n" + "="*80)
print("RETRIEVAL SUMMARY")
print("="*80)

print(f"\n📊 Results:")
print(f"  • Total segments uploaded: {len(uploaded_message_ids)}")
print(f"  • Successfully retrieved: {retrieved_count}")
print(f"  • Failed to retrieve: {len(uploaded_message_ids) - retrieved_count}")

if retrieved_segments:
    print(f"\n✅ Retrieved Segments:")
    for seg in retrieved_segments:
        print(f"  • {seg['message_id']}")
        if 'info' in seg and seg['info']:
            print(f"    - ID: {seg['info'].get('id', 'unknown')}")
            print(f"    - Size: {seg['data_size']} bytes decoded")

if retrieved_count == 0:
    print("\n⚠️ Note: Articles may still be propagating.")
    print("  Usenet propagation can take anywhere from minutes to hours.")
    print("  Articles are typically available faster within the same server network.")
else:
    print(f"\n✅ Successfully retrieved {retrieved_count}/{len(uploaded_message_ids)} segments!")
    print("  The segments are available on the Usenet server.")

# Disconnect
nntp_client.disconnect()
print("\n✓ Disconnected from Usenet")

print("\n" + "="*80)
print("RETRIEVAL TEST COMPLETE")
print("="*80)