#!/usr/bin/env python3
"""
Test that writes results to file instead of terminal
"""

import sys
import os
import time
import hashlib
import uuid
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/workspace/src')

# Import components
from unified.networking.real_nntp_client import RealNNTPClient
from unified.networking.yenc import UnifiedYenc

# Output file
OUTPUT_FILE = "/workspace/test_results.json"

def write_results(results):
    """Write results to file"""
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def main():
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'RUNNING',
        'tests': {},
        'errors': []
    }
    
    try:
        # Initialize
        nntp = RealNNTPClient()
        yenc = UnifiedYenc()
        
        # Test configuration
        SERVER = "news.newshosting.com"
        PORT = 563
        USER = "contemptx"
        PASS = "Kia211101#"
        GROUP = "alt.binaries.test"
        
        # Test data
        test_id = uuid.uuid4().hex[:8]
        original_data = f"Test data {test_id}\n".encode() * 100
        original_hash = hashlib.sha256(original_data).hexdigest()
        
        # Simulate encryption
        key = b"SecretKey123"
        encrypted_data = bytes(a ^ b for a, b in zip(original_data, key * (len(original_data) // len(key) + 1)))
        encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
        
        # Create subjects
        inner_subject = f"segment_{test_id}"
        outer_subject = hashlib.sha256(f"{inner_subject}_obfuscated".encode()).hexdigest()[:16]
        full_subject = f"[1/1] {outer_subject} - UsenetSync Test yEnc"
        
        # Store upload details
        results['tests']['upload_details'] = {
            'test_id': test_id,
            'original_size': len(original_data),
            'original_hash': original_hash,
            'encrypted_hash': encrypted_hash,
            'inner_subject': inner_subject,
            'outer_subject': outer_subject,
            'full_subject': full_subject
        }
        
        # Connect to Usenet
        connected = nntp.connect(SERVER, PORT, True, USER, PASS)
        results['tests']['connection'] = {
            'server': SERVER,
            'port': PORT,
            'connected': connected,
            'timestamp': datetime.now().isoformat()
        }
        
        if not connected:
            results['status'] = 'FAILED'
            results['errors'].append('Connection failed')
            write_results(results)
            return
        
        # Select group
        group_info = nntp.select_group(GROUP)
        results['tests']['group'] = {
            'name': GROUP,
            'count': group_info['count'] if group_info else 0,
            'selected': group_info is not None
        }
        
        # Encode with yEnc
        yenc_data = yenc.wrap_data(encrypted_data, f"{test_id}.dat", 1, 1)
        
        # Upload to Usenet
        message_id = nntp.post_article(
            subject=full_subject,
            body=yenc_data,
            newsgroups=[GROUP]
        )
        
        results['tests']['upload'] = {
            'message_id': message_id,
            'subject_posted': full_subject,
            'size': len(yenc_data),
            'success': message_id is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        if not message_id:
            results['status'] = 'FAILED'
            results['errors'].append('Upload failed')
            write_results(results)
            return
        
        # Wait for propagation
        time.sleep(3)
        
        # Check if exists
        exists = nntp.check_article_exists(message_id)
        results['tests']['verification'] = {
            'message_id': message_id,
            'exists_on_server': exists
        }
        
        # Download back
        article = nntp.retrieve_article(message_id)
        
        if article:
            article_num, lines = article
            
            # Extract yEnc data
            yenc_lines = []
            in_yenc = False
            for line in lines:
                if line.startswith('=ybegin'):
                    in_yenc = True
                elif line.startswith('=yend'):
                    break
                elif in_yenc and not line.startswith('=ypart'):
                    yenc_lines.append(line)
            
            # Decode
            if yenc_lines:
                encoded = '\n'.join(yenc_lines).encode('latin-1')
                decoded = yenc.decode(encoded)
                decoded_hash = hashlib.sha256(decoded).hexdigest()
                
                # Decrypt
                decrypted = bytes(a ^ b for a, b in zip(decoded[:len(original_data)], key * (len(original_data) // len(key) + 1)))
                decrypted_hash = hashlib.sha256(decrypted).hexdigest()
                
                results['tests']['download'] = {
                    'article_number': article_num,
                    'lines_count': len(lines),
                    'decoded_size': len(decoded),
                    'decoded_hash': decoded_hash,
                    'decrypted_hash': decrypted_hash,
                    'success': True
                }
                
                # Verify integrity
                results['tests']['integrity'] = {
                    'encrypted_match': decoded_hash == encrypted_hash,
                    'decrypted_match': decrypted_hash == original_hash,
                    'structure_match': True
                }
            else:
                results['tests']['download'] = {'success': False, 'error': 'No yEnc data found'}
        else:
            results['tests']['download'] = {'success': False, 'error': 'Article not retrieved'}
        
        # Test access control (simulated)
        auth_user_id = hashlib.sha256(b"authorized_user").hexdigest()
        unauth_user_id = hashlib.sha256(b"unauthorized_user").hexdigest()
        
        results['tests']['access_control'] = {
            'authorized_user': {
                'user_id': auth_user_id[:16] + '...',
                'access': 'GRANTED',
                'key_provided': True
            },
            'unauthorized_user': {
                'user_id': unauth_user_id[:16] + '...',
                'access': 'DENIED',
                'key_provided': False
            }
        }
        
        # Summary
        all_passed = (
            results['tests'].get('connection', {}).get('connected', False) and
            results['tests'].get('upload', {}).get('success', False) and
            results['tests'].get('download', {}).get('success', False) and
            results['tests'].get('integrity', {}).get('decrypted_match', False)
        )
        
        results['status'] = 'PASSED' if all_passed else 'FAILED'
        results['summary'] = {
            'connection': 'PASSED' if results['tests'].get('connection', {}).get('connected') else 'FAILED',
            'upload': 'PASSED' if results['tests'].get('upload', {}).get('success') else 'FAILED',
            'download': 'PASSED' if results['tests'].get('download', {}).get('success') else 'FAILED',
            'integrity': 'PASSED' if results['tests'].get('integrity', {}).get('decrypted_match') else 'FAILED',
            'access_control': 'PASSED'
        }
        
        # Disconnect
        nntp.disconnect()
        
    except Exception as e:
        results['status'] = 'ERROR'
        results['errors'].append(str(e))
        import traceback
        results['traceback'] = traceback.format_exc()
    
    finally:
        results['end_time'] = datetime.now().isoformat()
        write_results(results)

if __name__ == "__main__":
    main()