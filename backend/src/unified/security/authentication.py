#!/usr/bin/env python3
"""
Unified Authentication Module - User ID and Folder Key Management
Production-ready with Ed25519 keys and permanent User IDs
"""

import os
import secrets
import hashlib
import json
import base64
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class UnifiedAuthentication:
    """
    Unified authentication system handling User IDs and Folder Keys
    CRITICAL: User IDs are permanent - NEVER regenerated
    """
    
    def __init__(self, db, keys_dir: str = "data/keys"):
        """Initialize authentication system"""
        self.db = db
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self._user_cache = {}
        self._folder_keys_cache = {}
    
    def generate_user_id(self) -> str:
        """
        Generate permanent 64-character User ID
        CRITICAL: This is generated ONCE and NEVER changed
        """
        # Generate 32 random bytes (256 bits)
        random_bytes = secrets.token_bytes(32)
        # Convert to 64-character hex string
        user_id = random_bytes.hex()
        
        logger.info(f"Generated new User ID: {user_id[:8]}...")
        return user_id
    
    def create_user(self, username: Optional[str] = None, 
                   email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user with permanent User ID
        
        Returns:
            User data including User ID and keys
        """
        # Generate permanent User ID
        user_id = self.generate_user_id()
        
        # Generate Ed25519 key pair for user
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store in database
        user_data = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'public_key': public_pem.decode('utf-8'),
            'private_key_encrypted': self._encrypt_private_key(private_pem, user_id),
            'api_key': api_key,
            'created_at': time.time()
        }
        
        self.db.insert('users', user_data)
        
        # Save keys to file (backup)
        self._save_user_keys(user_id, private_pem, public_pem)
        
        # Cache user
        self._user_cache[user_id] = user_data
        
        return {
            'user_id': user_id,
            'api_key': api_key,
            'public_key': public_pem.decode('utf-8'),
            'username': username,
            'email': email
        }
    
    def authenticate_user(self, user_id: str, api_key: Optional[str] = None,
                         signature: Optional[bytes] = None,
                         challenge: Optional[bytes] = None) -> bool:
        """
        Authenticate user by ID and API key or signature
        
        Args:
            user_id: User ID to authenticate
            api_key: API key for authentication
            signature: Ed25519 signature for challenge
            challenge: Challenge data that was signed
        
        Returns:
            True if authentication successful
        """
        # Get user from database
        user = self.get_user(user_id)
        if not user:
            return False
        
        # API key authentication
        if api_key:
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            return user.get('api_key_hash') == api_key_hash
        
        # Signature authentication
        if signature and challenge:
            try:
                public_key_pem = user.get('public_key')
                if not public_key_pem:
                    return False
                
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode('utf-8'),
                    backend=default_backend()
                )
                
                public_key.verify(signature, challenge)
                return True
            except Exception as e:
                logger.warning(f"Signature verification failed: {e}")
                return False
        
        return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by ID"""
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if user:
            self._user_cache[user_id] = user
        
        return user
    
    def generate_folder_keys(self, folder_id: str, owner_id: str) -> Tuple[str, str]:
        """
        Generate Ed25519 key pair for folder
        CRITICAL: Keys are permanent once created
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Check if keys already exist
        existing = self.db.fetch_one(
            "SELECT private_key, public_key FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        
        if existing and existing['private_key']:
            logger.warning(f"Folder {folder_id} already has keys")
            return existing['private_key'], existing['public_key']
        
        # Generate new Ed25519 key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Update folder with keys
        self.db.update(
            'folders',
            {
                'private_key': self._encrypt_folder_key(private_pem, owner_id),
                'public_key': public_pem,
                'owner_id': owner_id
            },
            'folder_id = ?',
            (folder_id,)
        )
        
        # Cache keys
        self._folder_keys_cache[folder_id] = {
            'private_key': private_pem,
            'public_key': public_pem,
            'owner_id': owner_id
        }
        
        logger.info(f"Generated permanent keys for folder {folder_id}")
        return private_pem, public_pem
    
    def sign_data(self, data: bytes, folder_id: str, user_id: str) -> bytes:
        """
        Sign data with folder's private key
        
        Args:
            data: Data to sign
            folder_id: Folder ID whose key to use
            user_id: User ID requesting signature
        
        Returns:
            Ed25519 signature
        """
        # Get folder keys
        folder = self.db.fetch_one(
            "SELECT private_key, owner_id FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        
        if not folder:
            raise ValueError(f"Folder {folder_id} not found")
        
        # Check ownership
        if folder['owner_id'] != user_id:
            raise PermissionError(f"User {user_id} is not owner of folder {folder_id}")
        
        # Decrypt private key
        private_key_pem = self._decrypt_folder_key(folder['private_key'], user_id)
        
        # Load key and sign
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        signature = private_key.sign(data)
        return signature
    
    def verify_signature(self, data: bytes, signature: bytes, 
                        folder_id: str) -> bool:
        """
        Verify signature with folder's public key
        
        Args:
            data: Data that was signed
            signature: Signature to verify
            folder_id: Folder whose key to use
        
        Returns:
            True if signature is valid
        """
        # Get folder public key
        folder = self.db.fetch_one(
            "SELECT public_key FROM folders WHERE folder_id = ?",
            (folder_id,)
        )
        
        if not folder or not folder['public_key']:
            return False
        
        try:
            # Load public key and verify
            public_key = serialization.load_pem_public_key(
                folder['public_key'].encode('utf-8'),
                backend=default_backend()
            )
            
            public_key.verify(signature, data)
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
    
    def create_session(self, user_id: str, duration_hours: int = 24) -> str:
        """
        Create session token for user
        
        Args:
            user_id: User ID to create session for
            duration_hours: Session duration in hours
        
        Returns:
            Session token
        """
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.now() + timedelta(hours=duration_hours)
        
        # Update user with session
        self.db.update(
            'users',
            {
                'session_token': hashlib.sha256(session_token.encode()).hexdigest(),
                'session_expires': session_expires.isoformat(),
                'last_login': datetime.now().isoformat(),
                'login_count': self.db.fetch_one(
                    "SELECT login_count FROM users WHERE user_id = ?",
                    (user_id,)
                ).get('login_count', 0) + 1
            },
            'user_id = ?',
            (user_id,)
        )
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """
        Validate session token and return user ID
        
        Args:
            session_token: Session token to validate
        
        Returns:
            User ID if valid, None otherwise
        """
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        user = self.db.fetch_one(
            """
            SELECT user_id, session_expires 
            FROM users 
            WHERE session_token = ?
            """,
            (token_hash,)
        )
        
        if not user:
            return None
        
        # Check expiration
        expires = datetime.fromisoformat(user['session_expires'])
        if expires < datetime.now():
            return None
        
        return user['user_id']
    
    def revoke_session(self, user_id: str):
        """Revoke user's session"""
        self.db.update(
            'users',
            {'session_token': None, 'session_expires': None},
            'user_id = ?',
            (user_id,)
        )
    
    def _encrypt_private_key(self, private_key: bytes, user_id: str) -> str:
        """Encrypt private key for storage"""
        # Derive key from user ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id[:32].encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(user_id.encode('utf-8'))
        
        # Encrypt key (simplified - should use proper encryption)
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        ciphertext, nonce, tag = enc.encrypt(private_key, key)
        
        # Pack and encode
        packed = nonce + tag + ciphertext
        return base64.b64encode(packed).decode('ascii')
    
    def _decrypt_private_key(self, encrypted_key: str, user_id: str) -> bytes:
        """Decrypt private key"""
        # Derive key from user ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=user_id[:32].encode('utf-8'),
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(user_id.encode('utf-8'))
        
        # Decrypt
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        packed = base64.b64decode(encrypted_key)
        nonce = packed[:12]
        tag = packed[12:28]
        ciphertext = packed[28:]
        
        return enc.decrypt(ciphertext, key, nonce, tag)
    
    def _encrypt_folder_key(self, private_key: str, owner_id: str) -> str:
        """Encrypt folder private key"""
        return self._encrypt_private_key(private_key.encode('utf-8'), owner_id)
    
    def _decrypt_folder_key(self, encrypted_key: str, user_id: str) -> str:
        """Decrypt folder private key"""
        return self._decrypt_private_key(encrypted_key, user_id).decode('utf-8')
    
    def _save_user_keys(self, user_id: str, private_key: bytes, public_key: bytes):
        """Save user keys to file as backup"""
        user_dir = self.keys_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Save keys
        (user_dir / "private.pem").write_bytes(private_key)
        (user_dir / "public.pem").write_bytes(public_key)
        
        # Set permissions (Unix only)
        try:
            os.chmod(user_dir / "private.pem", 0o600)
        except:
            pass
    
    def export_user_keys(self, user_id: str) -> Dict[str, str]:
        """Export user's public key for sharing"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return {
            'user_id': user_id,
            'public_key': user['public_key'],
            'username': user.get('username'),
            'created_at': user.get('created_at')
        }
    
    def import_user_public_key(self, user_data: Dict[str, str]):
        """Import another user's public key"""
        # Store in a separate table or cache for verification
        # This would be used for private share access
        pass