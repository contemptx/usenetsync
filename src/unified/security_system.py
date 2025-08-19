#!/usr/bin/env python3
"""
Complete Security System for Unified UsenetSync
Implements user keys, folder keys, encryption, and access control
"""

import os
import sys
import json
import hashlib
import secrets
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

@dataclass
class UserKey:
    """User key information"""
    user_id: str
    public_key: bytes
    private_key: bytes
    created_at: datetime
    key_type: str = "ed25519"

@dataclass
class FolderKey:
    """Folder encryption key"""
    folder_id: str
    key: bytes
    created_at: datetime
    created_by: str
    algorithm: str = "AES-256-GCM"

@dataclass
class AccessToken:
    """Access token for authorization"""
    token: str
    user_id: str
    permissions: List[str]
    expires_at: datetime
    created_at: datetime

class SecuritySystem:
    """Comprehensive security system for UsenetSync"""
    
    def __init__(self, keys_dir: str = "/var/lib/usenetsync/keys"):
        """
        Initialize security system
        
        Args:
            keys_dir: Directory to store keys
        """
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # User database (in production, use secure database)
        self.users_file = self.keys_dir / "users.json"
        self.folders_file = self.keys_dir / "folders.json"
        self.sessions_file = self.keys_dir / "sessions.json"
        
        self._load_data()
        
    def _load_data(self):
        """Load security data from files"""
        # Load users
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
        
        # Load folders
        if self.folders_file.exists():
            with open(self.folders_file, 'r') as f:
                self.folders = json.load(f)
        else:
            self.folders = {}
        
        # Load sessions
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                self.sessions = json.load(f)
        else:
            self.sessions = {}
    
    def _save_data(self):
        """Save security data to files"""
        # Set restrictive permissions
        for file_path, data in [
            (self.users_file, self.users),
            (self.folders_file, self.folders),
            (self.sessions_file, self.sessions)
        ]:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            os.chmod(file_path, 0o600)
    
    def generate_user_id(self, email: Optional[str] = None) -> str:
        """
        Generate unique user ID
        
        Args:
            email: Optional email for deterministic ID
            
        Returns:
            User ID (SHA256 hex)
        """
        if email:
            # Deterministic ID from email
            return hashlib.sha256(email.encode()).hexdigest()
        else:
            # Random ID
            return hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    
    def generate_user_keys(self, user_id: str) -> UserKey:
        """
        Generate user key pair
        
        Args:
            user_id: User identifier
            
        Returns:
            UserKey object
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            # Generate Ed25519 key pair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            user_key = UserKey(
                user_id=user_id,
                public_key=public_key.public_bytes_raw(),
                private_key=private_key.private_bytes_raw(),
                created_at=datetime.now()
            )
            
            # Store keys securely
            self._store_user_key(user_key)
            
            return user_key
            
        except ImportError:
            # Fallback to symmetric key
            logger.warning("Ed25519 not available, using symmetric key")
            
            key = Fernet.generate_key()
            
            user_key = UserKey(
                user_id=user_id,
                public_key=key,
                private_key=key,
                created_at=datetime.now(),
                key_type="symmetric"
            )
            
            self._store_user_key(user_key)
            
            return user_key
    
    def _store_user_key(self, user_key: UserKey):
        """Store user key securely"""
        key_file = self.keys_dir / f"user_{user_key.user_id}.key"
        
        key_data = {
            'user_id': user_key.user_id,
            'public_key': base64.b64encode(user_key.public_key).decode(),
            'private_key': base64.b64encode(user_key.private_key).decode(),
            'created_at': user_key.created_at.isoformat(),
            'key_type': user_key.key_type
        }
        
        with open(key_file, 'w') as f:
            json.dump(key_data, f)
        
        # Set restrictive permissions
        os.chmod(key_file, 0o600)
        
        # Update users database
        self.users[user_key.user_id] = {
            'created_at': user_key.created_at.isoformat(),
            'key_file': str(key_file)
        }
        self._save_data()
    
    def generate_folder_key(self, folder_id: Optional[str] = None, 
                          user_id: Optional[str] = None) -> bytes:
        """
        Generate folder encryption key
        
        Args:
            folder_id: Optional folder identifier
            user_id: Optional user who created the key
            
        Returns:
            Encryption key bytes
        """
        # Generate AES-256 key
        key = secrets.token_bytes(32)
        
        if folder_id:
            folder_key = FolderKey(
                folder_id=folder_id,
                key=key,
                created_at=datetime.now(),
                created_by=user_id or "system"
            )
            
            self._store_folder_key(folder_key)
        
        return key
    
    def _store_folder_key(self, folder_key: FolderKey):
        """Store folder key securely"""
        key_file = self.keys_dir / f"folder_{folder_key.folder_id}.key"
        
        key_data = {
            'folder_id': folder_key.folder_id,
            'key': base64.b64encode(folder_key.key).decode(),
            'created_at': folder_key.created_at.isoformat(),
            'created_by': folder_key.created_by,
            'algorithm': folder_key.algorithm
        }
        
        with open(key_file, 'w') as f:
            json.dump(key_data, f)
        
        os.chmod(key_file, 0o600)
        
        # Update folders database
        self.folders[folder_key.folder_id] = {
            'created_at': folder_key.created_at.isoformat(),
            'created_by': folder_key.created_by,
            'key_file': str(key_file)
        }
        self._save_data()
    
    def encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM
        
        Args:
            data: Data to encrypt
            key: Encryption key (32 bytes)
            
        Returns:
            Encrypted data with nonce prepended
        """
        # Generate random nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Return nonce + ciphertext + tag
        return nonce + ciphertext + encryptor.tag
    
    def decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM
        
        Args:
            encrypted_data: Encrypted data with nonce prepended
            key: Decryption key (32 bytes)
            
        Returns:
            Decrypted data
        """
        # Extract nonce, ciphertext, and tag
        nonce = encrypted_data[:12]
        tag = encrypted_data[-16:]
        ciphertext = encrypted_data[12:-16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
    
    def encrypt_file(self, file_path: str, key: bytes, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file
        
        Args:
            file_path: Path to file to encrypt
            key: Encryption key
            output_path: Optional output path
            
        Returns:
            Path to encrypted file
        """
        if not output_path:
            output_path = f"{file_path}.encrypted"
        
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        
        encrypted = self.encrypt_data(plaintext, key)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        return output_path
    
    def decrypt_file(self, encrypted_path: str, key: bytes, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file
        
        Args:
            encrypted_path: Path to encrypted file
            key: Decryption key
            output_path: Optional output path
            
        Returns:
            Path to decrypted file
        """
        if not output_path:
            output_path = encrypted_path.replace('.encrypted', '')
        
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.decrypt_data(encrypted, key)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path
    
    def generate_session_token(self, user_id: str, ttl: int = 3600) -> str:
        """
        Generate session token for user
        
        Args:
            user_id: User identifier
            ttl: Time to live in seconds
            
        Returns:
            Session token
        """
        token = secrets.token_urlsafe(32)
        
        session = {
            'token': token,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat()
        }
        
        self.sessions[token] = session
        self._save_data()
        
        return token
    
    def verify_session_token(self, token: str) -> bool:
        """
        Verify session token
        
        Args:
            token: Session token to verify
            
        Returns:
            True if valid, False otherwise
        """
        if token not in self.sessions:
            return False
        
        session = self.sessions[token]
        expires_at = datetime.fromisoformat(session['expires_at'])
        
        if datetime.now() > expires_at:
            # Token expired
            del self.sessions[token]
            self._save_data()
            return False
        
        return True
    
    def check_access(self, user_id: str, resource: str, permission: str) -> bool:
        """
        Check if user has access to resource
        
        Args:
            user_id: User identifier
            resource: Resource identifier (e.g., folder_id)
            permission: Permission type (read, write, delete)
            
        Returns:
            True if access granted, False otherwise
        """
        # Simple ACL implementation
        acl_file = self.keys_dir / "acl.json"
        
        if acl_file.exists():
            with open(acl_file, 'r') as f:
                acl = json.load(f)
        else:
            acl = {}
        
        # Check user permissions
        user_perms = acl.get(user_id, {})
        resource_perms = user_perms.get(resource, [])
        
        return permission in resource_perms or "*" in resource_perms
    
    def grant_access(self, user_id: str, resource: str, permissions: List[str]):
        """
        Grant user access to resource
        
        Args:
            user_id: User identifier
            resource: Resource identifier
            permissions: List of permissions to grant
        """
        acl_file = self.keys_dir / "acl.json"
        
        if acl_file.exists():
            with open(acl_file, 'r') as f:
                acl = json.load(f)
        else:
            acl = {}
        
        if user_id not in acl:
            acl[user_id] = {}
        
        acl[user_id][resource] = permissions
        
        with open(acl_file, 'w') as f:
            json.dump(acl, f, indent=2)
        
        os.chmod(acl_file, 0o600)
    
    def revoke_access(self, user_id: str, resource: str):
        """
        Revoke user access to resource
        
        Args:
            user_id: User identifier
            resource: Resource identifier
        """
        acl_file = self.keys_dir / "acl.json"
        
        if not acl_file.exists():
            return
        
        with open(acl_file, 'r') as f:
            acl = json.load(f)
        
        if user_id in acl and resource in acl[user_id]:
            del acl[user_id][resource]
            
            with open(acl_file, 'w') as f:
                json.dump(acl, f, indent=2)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Hash password using PBKDF2
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        
        return key, salt
    
    def verify_password(self, password: str, hash_value: bytes, salt: bytes) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Password to verify
            hash_value: Password hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches, False otherwise
        """
        calculated_hash, _ = self.hash_password(password, salt)
        return calculated_hash == hash_value
    
    def sanitize_path(self, path: str) -> str:
        """
        Sanitize file path to prevent traversal attacks
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        # Convert to Path object
        p = Path(path)
        
        # Resolve to absolute path and check for traversal
        try:
            resolved = p.resolve()
            
            # Ensure path doesn't escape allowed directories
            allowed_dirs = [
                Path('/data'),
                Path('/tmp'),
                Path.home(),
                Path.cwd()
            ]
            
            for allowed in allowed_dirs:
                try:
                    resolved.relative_to(allowed)
                    return str(resolved)
                except ValueError:
                    continue
            
            # Path is outside allowed directories
            raise ValueError(f"Path {path} is not allowed")
            
        except Exception as e:
            logger.warning(f"Path sanitization failed for {path}: {e}")
            raise ValueError(f"Invalid path: {path}")
    
    def generate_api_key(self, user_id: str, name: str) -> str:
        """
        Generate API key for user
        
        Args:
            user_id: User identifier
            name: API key name/description
            
        Returns:
            API key
        """
        api_key = f"usk_{secrets.token_urlsafe(32)}"
        
        # Store API key
        api_keys_file = self.keys_dir / "api_keys.json"
        
        if api_keys_file.exists():
            with open(api_keys_file, 'r') as f:
                api_keys = json.load(f)
        else:
            api_keys = {}
        
        api_keys[api_key] = {
            'user_id': user_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'active': True
        }
        
        with open(api_keys_file, 'w') as f:
            json.dump(api_keys, f, indent=2)
        
        os.chmod(api_keys_file, 0o600)
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """
        Verify API key and return user ID
        
        Args:
            api_key: API key to verify
            
        Returns:
            User ID if valid, None otherwise
        """
        api_keys_file = self.keys_dir / "api_keys.json"
        
        if not api_keys_file.exists():
            return None
        
        with open(api_keys_file, 'r') as f:
            api_keys = json.load(f)
        
        if api_key in api_keys and api_keys[api_key]['active']:
            # Update last used
            api_keys[api_key]['last_used'] = datetime.now().isoformat()
            
            with open(api_keys_file, 'w') as f:
                json.dump(api_keys, f, indent=2)
            
            return api_keys[api_key]['user_id']
        
        return None


def test_security_system():
    """Test security system"""
    print("\n=== Testing Security System ===\n")
    
    # Create security system
    security = SecuritySystem(keys_dir="/tmp/security_test")
    
    # Test 1: User ID generation
    print("1. Testing user ID generation...")
    user_id = security.generate_user_id("test@example.com")
    print(f"   User ID: {user_id[:16]}...")
    assert len(user_id) == 64
    
    # Test 2: User key generation
    print("\n2. Testing user key generation...")
    user_key = security.generate_user_keys(user_id)
    print(f"   Key type: {user_key.key_type}")
    print(f"   Public key size: {len(user_key.public_key)} bytes")
    
    # Test 3: Folder key generation
    print("\n3. Testing folder key generation...")
    folder_key = security.generate_folder_key("test_folder", user_id)
    print(f"   Folder key size: {len(folder_key)} bytes")
    assert len(folder_key) == 32
    
    # Test 4: Encryption/Decryption
    print("\n4. Testing encryption/decryption...")
    test_data = b"This is sensitive data that needs encryption"
    
    encrypted = security.encrypt_data(test_data, folder_key)
    print(f"   Original size: {len(test_data)} bytes")
    print(f"   Encrypted size: {len(encrypted)} bytes")
    
    decrypted = security.decrypt_data(encrypted, folder_key)
    assert decrypted == test_data
    print("   ✓ Encryption/decryption successful")
    
    # Test 5: Session tokens
    print("\n5. Testing session tokens...")
    token = security.generate_session_token(user_id, ttl=60)
    print(f"   Token: {token[:16]}...")
    
    valid = security.verify_session_token(token)
    assert valid
    print("   ✓ Token verified")
    
    # Test 6: Access control
    print("\n6. Testing access control...")
    security.grant_access(user_id, "test_folder", ["read", "write"])
    
    has_read = security.check_access(user_id, "test_folder", "read")
    has_delete = security.check_access(user_id, "test_folder", "delete")
    
    assert has_read and not has_delete
    print("   ✓ Access control working")
    
    # Test 7: Password hashing
    print("\n7. Testing password hashing...")
    password = "SecurePassword123!"
    hash_value, salt = security.hash_password(password)
    
    valid = security.verify_password(password, hash_value, salt)
    invalid = security.verify_password("WrongPassword", hash_value, salt)
    
    assert valid and not invalid
    print("   ✓ Password hashing secure")
    
    # Test 8: Path sanitization
    print("\n8. Testing path sanitization...")
    try:
        safe_path = security.sanitize_path("/tmp/test.txt")
        print(f"   Safe path: {safe_path}")
        
        malicious_path = security.sanitize_path("../../etc/passwd")
        print("   ✗ Path traversal not prevented!")
    except ValueError:
        print("   ✓ Path traversal prevented")
    
    # Test 9: API keys
    print("\n9. Testing API key generation...")
    api_key = security.generate_api_key(user_id, "Test API Key")
    print(f"   API Key: {api_key[:20]}...")
    
    verified_user = security.verify_api_key(api_key)
    assert verified_user == user_id
    print("   ✓ API key verified")
    
    print("\n✓ Security system test completed successfully")


if __name__ == "__main__":
    test_security_system()