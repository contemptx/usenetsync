#!/usr/bin/env python3
"""
Unified Encryption Module - AES-256-GCM encryption for all data
Production-ready with key management and streaming support
"""

import os
import base64
import hashlib
import secrets
import struct
from typing import Tuple, Optional, Union, Generator
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import logging

logger = logging.getLogger(__name__)

class UnifiedEncryption:
    """
    Unified encryption system using AES-256-GCM
    Handles all encryption/decryption operations in the system
    """
    
    # Constants
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM
    TAG_SIZE = 16  # 128 bits
    SALT_SIZE = 32  # 256 bits
    CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming
    
    def __init__(self):
        """Initialize encryption system"""
        self.backend = default_backend()
        self._key_cache = {}  # Cache derived keys
    
    def generate_key(self) -> bytes:
        """Generate a random 256-bit key"""
        return secrets.token_bytes(self.KEY_SIZE)
    
    def generate_salt(self) -> bytes:
        """Generate a random salt"""
        return secrets.token_bytes(self.SALT_SIZE)
    
    def generate_nonce(self) -> bytes:
        """Generate a random nonce for GCM"""
        return secrets.token_bytes(self.NONCE_SIZE)
    
    def derive_key_pbkdf2(self, password: str, salt: bytes, 
                         iterations: int = 100000) -> bytes:
        """Derive key from password using PBKDF2"""
        cache_key = f"pbkdf2:{password}:{salt.hex()}:{iterations}"
        
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=iterations,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode('utf-8'))
        self._key_cache[cache_key] = key
        return key
    
    def derive_key_scrypt(self, password: str, salt: bytes,
                         n: int = 16384, r: int = 8, p: int = 1) -> bytes:
        """Derive key from password using Scrypt (more secure)"""
        cache_key = f"scrypt:{password}:{salt.hex()}:{n}:{r}:{p}"
        
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]
        
        kdf = Scrypt(
            salt=salt,
            length=self.KEY_SIZE,
            n=n,
            r=r,
            p=p,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode('utf-8'))
        self._key_cache[cache_key] = key
        return key
    
    def encrypt(self, data: bytes, key: bytes, 
               associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM
        
        Args:
            data: Data to encrypt
            key: 256-bit encryption key
            associated_data: Additional authenticated data (not encrypted)
        
        Returns:
            Tuple of (ciphertext, nonce, tag)
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        
        nonce = self.generate_nonce()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return ciphertext, nonce, encryptor.tag
    
    def decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes,
               associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt data using AES-256-GCM
        
        Args:
            ciphertext: Encrypted data
            key: 256-bit encryption key
            nonce: Nonce used for encryption
            tag: Authentication tag
            associated_data: Additional authenticated data
        
        Returns:
            Decrypted data
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=self.backend
        )
        
        decryptor = cipher.decryptor()
        
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)
        
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def encrypt_file(self, input_path: str, output_path: str, key: bytes,
                    progress_callback: Optional[callable] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt a file with streaming support
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            key: Encryption key
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (nonce, tag)
        """
        file_size = os.path.getsize(input_path)
        nonce = self.generate_nonce()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        bytes_processed = 0
        
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            # Write header: nonce (12 bytes)
            outfile.write(nonce)
            
            # Encrypt file in chunks
            while True:
                chunk = infile.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                
                encrypted_chunk = encryptor.update(chunk)
                outfile.write(encrypted_chunk)
                
                bytes_processed += len(chunk)
                if progress_callback:
                    progress_callback(bytes_processed, file_size)
            
            # Finalize and write tag
            encryptor.finalize()
            outfile.write(encryptor.tag)
        
        return nonce, encryptor.tag
    
    def decrypt_file(self, input_path: str, output_path: str, key: bytes,
                    progress_callback: Optional[callable] = None) -> None:
        """
        Decrypt a file with streaming support
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to output file
            key: Decryption key
            progress_callback: Optional callback for progress updates
        """
        file_size = os.path.getsize(input_path)
        
        with open(input_path, 'rb') as infile:
            # Read header
            nonce = infile.read(self.NONCE_SIZE)
            
            # Read tag from end of file
            infile.seek(-self.TAG_SIZE, os.SEEK_END)
            tag = infile.read(self.TAG_SIZE)
            
            # Reset to start of ciphertext
            infile.seek(self.NONCE_SIZE)
            ciphertext_size = file_size - self.NONCE_SIZE - self.TAG_SIZE
            
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=self.backend
            )
            
            decryptor = cipher.decryptor()
            bytes_processed = 0
            
            with open(output_path, 'wb') as outfile:
                # Decrypt file in chunks
                while bytes_processed < ciphertext_size:
                    chunk_size = min(self.CHUNK_SIZE, ciphertext_size - bytes_processed)
                    chunk = infile.read(chunk_size)
                    
                    decrypted_chunk = decryptor.update(chunk)
                    outfile.write(decrypted_chunk)
                    
                    bytes_processed += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_processed, ciphertext_size)
                
                # Finalize decryption
                decryptor.finalize()
    
    def encrypt_stream(self, data_stream: Generator[bytes, None, None], 
                      key: bytes) -> Generator[bytes, None, None]:
        """
        Encrypt a stream of data
        
        Args:
            data_stream: Generator yielding data chunks
            key: Encryption key
        
        Yields:
            Encrypted chunks
        """
        nonce = self.generate_nonce()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        
        # Yield header with nonce
        yield nonce
        
        # Encrypt chunks
        for chunk in data_stream:
            encrypted_chunk = encryptor.update(chunk)
            if encrypted_chunk:
                yield encrypted_chunk
        
        # Finalize and yield tag
        encryptor.finalize()
        yield encryptor.tag
    
    def decrypt_stream(self, encrypted_stream: Generator[bytes, None, None],
                      key: bytes) -> Generator[bytes, None, None]:
        """
        Decrypt a stream of data
        
        Args:
            encrypted_stream: Generator yielding encrypted chunks
            key: Decryption key
        
        Yields:
            Decrypted chunks
        """
        # Read nonce from first chunk
        nonce = next(encrypted_stream)
        
        # Collect all encrypted data and tag
        chunks = []
        for chunk in encrypted_stream:
            chunks.append(chunk)
        
        # Last chunk is the tag
        tag = chunks[-1]
        ciphertext = b''.join(chunks[:-1])
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=self.backend
        )
        
        decryptor = cipher.decryptor()
        
        # Yield decrypted data in chunks
        for i in range(0, len(ciphertext), self.CHUNK_SIZE):
            chunk = ciphertext[i:i + self.CHUNK_SIZE]
            decrypted_chunk = decryptor.update(chunk)
            if decrypted_chunk:
                yield decrypted_chunk
        
        decryptor.finalize()
    
    def wrap_key(self, key_to_wrap: bytes, wrapping_key: bytes) -> bytes:
        """
        Wrap a key using AES-256-GCM key wrapping
        
        Args:
            key_to_wrap: Key to be wrapped
            wrapping_key: Key encryption key
        
        Returns:
            Wrapped key with nonce and tag
        """
        ciphertext, nonce, tag = self.encrypt(key_to_wrap, wrapping_key)
        
        # Pack as: nonce (12) + tag (16) + ciphertext
        wrapped = nonce + tag + ciphertext
        return wrapped
    
    def unwrap_key(self, wrapped_key: bytes, wrapping_key: bytes) -> bytes:
        """
        Unwrap a key
        
        Args:
            wrapped_key: Wrapped key data
            wrapping_key: Key encryption key
        
        Returns:
            Unwrapped key
        """
        # Unpack: nonce (12) + tag (16) + ciphertext
        nonce = wrapped_key[:self.NONCE_SIZE]
        tag = wrapped_key[self.NONCE_SIZE:self.NONCE_SIZE + self.TAG_SIZE]
        ciphertext = wrapped_key[self.NONCE_SIZE + self.TAG_SIZE:]
        
        return self.decrypt(ciphertext, wrapping_key, nonce, tag)
    
    def encrypt_json(self, data: dict, key: bytes) -> str:
        """
        Encrypt JSON data to base64 string
        
        Args:
            data: Dictionary to encrypt
            key: Encryption key
        
        Returns:
            Base64-encoded encrypted data
        """
        import json
        
        json_bytes = json.dumps(data).encode('utf-8')
        ciphertext, nonce, tag = self.encrypt(json_bytes, key)
        
        # Pack and encode
        packed = nonce + tag + ciphertext
        return base64.b64encode(packed).decode('ascii')
    
    def decrypt_json(self, encrypted_data: str, key: bytes) -> dict:
        """
        Decrypt base64 JSON data
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            key: Decryption key
        
        Returns:
            Decrypted dictionary
        """
        import json
        
        # Decode and unpack
        packed = base64.b64decode(encrypted_data)
        nonce = packed[:self.NONCE_SIZE]
        tag = packed[self.NONCE_SIZE:self.NONCE_SIZE + self.TAG_SIZE]
        ciphertext = packed[self.NONCE_SIZE + self.TAG_SIZE:]
        
        # Decrypt
        json_bytes = self.decrypt(ciphertext, key, nonce, tag)
        return json.loads(json_bytes.decode('utf-8'))
    
    def secure_delete(self, data: Union[bytes, bytearray]) -> None:
        """
        Securely overwrite sensitive data in memory
        
        Args:
            data: Data to securely delete
        """
        if isinstance(data, bytes):
            # Can't modify bytes, just del reference
            del data
        elif isinstance(data, bytearray):
            # Overwrite with random data
            for i in range(len(data)):
                data[i] = secrets.randbits(8)
            del data
    
    def clear_key_cache(self):
        """Clear cached derived keys"""
        self._key_cache.clear()
    
    def get_key_fingerprint(self, key: bytes) -> str:
        """Get fingerprint of a key for identification"""
        return hashlib.sha256(key).hexdigest()[:16]