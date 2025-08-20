#!/usr/bin/env python3
"""
Self-executing test that runs on import
Results written to AUTO_TEST_RESULTS.txt
"""

import os
import sys

# Immediate file write to confirm execution
with open('/workspace/AUTO_TEST_STARTED.txt', 'w') as f:
    f.write('Test started\n')

try:
    sys.path.insert(0, '/workspace/src')
    
    # Quick test
    from unified.networking.real_nntp_client import RealNNTPClient
    import secrets
    import string
    
    with open('/workspace/AUTO_TEST_RESULTS.txt', 'w') as f:
        f.write("AUTO TEST RESULTS\n")
        f.write("=" * 50 + "\n")
        
        # Test 1: Generate correct subject
        subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
        f.write(f"Generated Subject: {subject}\n")
        f.write(f"Subject Length: {len(subject)}\n")
        f.write(f"Subject Format: {'CORRECT' if len(subject) == 20 else 'WRONG'}\n\n")
        
        # Test 2: Generate correct message ID
        msg_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        message_id = f"<{msg_id}@ngPost.com>"
        f.write(f"Generated Message ID: {message_id}\n")
        f.write(f"Message ID Format: {'CORRECT' if '@ngPost.com>' in message_id else 'WRONG'}\n\n")
        
        # Test 3: Try to connect
        f.write("Attempting connection...\n")
        nntp = RealNNTPClient()
        connected = nntp.connect("news.newshosting.com", 563, True, "contemptx", "Kia211101#")
        f.write(f"Connected: {connected}\n")
        
        if connected:
            # Try to post
            f.write("Attempting to post...\n")
            test_body = b"Test message"
            posted = nntp.post_article(
                subject=subject,
                body=test_body,
                newsgroups=["alt.binaries.test"],
                message_id=message_id
            )
            f.write(f"Posted Message ID: {posted}\n")
            f.write(f"Post Success: {posted is not None}\n")
            
            nntp.disconnect()
            f.write("Disconnected\n")
        
        f.write("\nTEST COMPLETE\n")
        
except Exception as e:
    with open('/workspace/AUTO_TEST_ERROR.txt', 'w') as f:
        f.write(f"Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print("If this runs, check /workspace/AUTO_TEST_*.txt files")