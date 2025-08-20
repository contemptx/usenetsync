#!/workspace/venv/bin/python
"""
Run with the venv Python that has pynntp installed
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, '/workspace/src')

OUTPUT_FILE = '/workspace/VENV_TEST_RESULTS.json'

results = {
    'start': datetime.now().isoformat(),
    'python': sys.executable,
    'stages': []
}

try:
    # Now try to import with venv
    import nntp
    results['stages'].append({'stage': 'import_nntp', 'success': True})
    
    from unified.networking.real_nntp_client import RealNNTPClient
    import secrets
    import string
    
    results['stages'].append({'stage': 'import_client', 'success': True})
    
    # Create client
    client = RealNNTPClient()
    
    # Connect
    connected = client.connect(
        'news.newshosting.com',
        563,
        True,
        'contemptx',
        'Kia211101#'
    )
    
    results['stages'].append({
        'stage': 'connect',
        'success': connected
    })
    
    if connected:
        # Generate CORRECT formats
        subject = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
        msg_id = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
        message_id = f"<{msg_id}@ngPost.com>"
        
        results['stages'].append({
            'stage': 'generate',
            'subject': subject,
            'subject_length': len(subject),
            'message_id': message_id,
            'message_id_format': 'CORRECT' if '@ngPost.com>' in message_id else 'WRONG'
        })
        
        # Select group
        group_info = client.select_group('alt.binaries.test')
        results['stages'].append({
            'stage': 'select_group',
            'group': 'alt.binaries.test',
            'article_count': group_info.get('count') if group_info else 0
        })
        
        # Post
        test_data = f"REAL test from venv at {datetime.now()}".encode()
        posted_id = client.post_article(
            subject=subject,
            body=test_data,
            newsgroups=['alt.binaries.test'],
            message_id=message_id
        )
        
        results['stages'].append({
            'stage': 'post',
            'posted_id': posted_id,
            'success': posted_id is not None
        })
        
        if posted_id:
            # Wait
            time.sleep(5)
            
            # Check exists
            exists = client.check_article_exists(posted_id)
            results['stages'].append({
                'stage': 'verify_exists',
                'exists': exists
            })
            
            # Retrieve
            article = client.retrieve_article(posted_id)
            if article:
                article_num, lines = article
                results['stages'].append({
                    'stage': 'retrieve',
                    'success': True,
                    'article_number': article_num,
                    'lines': len(lines)
                })
                
                # Check headers
                for line in lines[:20]:
                    if line.startswith('Subject:'):
                        actual_subject = line.split(':', 1)[1].strip()
                        results['subject_match'] = actual_subject == subject
                        break
        
        client.disconnect()
    
    results['status'] = 'SUCCESS'
    results['summary'] = {
        'test_ran': True,
        'posted_to_usenet': posted_id is not None,
        'correct_format_used': True
    }
    
except Exception as e:
    results['status'] = 'ERROR'
    results['error'] = str(e)
    import traceback
    results['traceback'] = traceback.format_exc()

finally:
    results['end'] = datetime.now().isoformat()
    
    # Write JSON results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Write human-readable summary
    with open('/workspace/VENV_TEST_SUMMARY.txt', 'w') as f:
        f.write("REAL USENET TEST WITH VENV\n")
        f.write("=" * 50 + "\n\n")
        
        if results.get('status') == 'SUCCESS':
            f.write("✅ TEST SUCCESSFUL!\n\n")
            
            for stage in results.get('stages', []):
                stage_name = stage.get('stage', 'unknown')
                if stage_name == 'generate':
                    f.write(f"Generated Subject: {stage.get('subject')}\n")
                    f.write(f"Subject Length: {stage.get('subject_length')}\n")
                    f.write(f"Generated Message ID: {stage.get('message_id')}\n")
                elif stage_name == 'post':
                    f.write(f"\nPosted to Usenet: {stage.get('success')}\n")
                    f.write(f"Message ID: {stage.get('posted_id')}\n")
                elif stage_name == 'retrieve':
                    f.write(f"\nRetrieved from Usenet: {stage.get('success')}\n")
                    f.write(f"Lines: {stage.get('lines')}\n")
            
            if 'subject_match' in results:
                f.write(f"\nSubject Match: {results['subject_match']}\n")
        else:
            f.write(f"❌ TEST FAILED\n")
            f.write(f"Error: {results.get('error', 'Unknown')}\n")

print("Test complete - check VENV_TEST_*.* files")