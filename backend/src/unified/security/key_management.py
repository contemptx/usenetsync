#!/usr/bin/env python3
"""
Unified Key Management Module - Secure key derivation and storage
Production-ready with Scrypt and secure key handling
"""

import os
import json
import hashlib
import secrets
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UnifiedKeyManagement:
    """
    Unified key management system
    Handles key derivation, storage, and lifecycle
    """
    
    # Key derivation parameters
    SCRYPT_N = 16384  # CPU/memory cost
    SCRYPT_R = 8      # Block size
    SCRYPT_P = 1      # Parallelization
    PBKDF2_ITERATIONS = 100000
    
    def __init__(self, db, keys_dir: str = "data/keys"):
        """Initialize key management system"""
        self.db = db
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self._key_cache = {}
        self._master_key = None
    
    def initialize_master_key(self, password: Optional[str] = None) -> bytes:
        """
        Initialize or load master key
        
        Args:
            password: Optional password for master key derivation
        
        Returns:
            Master key bytes
        """
        master_key_file = self.keys_dir / "master.key"
        
        if master_key_file.exists():
            # Load existing master key
            self._master_key = self._load_master_key(password)
        else:
            # Generate new master key
            self._master_key = self._generate_master_key(password)
        
        return self._master_key
    
    def _generate_master_key(self, password: Optional[str] = None) -> bytes:
        """Generate new master key"""
        if password:
            # Derive from password
            salt = secrets.token_bytes(32)
            master_key = self.derive_key_scrypt(password, salt)
            
            # Save encrypted
            self._save_master_key(master_key, salt, password)
        else:
            # Generate random
            master_key = secrets.token_bytes(32)
            
            # Save unencrypted (WARNING: less secure)
            self._save_master_key(master_key, None, None)
        
        logger.info("Generated new master key")
        return master_key
    
    def _load_master_key(self, password: Optional[str] = None) -> bytes:
        """Load existing master key"""
        master_key_file = self.keys_dir / "master.key"
        
        with open(master_key_file, 'rb') as f:
            data = json.loads(f.read())
        
        if data.get('encrypted'):
            if not password:
                raise ValueError("Password required for encrypted master key")
            
            # Decrypt master key
            salt = base64.b64decode(data['salt'])
            derived_key = self.derive_key_scrypt(password, salt)
            
            from .encryption import UnifiedEncryption
            enc = UnifiedEncryption()
            
            encrypted = base64.b64decode(data['key'])
            nonce = encrypted[:12]
            tag = encrypted[12:28]
            ciphertext = encrypted[28:]
            
            master_key = enc.decrypt(ciphertext, derived_key, nonce, tag)
        else:
            # Load unencrypted
            master_key = base64.b64decode(data['key'])
        
        logger.info("Loaded master key")
        return master_key
    
    def _save_master_key(self, master_key: bytes, salt: Optional[bytes],
                        password: Optional[str]):
        """Save master key to file"""
        master_key_file = self.keys_dir / "master.key"
        
        if password and salt:
            # Encrypt master key
            derived_key = self.derive_key_scrypt(password, salt)
            
            from .encryption import UnifiedEncryption
            enc = UnifiedEncryption()
            
            ciphertext, nonce, tag = enc.encrypt(master_key, derived_key)
            encrypted = nonce + tag + ciphertext
            
            data = {
                'encrypted': True,
                'key': base64.b64encode(encrypted).decode('ascii'),
                'salt': base64.b64encode(salt).decode('ascii'),
                'created': datetime.now().isoformat()
            }
        else:
            # Save unencrypted
            data = {
                'encrypted': False,
                'key': base64.b64encode(master_key).decode('ascii'),
                'created': datetime.now().isoformat()
            }
        
        # Write with restricted permissions
        with open(master_key_file, 'wb') as f:
            f.write(json.dumps(data).encode())
        
        # Set permissions (Unix only)
        try:
            os.chmod(master_key_file, 0o600)
        except:
            pass
    
    def derive_key_scrypt(self, password: str, salt: bytes,
                         n: Optional[int] = None,
                         r: Optional[int] = None,
                         p: Optional[int] = None) -> bytes:
        """
        Derive key using Scrypt (recommended)
        
        Args:
            password: Password to derive from
            salt: Salt bytes
            n: CPU/memory cost parameter
            r: Block size parameter
            p: Parallelization parameter
        
        Returns:
            32-byte derived key
        """
        # Use defaults if not specified
        n = n or self.SCRYPT_N
        r = r or self.SCRYPT_R
        p = p or self.SCRYPT_P
        
        # Check cache
        cache_key = f"scrypt:{password}:{salt.hex()}:{n}:{r}:{p}"
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]
        
        # Derive key
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=n,
            r=r,
            p=p,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        
        # Cache result
        self._key_cache[cache_key] = key
        
        return key
    
    def derive_key_pbkdf2(self, password: str, salt: bytes,
                         iterations: Optional[int] = None) -> bytes:
        """
        Derive key using PBKDF2 (fallback)
        
        Args:
            password: Password to derive from
            salt: Salt bytes
            iterations: Number of iterations
        
        Returns:
            32-byte derived key
        """
        iterations = iterations or self.PBKDF2_ITERATIONS
        
        # Check cache
        cache_key = f"pbkdf2:{password}:{salt.hex()}:{iterations}"
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        
        # Cache result
        self._key_cache[cache_key] = key
        
        return key
    
    def generate_folder_key(self, folder_id: str) -> Tuple[bytes, bytes]:
        """
        Generate encryption key for folder
        
        Args:
            folder_id: Folder identifier
        
        Returns:
            Tuple of (key, salt)
        """
        # Generate random key and salt
        key = secrets.token_bytes(32)
        salt = secrets.token_bytes(32)
        
        # Store encrypted with master key
        self._store_folder_key(folder_id, key, salt)
        
        return key, salt
    
    def get_folder_key(self, folder_id: str) -> Optional[Tuple[bytes, bytes]]:
        """
        Retrieve folder encryption key
        
        Args:
            folder_id: Folder identifier
        
        Returns:
            Tuple of (key, salt) or None
        """
        # Check cache
        if folder_id in self._key_cache:
            return self._key_cache[folder_id]
        
        # Load from storage
        key_file = self.keys_dir / f"folder_{folder_id}.key"
        
        if not key_file.exists():
            return None
        
        with open(key_file, 'rb') as f:
            data = json.loads(f.read())
        
        # Decrypt with master key
        if not self._master_key:
            raise ValueError("Master key not initialized")
        
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        # Decrypt key
        encrypted_key = base64.b64decode(data['key'])
        nonce = encrypted_key[:12]
        tag = encrypted_key[12:28]
        ciphertext = encrypted_key[28:]
        
        key = enc.decrypt(ciphertext, self._master_key, nonce, tag)
        salt = base64.b64decode(data['salt'])
        
        # Cache
        self._key_cache[folder_id] = (key, salt)
        
        return key, salt
    
    def _store_folder_key(self, folder_id: str, key: bytes, salt: bytes):
        """Store folder key encrypted"""
        if not self._master_key:
            raise ValueError("Master key not initialized")
        
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        # Encrypt key with master key
        ciphertext, nonce, tag = enc.encrypt(key, self._master_key)
        encrypted_key = nonce + tag + ciphertext
        
        # Save to file
        key_file = self.keys_dir / f"folder_{folder_id}.key"
        
        data = {
            'folder_id': folder_id,
            'key': base64.b64encode(encrypted_key).decode('ascii'),
            'salt': base64.b64encode(salt).decode('ascii'),
            'created': datetime.now().isoformat()
        }
        
        with open(key_file, 'wb') as f:
            f.write(json.dumps(data).encode())
        
        # Set permissions
        try:
            os.chmod(key_file, 0o600)
        except:
            pass
        
        # Cache
        self._key_cache[folder_id] = (key, salt)
    
    def rotate_folder_key(self, folder_id: str) -> Tuple[bytes, bytes]:
        """
        Rotate encryption key for folder
        
        Args:
            folder_id: Folder identifier
        
        Returns:
            New tuple of (key, salt)
        """
        # Generate new key
        new_key, new_salt = self.generate_folder_key(folder_id)
        
        # Mark old key for re-encryption
        self.db.update(
            'folders',
            {'needs_reencryption': True},
            'folder_id = ?',
            (folder_id,)
        )
        
        logger.info(f"Rotated key for folder {folder_id}")
        
        return new_key, new_salt
    
    def generate_share_key(self, share_id: str) -> bytes:
        """
        Generate encryption key for share
        
        Args:
            share_id: Share identifier
        
        Returns:
            32-byte key
        """
        # Derive from share ID and master key
        if not self._master_key:
            raise ValueError("Master key not initialized")
        
        data = f"{share_id}:{self._master_key.hex()}"
        key = hashlib.sha256(data.encode()).digest()
        
        return key
    
    def wrap_key(self, key: bytes, wrapping_key: bytes) -> bytes:
        """
        Wrap key for secure storage/transmission
        
        Args:
            key: Key to wrap
            wrapping_key: Key encryption key
        
        Returns:
            Wrapped key
        """
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        return enc.wrap_key(key, wrapping_key)
    
    def unwrap_key(self, wrapped_key: bytes, wrapping_key: bytes) -> bytes:
        """
        Unwrap key
        
        Args:
            wrapped_key: Wrapped key data
            wrapping_key: Key encryption key
        
        Returns:
            Unwrapped key
        """
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        return enc.unwrap_key(wrapped_key, wrapping_key)
    
    def clear_cache(self):
        """Clear key cache"""
        self._key_cache.clear()
        logger.info("Cleared key cache")
    
    def export_keys(self, password: str, output_file: str):
        """
        Export all keys (encrypted)
        
        Args:
            password: Password for export encryption
            output_file: Output file path
        """
        # Collect all keys
        keys_data = {
            'master_key': base64.b64encode(self._master_key).decode('ascii') if self._master_key else None,
            'folder_keys': {},
            'exported_at': datetime.now().isoformat()
        }
        
        # Get all folder keys
        for key_file in self.keys_dir.glob("folder_*.key"):
            folder_id = key_file.stem.replace("folder_", "")
            key_data = self.get_folder_key(folder_id)
            if key_data:
                key, salt = key_data
                keys_data['folder_keys'][folder_id] = {
                    'key': base64.b64encode(key).decode('ascii'),
                    'salt': base64.b64encode(salt).decode('ascii')
                }
        
        # Encrypt export
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        salt = enc.generate_salt()
        export_key = self.derive_key_scrypt(password, salt)
        
        encrypted = enc.encrypt_json(keys_data, export_key)
        
        # Save export
        export_data = {
            'version': 1,
            'salt': base64.b64encode(salt).decode('ascii'),
            'data': encrypted
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported keys to {output_file}")
    
    def import_keys(self, password: str, input_file: str):
        """
        Import keys from export
        
        Args:
            password: Password for decryption
            input_file: Input file path
        """
        with open(input_file, 'r') as f:
            export_data = json.load(f)
        
        # Decrypt export
        from .encryption import UnifiedEncryption
        enc = UnifiedEncryption()
        
        salt = base64.b64decode(export_data['salt'])
        import_key = self.derive_key_scrypt(password, salt)
        
        keys_data = enc.decrypt_json(export_data['data'], import_key)
        
        # Import master key
        if keys_data['master_key']:
            self._master_key = base64.b64decode(keys_data['master_key'])
            self._save_master_key(self._master_key, None, None)
        
        # Import folder keys
        for folder_id, key_data in keys_data['folder_keys'].items():
            key = base64.b64decode(key_data['key'])
            salt = base64.b64decode(key_data['salt'])
            self._store_folder_key(folder_id, key, salt)
        
        logger.info(f"Imported keys from {input_file}")