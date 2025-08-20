#!/usr/bin/env python3
"""
Use the EXISTING production NNTP client that's already in the codebase
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, '/workspace/src')

OUTPUT_FILE = '/workspace/PRODUCTION_TEST_RESULTS.json'

results = {
    'start': datetime.now().isoformat(),
    'stages': []
}

try:
    # Use the PRODUCTION client that already exists
    from networking.production_nntp_client import ProductionNNTPClient
    import secrets
    import string
    
    results['stages'].append({'stage': 'import', 'success': True})
    
    # Initialize client
    client = ProductionNNTPClient(
        host='news.newshosting.com',
        port=563,
        username='contemptx',
        password='Kia211101#',
        use_ssl=True,
        max_connections=1
    )
    
    results['stages'].append({'stage': 'client_created', 'success': True})
    
    # Connect
    connected = client.connect()
    results['stages'].append({
        'stage': 'connect',
        'success': connected,
        'authenticated': client.authenticated if hasattr(client, 'authenticated') else None
    })
    
    if connected:
        # Generate CORRECT subject (20 random chars)
        subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
        
        # Generate CORRECT message ID
        msg_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        message_id = f"<{msg_id}@ngPost.com>"
        
        results['stages'].append({
            'stage': 'generate',
            'subject': subject,
            'message_id': message_id
        })
        
        # Post data
        test_data = f"Production test at {datetime.now()}".encode()
        
        success, response = client.post_data(
            subject=subject,
            data=test_data,
            newsgroup='alt.binaries.test',
            message_id=message_id
        )
        
        results['stages'].append({
            'stage': 'post',
            'success': success,
            'response': str(response)[:200] if response else None
        })
        
        if success:
            # Extract message ID from response
            posted_id = response if isinstance(response, str) else message_id
            
            # Wait for propagation
            time.sleep(5)
            
            # Try to retrieve
            retrieved_data = client.retrieve_article(posted_id)
            
            results['stages'].append({
                'stage': 'retrieve',
                'message_id': posted_id,
                'retrieved': retrieved_data is not None,
                'size': len(retrieved_data) if retrieved_data else 0
            })
        
        # Disconnect
        client.disconnect()
        results['stages'].append({'stage': 'disconnect', 'success': True})
    
    results['status'] = 'COMPLETE'
    
except Exception as e:
    results['status'] = 'ERROR'
    results['error'] = str(e)
    import traceback
    results['traceback'] = traceback.format_exc()

finally:
    results['end'] = datetime.now().isoformat()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also write a simple summary
    with open('/workspace/PRODUCTION_TEST_SUMMARY.txt', 'w') as f:
        f.write("PRODUCTION CLIENT TEST SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Status: {results.get('status', 'UNKNOWN')}\n")
        if 'error' in results:
            f.write(f"Error: {results['error']}\n")
        else:
            for stage in results.get('stages', []):
                f.write(f"{stage.get('stage')}: {stage.get('success', '?')}\n")

print("Test complete - check PRODUCTION_TEST_*.* files")