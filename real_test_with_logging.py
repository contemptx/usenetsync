#!/usr/bin/env python3
"""
REAL TEST that writes everything to a file
No terminal output needed
"""

import sys
import os
import json
import traceback
from datetime import datetime

# Add to path
sys.path.insert(0, '/workspace/src')

# Output file
OUTPUT_FILE = '/workspace/REAL_TEST_RESULTS.json'

def log_result(results, stage, data):
    """Log results to dict"""
    results['stages'].append({
        'timestamp': datetime.now().isoformat(),
        'stage': stage,
        'data': data
    })
    # Write immediately in case of crash
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def main():
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'STARTED',
        'stages': []
    }
    
    try:
        log_result(results, 'IMPORT', 'Starting imports')
        
        from unified.networking.real_nntp_client import RealNNTPClient
        import secrets
        import string
        import time
        import hashlib
        
        log_result(results, 'IMPORT', 'Imports successful')
        
        # Credentials
        SERVER = "news.newshosting.com"
        PORT = 563
        USER = "contemptx"
        PASS = "Kia211101#"
        GROUP = "alt.binaries.test"
        
        log_result(results, 'CONFIG', {
            'server': SERVER,
            'port': PORT,
            'user': USER,
            'group': GROUP
        })
        
        # Create NNTP client
        nntp = RealNNTPClient()
        log_result(results, 'CLIENT', 'NNTP client created')
        
        # Connect
        connected = nntp.connect(SERVER, PORT, True, USER, PASS)
        log_result(results, 'CONNECT', {
            'connected': connected,
            'authenticated': nntp.authenticated
        })
        
        if not connected:
            results['status'] = 'FAILED'
            results['error'] = 'Connection failed'
            return
        
        # Select group
        group_info = nntp.select_group(GROUP)
        log_result(results, 'GROUP', group_info)
        
        # Generate CORRECT format subject (20 random chars)
        subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
        log_result(results, 'SUBJECT', {
            'generated': subject,
            'length': len(subject),
            'format': '20 random chars'
        })
        
        # Generate CORRECT format message ID
        msg_id_local = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        message_id = f"<{msg_id_local}@ngPost.com>"
        log_result(results, 'MESSAGE_ID', {
            'generated': message_id,
            'format': '<16chars@ngPost.com>'
        })
        
        # Create test data
        test_data = f"Real test at {datetime.now().isoformat()}\n".encode() * 10
        test_hash = hashlib.sha256(test_data).hexdigest()
        log_result(results, 'DATA', {
            'size': len(test_data),
            'hash': test_hash[:32] + '...'
        })
        
        # POST to Usenet
        posted_id = nntp.post_article(
            subject=subject,
            body=test_data,
            newsgroups=[GROUP],
            message_id=message_id
        )
        
        log_result(results, 'POST', {
            'requested_id': message_id,
            'returned_id': posted_id,
            'success': posted_id is not None
        })
        
        if not posted_id:
            results['status'] = 'FAILED'
            results['error'] = 'Post failed'
            return
        
        # Wait for propagation
        log_result(results, 'WAIT', 'Waiting 5 seconds for propagation')
        time.sleep(5)
        
        # Check if exists
        exists = nntp.check_article_exists(posted_id)
        log_result(results, 'EXISTS', {
            'message_id': posted_id,
            'exists': exists
        })
        
        # Try to retrieve
        article = nntp.retrieve_article(posted_id)
        if article:
            article_num, lines = article
            
            # Extract headers
            headers = {}
            body_start = 0
            for i, line in enumerate(lines):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key] = value.strip()
            
            # Extract body
            body_lines = lines[body_start:] if body_start < len(lines) else []
            body_text = '\n'.join(body_lines)
            
            log_result(results, 'RETRIEVED', {
                'article_number': article_num,
                'total_lines': len(lines),
                'headers': headers,
                'body_size': len(body_text),
                'subject_match': headers.get('Subject') == subject,
                'message_id_match': headers.get('Message-ID', '').strip('<>') == message_id.strip('<>')
            })
            
            # Verify data
            retrieved_hash = hashlib.sha256(body_text.encode()).hexdigest()
            log_result(results, 'VERIFY', {
                'original_hash': test_hash[:32] + '...',
                'retrieved_hash': retrieved_hash[:32] + '...',
                'match': retrieved_hash == test_hash
            })
        else:
            log_result(results, 'RETRIEVED', {'success': False})
        
        # Disconnect
        nntp.disconnect()
        log_result(results, 'DISCONNECT', 'Disconnected')
        
        results['status'] = 'SUCCESS'
        results['summary'] = {
            'posted_subject': subject,
            'posted_message_id': posted_id,
            'retrieved_successfully': article is not None,
            'data_verified': article is not None
        }
        
    except Exception as e:
        results['status'] = 'ERROR'
        results['error'] = str(e)
        results['traceback'] = traceback.format_exc()
        
    finally:
        results['end_time'] = datetime.now().isoformat()
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)

if __name__ == "__main__":
    main()