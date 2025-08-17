#!/usr/bin/env python3
"""
Enhanced E2E Test with Detailed Usenet Feedback
Shows complete server responses and data flow
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import secrets

# Add src to path
sys.path.insert(0, '/workspace')

# Import all real system components
from src.database.production_db_wrapper import ProductionDatabaseManager
from src.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.networking.production_nntp_client import ProductionNNTPClient
from src.networking.optimized_connection_pool import OptimizedConnectionPool, get_shared_pool

class EnhancedFeedbackTest:
    """Test with detailed Usenet server feedback"""
    
    def __init__(self):
        self.test_dir = None
        self.db_path = None
        self.systems = {}
        self.test_results = {
            'uploads': [],
            'retrievals': [],
            'errors': []
        }
        
    def setup(self):
        """Initialize test environment"""
        print("\n" + "="*80)
        print("ENHANCED USENET TEST WITH DETAILED FEEDBACK")
        print("="*80)
        print("\n🔧 SETTING UP TEST ENVIRONMENT")
        print("-" * 50)
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp(prefix='usenet_feedback_test_')
        self.db_path = os.path.join(self.test_dir, 'test.db')
        print(f"✓ Test directory: {self.test_dir}")
        
        # Create database
        self._create_schema()
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = self.db_path
        db_config.pool_size = 1  # Minimal for testing
        db_config.timeout = 60.0
        
        self.systems['db'] = EnhancedDatabaseManager(db_config)
        print("✓ Database initialized")
        
        # Initialize security
        self.systems['security'] = EnhancedSecuritySystem(self.systems['db'])
        print("✓ Security system initialized")
        
        # Initialize NNTP with new password and optimized pool
        print("\n📡 INITIALIZING NNTP CONNECTION")
        print("-" * 50)
        
        # Use the optimized connection pool
        self.systems['pool'] = OptimizedConnectionPool(
            host='news.newshosting.com',
            port=563,
            username='contemptx',
            password='Kia211101#',  # Updated password
            use_ssl=True,
            max_connections=60,
            initial_connections=1  # Start with just 1
        )
        
        print(f"✓ Connection pool created: {self.systems['pool'].get_stats()}")
        
        # Create NNTP client using the pool
        self.systems['nntp'] = ProductionNNTPClient(
            host='news.newshosting.com',
            port=563,
            username='contemptx',
            password='Kia211101#',  # Updated password
            use_ssl=True,
            max_connections=1  # Use minimal connections
        )
        print("✓ NNTP client initialized\n")
        
    def _create_schema(self):
        """Create minimal database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        
    def test_connection(self):
        """Test NNTP connection with detailed feedback"""
        print("\n📡 TESTING NNTP CONNECTION")
        print("-" * 50)
        
        try:
            with self.systems['pool'].get_connection() as conn:
                # Test with NOOP or simple command
                print("Sending test message to verify connection...")
                
                test_msg_id = self.systems['nntp']._generate_message_id()
                test_message = f"""From: test@usenetsync.com
Newsgroups: alt.binaries.test
Subject: Connection Test {datetime.now().strftime('%Y%m%d_%H%M%S')}
Message-ID: {test_msg_id}
Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}
X-Test: Enhanced feedback test

Testing connection at {datetime.now()}
""".encode('utf-8')
                
                print(f"\n📤 SENDING TEST MESSAGE:")
                print(f"  Message-ID: {test_msg_id}")
                print(f"  Size: {len(test_message)} bytes")
                
                # Post the message
                response = conn.post(test_message)
                
                print(f"\n📥 SERVER RESPONSE:")
                print(f"  Raw Response: {response}")
                print(f"  Response Type: {type(response)}")
                
                if isinstance(response, tuple):
                    code, msg_id = response
                    print(f"  Response Code: {code}")
                    print(f"  Server Message ID: {msg_id}")
                    
                    self.test_results['uploads'].append({
                        'test': 'connection',
                        'sent_id': test_msg_id,
                        'server_response': response,
                        'server_id': msg_id,
                        'success': True
                    })
                    print(f"\n✅ Connection test successful!")
                else:
                    print(f"  Unexpected response format")
                    
                return True
                
        except Exception as e:
            print(f"\n❌ Connection test failed: {e}")
            print(f"  Error Type: {type(e).__name__}")
            print(f"  Error Details: {str(e)}")
            self.test_results['errors'].append({
                'test': 'connection',
                'error': str(e),
                'type': type(e).__name__
            })
            return False
            
    def test_upload_segments(self):
        """Test uploading multiple segments with detailed feedback"""
        print("\n📤 TESTING SEGMENT UPLOADS")
        print("-" * 50)
        
        # Create test data
        test_files = [
            {'name': 'small.txt', 'size': 1024, 'content': b'A' * 1024},
            {'name': 'medium.txt', 'size': 5120, 'content': b'B' * 5120},
            {'name': 'large.txt', 'size': 10240, 'content': b'C' * 10240}
        ]
        
        for file_data in test_files:
            print(f"\n📁 Uploading: {file_data['name']} ({file_data['size']} bytes)")
            
            # Create segments (simulate 3 segments per file)
            segment_size = max(1024, file_data['size'] // 3)
            segments = []
            
            for i in range(0, file_data['size'], segment_size):
                segment = file_data['content'][i:i+segment_size]
                segments.append({
                    'index': len(segments),
                    'data': segment,
                    'size': len(segment)
                })
                
            print(f"  Created {len(segments)} segments")
            
            # Upload each segment
            for seg in segments[:2]:  # Upload first 2 segments only for testing
                try:
                    # Generate unique IDs
                    msg_id = self.systems['nntp']._generate_message_id()
                    subject = f"test_{file_data['name']}_seg{seg['index']}"
                    
                    # Create NNTP message
                    message = f"""From: test@usenetsync.com
Newsgroups: alt.binaries.test
Subject: {subject}
Message-ID: {msg_id}
Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}
Content-Type: application/octet-stream
Content-Length: {seg['size']}

""".encode('utf-8') + seg['data'][:500]  # Limit data for testing
                    
                    print(f"\n  📤 Segment {seg['index']}:")
                    print(f"    Message-ID: {msg_id}")
                    print(f"    Subject: {subject}")
                    print(f"    Size: {len(message)} bytes")
                    
                    # Upload with connection pool
                    with self.systems['pool'].get_connection() as conn:
                        response = conn.post(message)
                        
                    print(f"  📥 Server Response:")
                    print(f"    Raw: {response}")
                    
                    if isinstance(response, tuple):
                        code, server_id = response
                        print(f"    Code: {code}")
                        print(f"    Server ID: {server_id}")
                        
                        if code == 240:
                            print(f"    ✅ Upload successful")
                        else:
                            print(f"    ⚠️ Upload returned code {code}")
                            
                        self.test_results['uploads'].append({
                            'file': file_data['name'],
                            'segment': seg['index'],
                            'sent_id': msg_id,
                            'server_response': response,
                            'success': code == 240
                        })
                    else:
                        print(f"    ⚠️ Unexpected response: {response}")
                        
                    # Rate limiting - wait between uploads
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"  ❌ Upload failed: {e}")
                    self.test_results['errors'].append({
                        'file': file_data['name'],
                        'segment': seg['index'],
                        'error': str(e)
                    })
                    
                    # If rate limited, wait longer
                    if '502' in str(e):
                        print(f"    ⚠️ Rate limited - waiting 30s...")
                        time.sleep(30)
                        
    def test_retrieval(self):
        """Test retrieving uploaded articles"""
        print("\n📥 TESTING ARTICLE RETRIEVAL")
        print("-" * 50)
        
        # Try to retrieve some of the uploaded articles
        successful_uploads = [u for u in self.test_results['uploads'] if u.get('success')]
        
        if not successful_uploads:
            print("  ⚠️ No successful uploads to retrieve")
            return
            
        for upload in successful_uploads[:2]:  # Test first 2
            try:
                server_id = upload.get('server_response', [None, None])[1]
                if not server_id:
                    continue
                    
                print(f"\n  📥 Retrieving: {server_id}")
                
                with self.systems['pool'].get_connection() as conn:
                    # Try to retrieve the article
                    response = conn.connection.article(server_id)
                    
                print(f"  📥 Server Response:")
                print(f"    Response Type: {type(response)}")
                
                if response:
                    resp_code = response[0] if isinstance(response, tuple) else None
                    print(f"    Response Code: {resp_code}")
                    
                    if resp_code == 220:  # Article retrieved
                        print(f"    ✅ Article retrieved successfully")
                        # Show first 200 chars of article
                        if len(response) > 2:
                            article_preview = str(response[2])[:200] if response[2] else "No content"
                            print(f"    Preview: {article_preview}...")
                    else:
                        print(f"    ⚠️ Retrieval returned code {resp_code}")
                        
                    self.test_results['retrievals'].append({
                        'message_id': server_id,
                        'response': str(response)[:500],
                        'success': resp_code == 220
                    })
                    
            except Exception as e:
                print(f"  ❌ Retrieval failed: {e}")
                self.test_results['errors'].append({
                    'operation': 'retrieval',
                    'message_id': server_id,
                    'error': str(e)
                })
                
    def show_pool_stats(self):
        """Show connection pool statistics"""
        print("\n📊 CONNECTION POOL STATISTICS")
        print("-" * 50)
        
        stats = self.systems['pool'].get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    def generate_report(self):
        """Generate detailed test report"""
        print("\n" + "="*80)
        print("DETAILED TEST REPORT")
        print("="*80)
        
        # Upload Summary
        print("\n📤 UPLOAD RESULTS")
        print("-" * 50)
        total_uploads = len(self.test_results['uploads'])
        successful = sum(1 for u in self.test_results['uploads'] if u.get('success'))
        print(f"  Total Attempts: {total_uploads}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total_uploads - successful}")
        print(f"  Success Rate: {(successful/total_uploads*100) if total_uploads > 0 else 0:.1f}%")
        
        print("\n  Detailed Upload Results:")
        for upload in self.test_results['uploads']:
            status = "✅" if upload.get('success') else "❌"
            print(f"    {status} {upload.get('file', 'test')} - Segment {upload.get('segment', 0)}")
            print(f"       Sent ID: {upload.get('sent_id', 'N/A')[:50]}...")
            print(f"       Server Response: {upload.get('server_response')}")
            
        # Retrieval Summary
        print("\n📥 RETRIEVAL RESULTS")
        print("-" * 50)
        total_retrievals = len(self.test_results['retrievals'])
        successful_ret = sum(1 for r in self.test_results['retrievals'] if r.get('success'))
        print(f"  Total Attempts: {total_retrievals}")
        print(f"  Successful: {successful_ret}")
        print(f"  Failed: {total_retrievals - successful_ret}")
        
        # Error Summary
        if self.test_results['errors']:
            print("\n⚠️ ERRORS ENCOUNTERED")
            print("-" * 50)
            for error in self.test_results['errors']:
                print(f"  • {error.get('operation', 'Unknown')}: {error.get('error')}")
                
        # Save detailed results to file
        results_file = os.path.join(self.test_dir, 'test_results.json')
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {results_file}")
        
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 CLEANING UP")
        print("-" * 50)
        
        try:
            # Close connection pool
            if 'pool' in self.systems:
                self.systems['pool'].close_all()
                print("✓ Connection pool closed")
                
            # Remove test directory
            if self.test_dir and os.path.exists(self.test_dir):
                # Save the results file first
                results_file = os.path.join(self.test_dir, 'test_results.json')
                if os.path.exists(results_file):
                    shutil.copy(results_file, '/workspace/latest_test_results.json')
                    print("✓ Results saved to /workspace/latest_test_results.json")
                    
                shutil.rmtree(self.test_dir)
                print("✓ Test directory removed")
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
            
    def run(self):
        """Run the complete test suite"""
        try:
            self.setup()
            
            # Run tests
            if self.test_connection():
                self.test_upload_segments()
                time.sleep(5)  # Wait before retrieval
                self.test_retrieval()
                
            # Show statistics
            self.show_pool_stats()
            
            # Generate report
            self.generate_report()
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.cleanup()


if __name__ == "__main__":
    test = EnhancedFeedbackTest()
    test.run()