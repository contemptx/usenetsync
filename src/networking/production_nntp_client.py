#!/usr/bin/env python3
"""
Production-ready NNTP client with connection pooling, retry logic, and robust error handling.
Supports posting millions of files with high performance and reliability.
"""

# Use pynntp which provides the nntp module
from nntp import NNTPClient
import time
import logging
import threading
import queue
import socket
import ssl
from datetime import datetime
from collections import deque
from contextlib import contextmanager
import hashlib
import random
import string
import email.utils
from typing import Optional, Tuple, Dict, List, Any
import re
import getpass
from dataclasses import dataclass, asdict

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration for NNTP client"""
    name: str
    hostname: str
    port: int
    username: str
    password: str
    posting_group: str = "alt.binaries.test"
    use_ssl: bool = True
    max_connections: int = 10
    priority: int = 1
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create from dictionary"""
        return cls(**data)


class ConnectionStats:
    """Track connection statistics for monitoring"""
    def __init__(self):
        self.posts_successful = 0
        self.posts_failed = 0
        self.connections_created = 0
        self.connections_failed = 0
        self.connections_recycled = 0
        self.total_bytes_posted = 0
        self.total_post_time = 0
        self._lock = threading.Lock()
    
    def record_post(self, success, bytes_posted=0, duration=0):
        with self._lock:
            if success:
                self.posts_successful += 1
                self.total_bytes_posted += bytes_posted
                self.total_post_time += duration
            else:
                self.posts_failed += 1
    
    def record_connection(self, action, success=True):
        with self._lock:
            if action == 'create':
                if success:
                    self.connections_created += 1
                else:
                    self.connections_failed += 1
            elif action == 'recycle':
                self.connections_recycled += 1
    
    def get_stats(self):
        with self._lock:
            avg_post_time = self.total_post_time / self.posts_successful if self.posts_successful > 0 else 0
            return {
                'posts_successful': self.posts_successful,
                'posts_failed': self.posts_failed,
                'success_rate': self.posts_successful / (self.posts_successful + self.posts_failed) if (self.posts_successful + self.posts_failed) > 0 else 0,
                'connections_created': self.connections_created,
                'connections_failed': self.connections_failed,
                'connections_recycled': self.connections_recycled,
                'total_bytes_posted': self.total_bytes_posted,
                'average_post_time': avg_post_time
            }


