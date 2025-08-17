#!/usr/bin/env python3
"""
REAL Usenet Testing - No Simulation!
Actually posts to and retrieves from Usenet
"""

import os
import sys
import json
import time
import hashlib
import secrets
import base64
from datetime import datetime
from pathlib import Path

# Add user site-packages to path
import site
sys.path.insert(0, site.USER_SITE)
sys.path.insert(0, '/workspace')

# Use pynntp for real NNTP operations (imports as 'nntp')
import nntp


class RealUsenetTest:
    """Perform REAL Usenet operations - no simulation!"""
    
    def __init__(self):
        # Load real credentials from config
        with open('/workspace/usenet_sync_config.json', 'r') as f:
            self.config = json.load(f)
        
        self.server_config = self.config['servers'][0]
        self.results = []
        self.posted_articles = []
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {message}")
        self.results.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def connect_to_usenet(self):
        """Establish REAL connection to Usenet server"""
        self.log("="*60)
        self.log("CONNECTING TO REAL USENET SERVER")
        self.log("="*60)
        
        try:
            # Real connection parameters
            hostname = self.server_config['hostname']
            port = self.server_config['port']
            username = self.server_config['username']
            password = self.server_config['password']
            use_ssl = self.server_config['use_ssl']
            
            self.log(f"Connecting to {hostname}:{port} (SSL: {use_ssl})")
            
            # Create REAL NNTP connection
            self.nntp_client = nntp.NNTPClient(
                host=hostname,
                port=port,
                username=username,
                password=password,
                use_ssl=use_ssl
            )
            
            # Get server capabilities
            response = self.nntp_client.capabilities()
            self.log(f"Server capabilities: {response}", "SUCCESS")
            
            # Select posting group
            group = self.server_config.get('posting_group', 'alt.binaries.test')
            self.nntp_client.group(group)
            self.log(f"Selected group: {group}", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Connection failed: {e}", "ERROR")
            return False
    
    def test_real_posting(self):
        """Post REAL articles to Usenet"""
        self.log("\n" + "="*60)
        self.log("TESTING REAL ARTICLE POSTING")
        self.log("="*60)
        
        try:
            # Create test data
            test_files = [
                ("test1.txt", b"This is test file 1 content - " + secrets.token_bytes(100)),
                ("test2.txt", b"This is test file 2 content - " + secrets.token_bytes(200)),
                ("test3.bin", secrets.token_bytes(1024))  # 1KB binary file
            ]
            
            for filename, content in test_files:
                # Generate obfuscated message ID and subject
                message_id = f"<{secrets.token_hex(16)}@ngPost.com>"
                subject = base64.b32encode(secrets.token_bytes(10)).decode().rstrip('=')
                
                # Encode content for posting
                encoded_content = base64.b64encode(content).decode('ascii')
                
                # Build article
                article_lines = [
                    f"From: anonymous@example.com",
                    f"Newsgroups: {self.server_config.get('posting_group', 'alt.binaries.test')}",
                    f"Subject: {subject}",
                    f"Message-ID: {message_id}",
                    f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}",
                    "",  # Empty line between headers and body
                    "=ybegin line=128 size=" + str(len(content)) + " name=" + filename,
                    encoded_content,
                    "=yend size=" + str(len(content))
                ]
                
                article = '\r\n'.join(article_lines)
                
                self.log(f"\nPosting article for {filename}:")
                self.log(f"  Message-ID: {message_id}")
                self.log(f"  Subject: {subject}")
                self.log(f"  Size: {len(content)} bytes")
                
                # POST THE ARTICLE FOR REAL!
                try:
                    response = self.nntp_client.post(article)
                    self.log(f"  Posted successfully! Response: {response}", "SUCCESS")
                    
                    # Store for retrieval test
                    self.posted_articles.append({
                        "filename": filename,
                        "message_id": message_id,
                        "subject": subject,
                        "content": content,
                        "content_hash": hashlib.sha256(content).hexdigest()
                    })
                    
                except Exception as post_error:
                    self.log(f"  Posting failed: {post_error}", "ERROR")
            
            self.log(f"\nTotal articles posted: {len(self.posted_articles)}", "SUCCESS")
            return len(self.posted_articles) > 0
            
        except Exception as e:
            self.log(f"Posting test failed: {e}", "ERROR")
            return False
    
    def test_real_retrieval(self):
        """Retrieve REAL articles from Usenet"""
        self.log("\n" + "="*60)
        self.log("TESTING REAL ARTICLE RETRIEVAL")
        self.log("="*60)
        
        if not self.posted_articles:
            self.log("No articles to retrieve (posting may have failed)", "WARNING")
            return False
        
        # Wait a moment for propagation
        self.log("Waiting 2 seconds for article propagation...")
        time.sleep(2)
        
        retrieved_count = 0
        
        for article_info in self.posted_articles:
            message_id = article_info['message_id']
            self.log(f"\nRetrieving article: {message_id}")
            
            try:
                # RETRIEVE THE ARTICLE FOR REAL!
                response = self.nntp_client.article(message_id)
                
                if response:
                    # Parse the response
                    article_num, article_id, article_lines = response
                    
                    self.log(f"  Article retrieved successfully!", "SUCCESS")
                    self.log(f"  Article number: {article_num}")
                    self.log(f"  Lines received: {len(article_lines)}")
                    
                    # Extract and verify content
                    in_body = False
                    body_lines = []
                    
                    for line in article_lines:
                        if not in_body:
                            if line.strip() == '':
                                in_body = True
                        else:
                            if line.startswith('=yend'):
                                break
                            elif not line.startswith('=ybegin'):
                                body_lines.append(line)
                    
                    # Decode content
                    encoded_body = ''.join(body_lines)
                    try:
                        decoded_content = base64.b64decode(encoded_body)
                        
                        # Verify hash
                        retrieved_hash = hashlib.sha256(decoded_content).hexdigest()
                        original_hash = article_info['content_hash']
                        
                        if retrieved_hash == original_hash:
                            self.log(f"  ✅ Content verified! Hash matches: {retrieved_hash[:16]}...", "SUCCESS")
                            retrieved_count += 1
                        else:
                            self.log(f"  ❌ Hash mismatch! Expected: {original_hash[:16]}..., Got: {retrieved_hash[:16]}...", "ERROR")
                    
                    except Exception as decode_error:
                        self.log(f"  Failed to decode content: {decode_error}", "ERROR")
                    
                else:
                    self.log(f"  No response received", "WARNING")
                    
            except Exception as retrieve_error:
                self.log(f"  Retrieval failed: {retrieve_error}", "ERROR")
        
        self.log(f"\nTotal articles retrieved: {retrieved_count}/{len(self.posted_articles)}", 
                "SUCCESS" if retrieved_count == len(self.posted_articles) else "WARNING")
        
        return retrieved_count > 0
    
    def test_large_file_posting(self):
        """Test posting larger segmented files"""
        self.log("\n" + "="*60)
        self.log("TESTING LARGE FILE SEGMENTATION AND POSTING")
        self.log("="*60)
        
        try:
            # Create a 2MB test file
            large_content = secrets.token_bytes(2 * 1024 * 1024)  # 2MB
            file_hash = hashlib.sha256(large_content).hexdigest()
            
            self.log(f"Created 2MB test file, hash: {file_hash[:16]}...")
            
            # Segment it (750KB per segment as configured)
            segment_size = 768000  # 750KB
            segments = []
            
            for i in range(0, len(large_content), segment_size):
                segment = large_content[i:i + segment_size]
                segments.append(segment)
            
            self.log(f"Split into {len(segments)} segments")
            
            # Post each segment
            segment_info = []
            
            for idx, segment in enumerate(segments):
                message_id = f"<{secrets.token_hex(16)}@ngPost.com>"
                subject = base64.b32encode(secrets.token_bytes(10)).decode().rstrip('=')
                
                # Build yEnc encoded article
                encoded = base64.b64encode(segment).decode('ascii')
                
                article_lines = [
                    f"From: anonymous@example.com",
                    f"Newsgroups: {self.server_config.get('posting_group', 'alt.binaries.test')}",
                    f"Subject: {subject}",
                    f"Message-ID: {message_id}",
                    f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}",
                    "",
                    f"=ybegin part={idx+1} total={len(segments)} line=128 size={len(segment)} name=largefile.bin",
                    f"=ypart begin={idx*segment_size+1} end={(idx+1)*segment_size}",
                    encoded,
                    f"=yend size={len(segment)} part={idx+1}"
                ]
                
                article = '\r\n'.join(article_lines)
                
                self.log(f"  Posting segment {idx+1}/{len(segments)}: {message_id}")
                
                try:
                    response = self.nntp_client.post(article)
                    self.log(f"    Posted! Response: {response}", "SUCCESS")
                    
                    segment_info.append({
                        "index": idx,
                        "message_id": message_id,
                        "subject": subject,
                        "size": len(segment),
                        "hash": hashlib.sha256(segment).hexdigest()
                    })
                    
                except Exception as e:
                    self.log(f"    Failed: {e}", "ERROR")
            
            self.log(f"\nPosted {len(segment_info)}/{len(segments)} segments successfully", 
                    "SUCCESS" if len(segment_info) == len(segments) else "WARNING")
            
            # Store for retrieval
            self.large_file_segments = segment_info
            return len(segment_info) > 0
            
        except Exception as e:
            self.log(f"Large file test failed: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """Close connection"""
        try:
            if hasattr(self, 'nntp_client'):
                self.nntp_client.quit()
                self.log("Connection closed", "SUCCESS")
        except:
            pass
    
    def generate_report(self):
        """Generate test report"""
        self.log("\n" + "="*60)
        self.log("REAL USENET TEST REPORT")
        self.log("="*60)
        
        # Save detailed results
        report = {
            "test_time": datetime.now().isoformat(),
            "server": self.server_config['hostname'],
            "posted_articles": self.posted_articles,
            "large_file_segments": getattr(self, 'large_file_segments', []),
            "results": self.results
        }
        
        with open('/workspace/real_usenet_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log("Report saved to: /workspace/real_usenet_test_report.json", "SUCCESS")
        
        # Summary
        self.log("\nSUMMARY:")
        self.log(f"  Articles posted: {len(self.posted_articles)}")
        self.log(f"  Articles retrieved: {sum(1 for r in self.results if 'Content verified' in r.get('message', ''))}")
        self.log(f"  Large file segments: {len(getattr(self, 'large_file_segments', []))}")


if __name__ == "__main__":
    tester = RealUsenetTest()
    
    try:
        # Connect
        if not tester.connect_to_usenet():
            print("Failed to connect to Usenet server!")
            sys.exit(1)
        
        # Run tests
        tester.test_real_posting()
        tester.test_real_retrieval()
        tester.test_large_file_posting()
        
        # Generate report
        tester.generate_report()
        
    finally:
        tester.cleanup()
    
    print("\n✅ REAL Usenet testing complete!")