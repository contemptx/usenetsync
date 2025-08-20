#!/usr/bin/env python3
"""
REAL TEST - NO SIMULATION
Actually posts to Usenet and retrieves
"""

import sys
import os
sys.path.insert(0, '/workspace/src')

from unified.networking.real_nntp_client import RealNNTPClient
import secrets
import string
import time

# REAL credentials
SERVER = "news.newshosting.com"
PORT = 563
USER = "contemptx"
PASS = "Kia211101#"
GROUP = "alt.binaries.test"

print("STARTING REAL TEST - NO SIMULATION")
print("=" * 50)

# Connect
nntp = RealNNTPClient()
connected = nntp.connect(SERVER, PORT, True, USER, PASS)
print(f"Connected: {connected}")

if connected:
    # Generate REAL subject (20 random chars)
    subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
    print(f"Subject to post: {subject}")
    
    # Generate REAL message ID  
    msg_id_local = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    message_id = f"<{msg_id_local}@ngPost.com>"
    print(f"Message ID: {message_id}")
    
    # Post REAL article
    test_data = f"Test at {time.time()}".encode()
    posted_id = nntp.post_article(
        subject=subject,
        body=test_data,
        newsgroups=[GROUP],
        message_id=message_id
    )
    
    print(f"Posted ID returned: {posted_id}")
    
    # Wait and retrieve
    time.sleep(3)
    exists = nntp.check_article_exists(posted_id or message_id)
    print(f"Article exists: {exists}")
    
    if exists:
        article = nntp.retrieve_article(posted_id or message_id)
        if article:
            print(f"Retrieved: {len(article[1])} lines")
    
    nntp.disconnect()

print("REAL TEST COMPLETE")