class NNTPConnection:
    """Wrapper for NNTP connection with health checking"""
    def __init__(self, host, port, username, password, use_ssl=True, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.connection = None
        self.created_at = None
        self.last_used = None
        self.post_count = 0
        self.is_authenticated = False
        self._lock = threading.Lock()
    
    def connect(self):
        """Establish connection to NNTP server"""
        try:
            # Use NNTPClient from nntp module
            # IMPORTANT: use_ssl parameter is required for SSL connections!
            self.connection = NNTPClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_ssl=self.use_ssl,  # Critical for port 563!
                timeout=self.timeout
            )
            
            self.is_authenticated = True
            self.created_at = time.time()
            self.last_used = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port} - {e}")
            self.connection = None
            return False
    
    def is_healthy(self, max_age=300, max_posts=1000):
        """Check if connection is healthy"""
        if not self.connection:
            return False
        
        with self._lock:
            # Check age
            if time.time() - self.created_at > max_age:
                return False
            
            # Check post count
            if self.post_count >= max_posts:
                return False
            
            # Try a simple command to test connection
            try:
                # pynntp doesn't have a date() method, so we'll just check if connection exists
                # and hasn't exceeded limits
                return True
            except:
                return False
    
    def post(self, data):
        """Post article to server using pynntp"""
        with self._lock:
            if not self.connection:
                raise Exception("Connection not established")
            
            # Store the Message-ID we're sending
            sent_message_id = None
            
            # pynntp's post method expects (headers_dict, body_string)
            # We receive data as bytes, so we need to parse it
            
            if isinstance(data, bytes):
                # Decode and split headers from body
                try:
                    data_str = data.decode('utf-8')
                except UnicodeDecodeError:
                    # Handle binary data - split at header boundary first
                    header_end = data.find(b'\r\n\r\n')
                    if header_end == -1:
                        header_end = data.find(b'\n\n')
                        if header_end == -1:
                            raise Exception("Invalid message format")
                        body_start = header_end + 2
                    else:
                        body_start = header_end + 4
                    
                    # Headers should be decodable as UTF-8
                    header_data = data[:header_end].decode('utf-8', errors='replace')
                    body_data = data[body_start:]  # Keep body as bytes for now
                    
                    # Convert body to base64 for binary data
                    import base64
                    body_str = base64.b64encode(body_data).decode('ascii')
                    headers_need_encoding = True
                else:
                    # Successfully decoded as UTF-8
                    # Split headers and body
                    if '\r\n\r\n' in data_str:
                        header_part, body_str = data_str.split('\r\n\r\n', 1)
                    elif '\n\n' in data_str:
                        header_part, body_str = data_str.split('\n\n', 1)
                    else:
                        header_part = data_str
                        body_str = ''
                    header_data = header_part
                    headers_need_encoding = False
                
                # Parse headers into dict
                headers = {}
                for line in header_data.split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        headers[key] = value
                        
                        # Capture the Message-ID we're sending
                        if key.lower() == 'message-id':
                            sent_message_id = value
                
                # Add encoding headers if needed
                if headers_need_encoding and 'Content-Transfer-Encoding' not in headers:
                    headers['Content-Transfer-Encoding'] = 'base64'
                
                # Try to post with pynntp format
                try:
                    result = self.connection.post(headers, body_str)
                except Exception as e:
                    # If that fails, try posting the raw data
                    logger.debug(f"Dict/body post failed: {e}, trying raw bytes")
                    # Don't try raw bytes - it won't work with pynntp
                    # result = self.connection.post(data)
                    raise e  # Re-raise the original exception
            
            else:
                # Already in the correct format (headers dict, body string)
                result = self.connection.post(data)
            
            self.post_count += 1
            self.last_used = time.time()
            
            # Return standardized response with actual message ID if we have it
            if isinstance(result, bool):
                if result:
                    return (240, sent_message_id if sent_message_id else '<posted>')
                else:
                    return (441, 'Posting failed')
            elif hasattr(result, 'code'):
                msg_id = sent_message_id if sent_message_id else getattr(result, 'message_id', '<posted>')
                return (result.code, msg_id)
            else:
                return (240, sent_message_id if sent_message_id else '<posted>')

    def retrieve_article(self, message_id: str, newsgroup: str) -> Optional[bytes]:
        """Retrieve article by message ID"""
        with self._lock:
            if not self.connection:
                raise Exception("Connection not established")
            
            try:
                # pynntp uses a different API than nntplib
                # First, ensure we're in the right group
                self.connection.group(newsgroup)
                
                # Retrieve article by message ID
                # pynntp returns: (status_code, headers, body)
                response = self.connection.article(message_id)
                
                if response:
                    # Handle pynntp's response format
                    if isinstance(response, tuple) and len(response) >= 3:
                        # response[0] = status code (0 for success)
                        # response[1] = HeaderDict with headers
                        # response[2] = body as bytes
                        status_code = response[0]
                        headers = response[1]
                        body = response[2]
                        
                        # Return the body directly
                        if isinstance(body, bytes):
                            return body
                        elif isinstance(body, str):
                            return body.encode('utf-8', errors='replace')
                        else:
                            # If body is something else, try to convert it
                            return str(body).encode('utf-8', errors='replace')
                    
                    # Fallback for unexpected response format
                    elif isinstance(response, bytes):
                        return response
                    elif isinstance(response, str):
                        return response.encode('utf-8', errors='replace')
                        
                return None
                        
            except Exception as e:
                logger.error(f"Failed to retrieve article {message_id}: {e}")
                return None

    def close(self):
        """Close the connection"""
        with self._lock:
            if self.connection:
                try:
                    self.connection.quit()
                except:
                    pass
                self.connection = None


