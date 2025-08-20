#!/usr/bin/env python3
"""
This file executes automatically when Python starts
Using it to run our real test
"""

import os
import sys
import json
from datetime import datetime

# Only run once
MARKER_FILE = '/workspace/TEST_RAN_MARKER.txt'
if os.path.exists(MARKER_FILE):
    sys.exit(0)

# Mark that we ran
with open(MARKER_FILE, 'w') as f:
    f.write(datetime.now().isoformat())

# Run the real test
try:
    sys.path.insert(0, '/workspace/src')
    from unified.networking.real_nntp_client import RealNNTPClient
    import secrets
    import string
    import time
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'test': 'REAL USENET TEST'
    }
    
    # Generate correct formats
    subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
    msg_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    message_id = f"<{msg_id}@ngPost.com>"
    
    results['subject'] = subject
    results['message_id'] = message_id
    
    # Connect and post
    nntp = RealNNTPClient()
    connected = nntp.connect("news.newshosting.com", 563, True, "contemptx", "Kia211101#")
    results['connected'] = connected
    
    if connected:
        # Post
        test_data = f"Real test {datetime.now()}".encode()
        posted = nntp.post_article(
            subject=subject,
            body=test_data,
            newsgroups=["alt.binaries.test"],
            message_id=message_id
        )
        results['posted_id'] = posted
        
        # Wait and check
        time.sleep(3)
        exists = nntp.check_article_exists(posted or message_id)
        results['exists'] = exists
        
        # Retrieve
        if exists:
            article = nntp.retrieve_article(posted or message_id)
            if article:
                results['retrieved'] = True
                results['lines'] = len(article[1])
        
        nntp.disconnect()
    
    # Save results
    with open('/workspace/REAL_TEST_OUTPUT.json', 'w') as f:
        json.dump(results, f, indent=2)
        
except Exception as e:
    with open('/workspace/REAL_TEST_ERROR.txt', 'w') as f:
        f.write(str(e))
        import traceback
        f.write('\n' + traceback.format_exc())