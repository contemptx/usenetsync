#!/usr/bin/env python3
"""
Simple REAL Usenet post test
"""
import sys
import site
sys.path.insert(0, site.USER_SITE)

import nntp
import secrets
import base64
from datetime import datetime, UTC

# Connect
print("Connecting to Usenet...")
client = nntp.NNTPClient(
    host='news.newshosting.com',
    port=563,
    username='contemptx',
    password='Kia211101#',
    use_ssl=True
)

print("Connected!")

# Select group
client.group('alt.binaries.test')
print("Group selected: alt.binaries.test")

# Create a simple test article
message_id = f"<{secrets.token_hex(16)}@ngPost.com>"
subject = base64.b32encode(secrets.token_bytes(10)).decode().rstrip('=')
content = b"This is a real test post to Usenet!"
encoded = base64.b64encode(content).decode('ascii')

# Build headers dictionary and body
headers = {
    'From': 'test@example.com',
    'Newsgroups': 'alt.binaries.test',
    'Subject': subject,
    'Message-ID': message_id,
    'Date': datetime.now(UTC).strftime('%a, %d %b %Y %H:%M:%S +0000')
}

# Body with yEnc encoding
body = f"""=ybegin line=128 size={len(content)} name=test.txt
{encoded}
=yend size={len(content)}"""

print(f"\nPosting article:")
print(f"  Message-ID: {message_id}")
print(f"  Subject: {subject}")

# Try to post
try:
    # The post method expects headers dict and body
    response = client.post(headers=headers, body=body)
    print(f"✅ Posted successfully! Response: {response}")
except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"Error type: {type(e)}")
    
# Try to retrieve it
print("\nTrying to retrieve...")
try:
    response = client.article(message_id)
    if response:
        print(f"✅ Retrieved successfully!")
        article_num, article_id, lines = response
        print(f"  Article number: {article_num}")
        print(f"  Lines: {len(lines)}")
    else:
        print("❌ No response")
except Exception as e:
    print(f"❌ Retrieval failed: {e}")

client.quit()
print("\nDone!")