class ConnectionPool:
    """Thread-safe connection pool for NNTP connections"""
    def __init__(self, host, port, username, password, use_ssl=True, 
                 max_connections=10, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.max_connections = max_connections
        self.timeout = timeout
        
        self.pool = queue.Queue(maxsize=max_connections)
        self.all_connections = []
        self._lock = threading.Lock()
        self.stats = ConnectionStats()
        
        # Initialize pool with connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create initial connections for the pool"""
        logger.info(f"Initializing pool with {self.max_connections} connections")
        for _ in range(self.max_connections):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
                self.all_connections.append(conn)
    
    def _create_connection(self):
        """Create a new NNTP connection"""
        conn = NNTPConnection(
            self.host, self.port, self.username, 
            self.password, self.use_ssl, self.timeout
        )
        
        if conn.connect():
            self.stats.record_connection('create', True)
            return conn
        else:
            self.stats.record_connection('create', False)
            return None
    
    @contextmanager
    def get_connection(self, timeout=5):
        """Get a connection from the pool"""
        connection = None
        try:
            # Try to get a healthy connection
            attempts = 0
            while attempts < 3:
                try:
                    connection = self.pool.get(timeout=timeout)
                    
                    # Check if connection is healthy
                    if connection.is_healthy():
                        yield connection
                        return
                    else:
                        # Connection is unhealthy, close and create new one
                        logger.debug("Recycling unhealthy connection")
                        connection.close()
                        self.stats.record_connection('recycle')
                        
                        new_conn = self._create_connection()
                        if new_conn:
                            connection = new_conn
                            yield connection
                            return
                        
                except queue.Empty:
                    logger.warning("Connection pool exhausted")
                    raise Exception("No available connections in pool")
                
                attempts += 1
            
            raise Exception("Failed to get healthy connection after 3 attempts")
            
        finally:
            # Return connection to pool
            if connection:
                self.pool.put(connection)
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            # Empty the queue
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                except:
                    pass
            
            # Close any remaining connections
            for conn in self.all_connections:
                try:
                    conn.close()
                except:
                    pass
            
            self.all_connections.clear()
    
    def get_stats(self):
        """Get pool statistics"""
        stats = self.stats.get_stats()
        stats['pool_size'] = self.pool.qsize()
        stats['max_connections'] = self.max_connections
        return stats


class ProductionNNTPClient:
    """High-performance NNTP client for production use"""
    
    def __init__(self, host, port, username, password, use_ssl=True, 
                 max_connections=10, max_retries=3, retry_delay=1.0,
                 timeout=30, user_agent="UsenetSync/1.0"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        
        # Initialize connection pool
        self.connection_pool = ConnectionPool(
            host, port, username, password, 
            use_ssl, max_connections, timeout
        )
        
        logger.info(f"Initialized NNTP client for {host}:{port} with {max_connections} connections")
    
    @classmethod
    def from_config(cls):
        """Create client instance from secure configuration"""
        try:
            from secure_config import default_config
            config = default_config.get_client_config()
            
            return cls(
                host=config['host'],
                port=config['port'],
                username=config['username'],
                password=config['password'],
                use_ssl=config['use_ssl'],
                max_connections=config.get('max_connections', 10),
                timeout=config.get('timeout', 30)
            )
        except ImportError:
            logger.warning("secure_config not found, trying environment variables")
            # Fallback to environment variables
            import os
            username = os.environ.get('NNTP_USERNAME')
            password = os.environ.get('NNTP_PASSWORD')
            
            if not username or not password:
                raise ValueError(
                    "Credentials not configured! Set environment variables:\n"
                    "  set NNTP_USERNAME=your_username\n"
                    "  set NNTP_PASSWORD=your_password\n"
                    "Or create secure_config.py"
                )
            
            return cls(
                host=os.environ.get('NNTP_HOST', 'news.newshosting.com'),
                port=int(os.environ.get('NNTP_PORT', '563')),
                username=username,
                password=password,
                use_ssl=True,
                max_connections=10
            )
    
    def _generate_message_id(self, prefix="usync"):
        """Generate unique message ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        host_part = self.host.replace('.', '-')
        return f"<{prefix}-{timestamp}-{random_str}@{host_part}>"
    
    def _build_headers(self, subject, newsgroup, from_user=None, 
                      message_id=None, extra_headers=None):
        """Build message headers"""
        headers = {}
        
        # Required headers
        headers['From'] = from_user or f"poster@{self.host}"
        headers['Newsgroups'] = newsgroup
        headers['Subject'] = subject.replace('_', ' ').strip() if subject else 'No Subject'
        headers['Message-ID'] = message_id or self._generate_message_id()
        headers['Date'] = email.utils.formatdate(localtime=True)
        headers['User-Agent'] = self.user_agent
        
        # Optional headers
        headers['X-No-Archive'] = 'yes'
        
        # Add any extra headers
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    def _format_message(self, headers, data):
        """Format message with headers and body"""
        # Build header lines
        header_lines = []
        for key, value in headers.items():
            # Ensure no newlines in header values
            value = str(value).replace('\r', '').replace('\n', ' ')
            header_lines.append(f"{key}: {value}")
        
        # Combine headers and body
        message = '\r\n'.join(header_lines) + '\r\n\r\n'
        
        # Add body
        # Check if data contains binary/control characters
        if isinstance(data, bytes):
            try:
                data.decode("utf-8")
                # Check for control characters
                if any(0 <= b < 32 for b in data):
                    raise UnicodeDecodeError("ascii", b"", 0, 1, "control chars")
            except UnicodeDecodeError:
                # Binary data - must use base64
                import base64
                headers["Content-Type"] = "application/octet-stream"
                headers["Content-Transfer-Encoding"] = "base64"
                encoded = base64.b64encode(data).decode("ascii")
                message = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
                message += "\r\n\r\n" + encoded
                return message.encode("utf-8")
        
        if isinstance(data, bytes):
            message = message.encode('utf-8') + data
        else:
            message = message.encode('utf-8') + str(data).encode('utf-8')
        
        return message
    
    def post_data(self, subject, data, newsgroup, from_user=None, message_id=None, extra_headers=None):
        """Post data with specified headers"""
        headers = self._build_headers(
            subject=subject,
            newsgroup=newsgroup,
            from_user=from_user,
            message_id=message_id,
            extra_headers=extra_headers
        )
        
        message = self._format_message(headers, data)
        
        # Post with retry logic
        return self._post_with_retry(message, headers.get('Message-ID'))
    
    def _post_with_retry(self, message, message_id):
        """Post message with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                with self.connection_pool.get_connection() as conn:
                    response = conn.post(message)
                    
                    duration = time.time() - start_time
                    self.connection_pool.stats.record_post(True, len(message), duration)
                    
                    logger.debug(f"Posted message {message_id} successfully in {duration:.2f}s")
                    return True, response
                    
            except Exception as e:
                last_error = e
                self.connection_pool.stats.record_post(False)
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Post failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to post message {message_id} after {self.max_retries} attempts: {e}")
        
        return False, str(last_error)
    
    def post_file(self, file_path, subject, newsgroup, from_user=None, 
                  message_id=None, extra_headers=None, chunk_size=8192):
        """Post a file efficiently"""
        try:
            # Read file in chunks to handle large files
            with open(file_path, 'rb') as f:
                # For very large files, you might want to post in parts
                # This example posts the whole file
                data = f.read()
            
            return self.post_data(
                subject=subject,
                data=data,
                newsgroup=newsgroup,
                from_user=from_user,
                message_id=message_id,
                extra_headers=extra_headers
            )
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return False, str(e)
    
    def post_multipart(self, parts, subject, newsgroup, from_user=None,
                      message_id_prefix=None, extra_headers=None):
        """Post multipart message"""
        results = []
        base_message_id = message_id_prefix or self._generate_message_id("multipart")
        
        # Remove the angle brackets from base message ID if present
        if base_message_id.startswith('<') and base_message_id.endswith('>'):
            base_id_core = base_message_id[1:-1]
        else:
            base_id_core = base_message_id
        
        for i, part_data in enumerate(parts):
            part_subject = f"{subject} [{i+1}/{len(parts)}]"
            # Create a valid message ID - no dots before @ symbol
            part_message_id = f"<{base_id_core}-p{i+1}@{self.host.replace('.', '-')}>"
            
            # Add part-specific headers
            part_headers = extra_headers.copy() if extra_headers else {}
            if i > 0:
                part_headers['References'] = base_message_id
            
            success, response = self.post_data(
                subject=part_subject,
                data=part_data,
                newsgroup=newsgroup,
                from_user=from_user,
                message_id=part_message_id,
                extra_headers=part_headers
            )
            
            results.append((success, response))
            
            if not success:
                logger.error(f"Failed to post part {i+1} of multipart message")
                break
        
        return results
    
    def batch_post(self, posts, progress_callback=None):
        """Post multiple messages in batch"""
        results = []
        total = len(posts)
        
        for i, post_data in enumerate(posts):
            success, response = self.post_data(**post_data)
            results.append((success, response))
            
            if progress_callback:
                progress_callback(i + 1, total, success)
        
        return results
    
    def get_stats(self):
        """Get client statistics"""
        return self.connection_pool.get_stats()
    
    def retrieve_article(self, message_id: str, newsgroup: str) -> Optional[bytes]:
        """Retrieve article from Usenet"""
        try:
            with self.connection_pool.get_connection() as conn:
                return conn.retrieve_article(message_id, newsgroup)
        except Exception as e:
            logger.error(f"Error retrieving article: {e}")
            return None
    
    def close(self):
        """Close all connections"""
        logger.info("Closing NNTP client connections")
        self.connection_pool.close_all()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Helper functions for common operations
def create_yenc_headers(filename, part=1, total=1, size=0, line_length=128):
    """Create yEnc headers for file posting"""
    headers = {
        'X-yEnc': 'yes',
        'X-yEnc-Part': f"{part}/{total}",
        'X-yEnc-Size': str(size),
        'X-yEnc-Line': str(line_length),
        'X-yEnc-Name': filename
    }
    return headers


def split_file_for_posting(file_path, max_size=500000):
    """Split large file into chunks for posting"""
    chunks = []
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(max_size)
            if not chunk:
                break
            chunks.append(chunk)
    
    return chunks


def create_client_from_config():
    """Create NNTP client using secure configuration"""
    try:
        from secure_config import default_config
        config = default_config.get_client_config()
        
        return ProductionNNTPClient(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            use_ssl=config['use_ssl'],
            max_connections=config.get('max_connections', 10),
            timeout=config.get('timeout', 30)
        )
    except ImportError:
        logger.warning("secure_config not found, using environment variables")
        # Fallback to environment variables
        import os
        username = os.environ.get('NNTP_USERNAME')
        password = os.environ.get('NNTP_PASSWORD')
        
        if not username or not password:
            raise ValueError(
                "Credentials not configured! Set environment variables:\n"
                "  set NNTP_USERNAME=your_username\n"
                "  set NNTP_PASSWORD=your_password"
            )
        
        return ProductionNNTPClient(
            host=os.environ.get('NNTP_HOST', 'news.newshosting.com'),
            port=int(os.environ.get('NNTP_PORT', '563')),
            username=username,
            password=password,
            use_ssl=True,
            max_connections=10
        )
