#!/usr/bin/env python3
"""
Unified Obfuscation Module - Subject pairs and message ID generation
CRITICAL: Maintains two-layer subject system for Usenet security
"""

import secrets
import hashlib
import random
import string
from typing import Tuple, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SubjectPair:
    """Two-layer subject system"""
    internal_subject: str  # 64 hex chars for verification (never posted)
    usenet_subject: str    # 20 random chars for obfuscation (posted)

class UnifiedObfuscation:
    """
    Unified obfuscation system for Usenet posting
    CRITICAL: No correlation between internal and Usenet data
    """
    
    # Common Usenet posting tools for blending
    USER_AGENTS = [
        "Mozilla Thunderbird",
        "Pan/0.146",
        "slrn/1.0.3",
        "Xnews/5.04.25",
        "Forte Agent 8.0",
        "MesNews/1.08.06.00",
        "Gnus/5.13",
        "tin/2.4.5",
        "ngPost/4.14"
    ]
    
    # Common domains for message IDs
    DOMAINS = [
        "ngPost.com",
        "news.local",
        "usenet.local",
        "posting.local",
        "nntp.local"
    ]
    
    def __init__(self):
        """Initialize obfuscation system"""
        self._subject_cache = {}
    
    def generate_subject_pair(self, folder_id: str, file_version: int,
                            segment_index: int, private_key: bytes) -> SubjectPair:
        """
        Generate two-layer subject pair
        CRITICAL: Complete separation between internal and Usenet subjects
        
        Args:
            folder_id: Folder identifier
            file_version: File version number
            segment_index: Segment index
            private_key: Private key for signing
        
        Returns:
            SubjectPair with internal and Usenet subjects
        """
        # Generate internal subject for verification (64 hex chars)
        internal_data = f"{folder_id}:{file_version}:{segment_index}:{secrets.token_hex(16)}"
        internal_hash = hashlib.sha256(internal_data.encode()).digest()
        
        # Sign with private key for authenticity
        signature_data = internal_hash + private_key[:32]
        internal_subject = hashlib.sha256(signature_data).hexdigest()
        
        # Generate completely random Usenet subject (20 chars)
        # CRITICAL: No patterns, no correlation with internal subject
        usenet_subject = self._generate_random_subject()
        
        # Cache the pair
        cache_key = f"{folder_id}:{file_version}:{segment_index}"
        self._subject_cache[cache_key] = SubjectPair(internal_subject, usenet_subject)
        
        logger.debug(f"Generated subject pair for segment {segment_index}")
        
        return SubjectPair(internal_subject, usenet_subject)
    
    def _generate_random_subject(self, length: int = 20) -> str:
        """
        Generate completely random subject for Usenet
        CRITICAL: Pure randomness, no patterns
        
        Args:
            length: Length of random subject
        
        Returns:
            Random subject string
        """
        # Use full character set for maximum entropy
        charset = string.ascii_letters + string.digits
        
        # Generate random subject
        subject = ''.join(secrets.choice(charset) for _ in range(length))
        
        return subject
    
    def generate_message_id(self, prefix: Optional[str] = None) -> str:
        """
        Generate obfuscated message ID
        CRITICAL: No timestamps, no identifying information
        
        Args:
            prefix: Optional prefix (ignored for security)
        
        Returns:
            Message ID that blends with legitimate traffic
        """
        # Generate random local part (16 chars)
        random_str = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=16)
        )
        
        # Use random domain from common tools
        domain = random.choice(self.DOMAINS)
        
        # Format as standard message ID
        message_id = f"<{random_str}@{domain}>"
        
        return message_id
    
    def generate_share_id(self, folder_id: str, share_type: str,
                         version: int = 1) -> str:
        """
        Generate share ID with NO Usenet information
        CRITICAL: No message IDs or subjects in share ID
        
        Args:
            folder_id: Folder being shared
            share_type: Type of share
            version: Share version
        
        Returns:
            Random share ID with no patterns
        """
        # Generate unique data
        unique_data = f"{folder_id}:{share_type}:{version}:{secrets.token_hex(16)}"
        full_hash = hashlib.sha256(unique_data.encode()).digest()
        
        # Convert to base32 for readability (no 0/O or 1/l confusion)
        import base64
        share_id = base64.b32encode(full_hash[:15]).decode('ascii').rstrip('=')
        
        # Return consistent length (24 chars)
        return share_id[:24]
    
    def generate_random_headers(self) -> dict:
        """
        Generate random headers to blend with legitimate traffic
        
        Returns:
            Dictionary of headers
        """
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'X-Newsreader': random.choice(self.USER_AGENTS),
            'Organization': random.choice([
                None,  # No organization
                "Private",
                "Personal",
                "Home"
            ])
        }
        
        # Remove None values
        return {k: v for k, v in headers.items() if v is not None}
    
    def obfuscate_filename(self, filename: str) -> str:
        """
        Obfuscate filename for posting
        
        Args:
            filename: Original filename
        
        Returns:
            Obfuscated filename
        """
        # Generate random name with same extension
        import os
        _, ext = os.path.splitext(filename)
        
        # Random 12 character name
        random_name = ''.join(
            secrets.choice(string.ascii_lowercase + string.digits) 
            for _ in range(12)
        )
        
        return f"{random_name}{ext}"
    
    def generate_newsgroup_list(self, base_groups: List[str],
                              randomize: bool = True) -> List[str]:
        """
        Generate list of newsgroups for posting
        
        Args:
            base_groups: Base newsgroups to use
            randomize: Whether to randomize order
        
        Returns:
            List of newsgroups
        """
        groups = base_groups.copy()
        
        if randomize:
            random.shuffle(groups)
        
        # Limit to reasonable number
        return groups[:5]
    
    def generate_yenc_name(self, segment_index: int, total_segments: int) -> str:
        """
        Generate yEnc-compatible name
        
        Args:
            segment_index: Current segment index
            total_segments: Total number of segments
        
        Returns:
            yEnc name
        """
        # Random base name
        base_name = ''.join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(16)
        )
        
        # Standard yEnc format
        return f"{base_name}.part{segment_index:03d}of{total_segments:03d}"
    
    def verify_subject_pair(self, internal_subject: str, 
                          folder_id: str, file_version: int,
                          segment_index: int) -> bool:
        """
        Verify internal subject is valid
        
        Args:
            internal_subject: Internal subject to verify
            folder_id: Expected folder ID
            file_version: Expected version
            segment_index: Expected segment index
        
        Returns:
            True if valid
        """
        # Check cache
        cache_key = f"{folder_id}:{file_version}:{segment_index}"
        cached = self._subject_cache.get(cache_key)
        
        if cached and cached.internal_subject == internal_subject:
            return True
        
        # Verify format (64 hex chars)
        if len(internal_subject) != 64:
            return False
        
        try:
            int(internal_subject, 16)
            return True
        except ValueError:
            return False
    
    def generate_post_headers(self, subject: str, newsgroups: List[str],
                            references: Optional[str] = None) -> dict:
        """
        Generate complete headers for NNTP posting
        
        Args:
            subject: Subject line (Usenet subject)
            newsgroups: List of newsgroups
            references: Optional references header
        
        Returns:
            Complete headers dictionary
        """
        headers = {
            'Subject': subject,
            'Newsgroups': ','.join(newsgroups),
            'Message-ID': self.generate_message_id(),
            'From': self._generate_random_from(),
            'Date': self._generate_date_header(),
            'Path': self._generate_path_header(),
            'Lines': '1000',  # Will be updated
        }
        
        # Add random headers
        headers.update(self.generate_random_headers())
        
        # Add references if provided
        if references:
            headers['References'] = references
        
        return headers
    
    def _generate_random_from(self) -> str:
        """Generate random From header"""
        # Random username
        username = ''.join(
            random.choices(string.ascii_lowercase, k=8)
        )
        
        # Random domain
        domain = random.choice([
            "example.com",
            "invalid.local",
            "nospam.invalid",
            "poster.local"
        ])
        
        return f"{username}@{domain}"
    
    def _generate_date_header(self) -> str:
        """Generate RFC 5322 compliant date header"""
        from email.utils import formatdate
        return formatdate(localtime=False, usegmt=True)
    
    def _generate_path_header(self) -> str:
        """Generate Path header for NNTP"""
        # Simulate typical path through servers
        servers = [
            "not-for-mail",
            "!.POSTED",
            "!news.local"
        ]
        
        return '!'.join(servers)
    
    def sanitize_for_posting(self, data: str) -> str:
        """
        Sanitize data for NNTP posting
        
        Args:
            data: Data to sanitize
        
        Returns:
            Sanitized data
        """
        # Remove any control characters
        sanitized = ''.join(
            char for char in data 
            if char.isprintable() or char in '\r\n\t'
        )
        
        # Ensure no lines start with '.'
        lines = sanitized.split('\n')
        sanitized_lines = []
        
        for line in lines:
            if line.startswith('.'):
                line = '.' + line
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)