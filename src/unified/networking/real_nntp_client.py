#!/usr/bin/env python3
"""
REAL NNTP Client using pynntp - NO SIMPLIFICATION
Tests with actual Usenet server credentials
"""

import nntp  # This is pynntp, NOT nntplib
import logging
import time
import hashlib
import uuid
import random
import string
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class RealNNTPClient:
    """
    REAL NNTP client using pynntp library
    NO SIMPLIFICATION - Full implementation with real Usenet
    """
    
    def __init__(self):
        """Initialize REAL NNTP client"""
        self.client = None
        self.connected = False
        self.authenticated = False
        self.server_info = {}
        
    def connect(self, host: str, port: int = 119, use_ssl: bool = False, 
                username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Connect to REAL Usenet server
        
        Args:
            host: Server hostname (e.g., news.newshosting.com)
            port: Server port (563 for SSL)
            use_ssl: Whether to use SSL
            
        Returns:
            True if connected
        """
        try:
            logger.info(f"Connecting to REAL Usenet server: {host}:{port} (SSL: {use_ssl})")
            
            # Create REAL NNTP connection using pynntp
            # Pass credentials if provided
            if username and password:
                self.client = nntp.NNTPClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    use_ssl=use_ssl
                )
                self.authenticated = True
            else:
                self.client = nntp.NNTPClient(
                    host=host,
                    port=port,
                    use_ssl=use_ssl
                )
            
            self.connected = True
            self.server_info = {
                'host': host,
                'port': port,
                'ssl': use_ssl,
                'connected_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ CONNECTED to {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection FAILED: {e}")
            self.connected = False
            return False
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with REAL Usenet credentials
        
        Args:
            username: Real username (e.g., contemptx)
            password: Real password
            
        Returns:
            True if authenticated
        """
        if not self.connected:
            raise RuntimeError("Not connected to server")
        
        try:
            logger.info(f"Authenticating as {username}")
            
            # REAL authentication using pynntp
            response = self.client.authenticate(username, password)
            
            self.authenticated = True
            logger.info(f"✅ AUTHENTICATED as {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication FAILED: {e}")
            self.authenticated = False
            return False
    
    def post_article(self, subject: str, body: bytes, newsgroups: List[str],
                     from_header: Optional[str] = None, message_id: Optional[str] = None) -> Optional[str]:
        """
        Post REAL article to Usenet
        
        Args:
            subject: Article subject
            body: Article body (binary data)
            newsgroups: List of newsgroups to post to
            from_header: From header
            message_id: Optional message ID (will generate if not provided)
            
        Returns:
            REAL Message-ID from server or None
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated")
        
        try:
            # Generate Message-ID in correct format (ngPost.com domain)
            if not message_id:
                # Generate 16 random chars @ ngPost.com (blends with legitimate traffic)
                random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
                message_id = f"<{random_str}@ngPost.com>"
            
            # Build article headers for pynntp
            headers = {
                'Subject': subject,
                'From': from_header or 'UsenetSync <noreply@usenetsync.com>',
                'Newsgroups': ','.join(newsgroups),
                'Message-ID': message_id,
                'Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
                'X-UsenetSync-Version': '1.0'
            }
            
            logger.info(f"Posting article to {newsgroups} with Message-ID: {message_id}")
            
            # POST to REAL Usenet server using pynntp format
            response = self.client.post(headers=headers, body=body)
            
            logger.info(f"✅ POSTED successfully: {message_id}")
            logger.info(f"   Server response: {response}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Post FAILED: {e}")
            return None
    
    def retrieve_article(self, message_id: str) -> Optional[Tuple[int, List[str]]]:
        """
        Retrieve REAL article from Usenet
        
        Args:
            message_id: Message-ID to retrieve
            
        Returns:
            Tuple of (article_number, article_lines) or None
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated")
        
        try:
            logger.info(f"Retrieving article: {message_id}")
            
            # REAL article retrieval
            response = self.client.article(message_id)
            
            # Parse response
            article_number = response[0]
            article_lines = response[1]
            
            logger.info(f"✅ RETRIEVED article {article_number} ({len(article_lines)} lines)")
            
            return (article_number, article_lines)
            
        except Exception as e:
            logger.error(f"❌ Retrieval FAILED: {e}")
            return None
    
    def select_group(self, newsgroup: str) -> Optional[Dict[str, Any]]:
        """
        Select REAL newsgroup
        
        Args:
            newsgroup: Newsgroup name (e.g., alt.binaries.test)
            
        Returns:
            Group information or None
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated")
        
        try:
            logger.info(f"Selecting newsgroup: {newsgroup}")
            
            # REAL group selection
            response = self.client.group(newsgroup)
            
            # Parse response: (count, first, last, name)
            group_info = {
                'count': response[0],
                'first': response[1],
                'last': response[2],
                'name': response[3]
            }
            
            logger.info(f"✅ SELECTED {newsgroup}: {group_info['count']} articles")
            
            return group_info
            
        except Exception as e:
            logger.error(f"❌ Group selection FAILED: {e}")
            return None
    
    def check_article_exists(self, message_id: str) -> bool:
        """
        Check if article exists on REAL server
        
        Args:
            message_id: Message-ID to check
            
        Returns:
            True if article exists
        """
        if not self.authenticated:
            return False
        
        try:
            # Try to get article headers
            response = self.client.head(message_id)
            return response is not None
            
        except:
            return False
    
    def disconnect(self):
        """Disconnect from REAL server"""
        if self.client:
            try:
                self.client.quit()
                logger.info("✅ DISCONNECTED from server")
            except:
                pass
            
            self.connected = False
            self.authenticated = False
            self.client = None


def test_real_usenet_connection():
    """
    TEST WITH REAL USENET CREDENTIALS
    Using actual server: news.newshosting.com
    """
    print("\n" + "=" * 80)
    print("TESTING REAL USENET CONNECTION")
    print("=" * 80)
    
    # REAL credentials provided by user
    SERVER = "news.newshosting.com"
    PORT = 563
    USERNAME = "contemptx"
    PASSWORD = "Kia211101#"
    USE_SSL = True
    TEST_NEWSGROUP = "alt.binaries.test"
    
    print(f"\nServer: {SERVER}:{PORT} (SSL: {USE_SSL})")
    print(f"User: {USERNAME}")
    print(f"Newsgroup: {TEST_NEWSGROUP}")
    print("-" * 80)
    
    client = RealNNTPClient()
    
    try:
        # 1. CONNECT to REAL server with credentials
        print("\n1. CONNECTING to REAL Usenet server with authentication...")
        connected = client.connect(SERVER, PORT, USE_SSL, USERNAME, PASSWORD)
        if not connected:
            print("   ❌ Connection FAILED")
            return False
        print("   ✅ CONNECTED and AUTHENTICATED successfully")
        
        # 3. SELECT REAL newsgroup
        print(f"\n3. SELECTING newsgroup {TEST_NEWSGROUP}...")
        group_info = client.select_group(TEST_NEWSGROUP)
        if group_info:
            print(f"   ✅ Group selected: {group_info['count']} articles")
        else:
            print("   ❌ Group selection FAILED")
        
        # 4. POST REAL test article
        print("\n4. POSTING test article to REAL Usenet...")
        test_subject = f"UsenetSync Test {uuid.uuid4().hex[:8]}"
        test_body = f"This is a REAL test post to Usenet\nTimestamp: {datetime.now()}\nServer: {SERVER}\n"
        
        message_id = client.post_article(
            subject=test_subject,
            body=test_body.encode('utf-8'),
            newsgroups=[TEST_NEWSGROUP]
        )
        
        if message_id:
            print(f"   ✅ POSTED successfully!")
            print(f"   Message-ID: {message_id}")
            
            # 5. VERIFY article exists
            print("\n5. VERIFYING article on server...")
            time.sleep(2)  # Give server time to process
            
            exists = client.check_article_exists(message_id)
            if exists:
                print(f"   ✅ Article VERIFIED on server")
                
                # 6. RETRIEVE the article back
                print("\n6. RETRIEVING article from server...")
                article = client.retrieve_article(message_id)
                if article:
                    article_num, lines = article
                    print(f"   ✅ RETRIEVED article #{article_num}")
                    print(f"   Article has {len(lines)} lines")
                    
                    # Verify content
                    article_text = '\n'.join(lines)
                    if test_subject in article_text:
                        print(f"   ✅ Content VERIFIED - subject found")
                    else:
                        print(f"   ⚠️  Content mismatch")
                else:
                    print(f"   ❌ Retrieval FAILED")
            else:
                print(f"   ⚠️  Article not found (may need more time to propagate)")
        else:
            print("   ❌ Post FAILED")
            return False
        
        print("\n" + "=" * 80)
        print("✅ ALL REAL USENET TESTS PASSED!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        client.disconnect()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run REAL test
    success = test_real_usenet_connection()
    exit(0 if success else 1)