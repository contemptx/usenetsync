# Access Management and Security Levels Documentation

## Overview

UsenetSync implements three distinct access levels for folder sharing, each with different security guarantees and use cases. All authentication and access control happens **client-side** - Usenet servers never see unencrypted data or access credentials.

## Access Levels

### 1. PUBLIC Access

**Use Case**: Share with anyone who has the access string. No authentication required.

**Security Model**:
- Data IS encrypted (AES-256-GCM)
- Encryption key is INCLUDED in the access string
- Anyone with the access string can decrypt
- No user tracking or access control

**Implementation**:
```python
def create_public_share(folder_id: str, files_data: List, segments_data: Dict):
    # Generate random encryption key
    encryption_key = secrets.token_bytes(32)  # 256-bit key
    
    # Encrypt the data
    data_to_encrypt = json.dumps({
        'files': files_data,
        'segments': segments_data
    }).encode('utf-8')
    
    encrypted_data = encrypt_data(data_to_encrypt, encryption_key)
    
    # Create index with key included (makes it "public")
    index = {
        'share_type': 'public',
        'encryption_key': base64.b64encode(encryption_key),  # KEY INCLUDED
        'encrypted_data': base64.b64encode(encrypted_data),
        'signature': sign_with_folder_key(...)
    }
    
    # Post to Usenet
    post_to_usenet(index)
    
    # Access string contains everything needed
    access_string = create_access_string({
        'share_id': share_id,
        'index_location': message_id,
        # Encryption key is IN the index on Usenet
    })
```

**Download Process**:
```python
def download_public_share(access_string: str):
    # Parse access string
    data = parse_access_string(access_string)
    
    # Download index from Usenet
    index = download_from_usenet(data['index_location'])
    
    # Extract encryption key (it's included)
    encryption_key = base64.b64decode(index['encryption_key'])
    
    # Decrypt data
    decrypted = decrypt_data(index['encrypted_data'], encryption_key)
    
    # No authentication needed - anyone can do this
```

**Pros**:
- Simple sharing - just send the access string
- No user management required
- Still encrypted on Usenet

**Cons**:
- No access control - anyone with the string can access
- Cannot revoke access
- No audit trail

### 2. PRIVATE Access

**Use Case**: Share with specific authorized users only. Each user must prove their identity.

**Security Model**:
- Data encrypted with session key
- Session key wrapped separately for EACH authorized user
- Zero-knowledge proofs for authentication
- User never reveals their ID, only proves they know it
- Owner has special access through folder keys

**Implementation**:
```python
def create_private_share(folder_id: str, files_data: List, segments_data: Dict, 
                        authorized_users: List[str]):
    # Generate random session key for this share
    session_key = secrets.token_bytes(32)
    
    # Create access commitments for each user
    commitments = []
    for user_id in authorized_users:
        # Create zero-knowledge proof parameters
        zk_params = generate_zk_params()
        
        # Hash user_id with salt (never store plaintext)
        salt = secrets.token_hex(16)
        user_id_hash = hash(user_id + salt)
        
        # Create verification key
        verification_key = hash(user_id + folder_id + salt)
        
        # Derive user-specific wrapping key
        user_wrapping_key = derive_user_key(user_id, folder_id)
        
        # Wrap session key for this user
        wrapped_key = wrap_key(session_key, user_wrapping_key)
        
        commitments.append({
            'hash': user_id_hash,           # For identification
            'salt': salt,                   # For key derivation
            'params': zk_params,             # For zero-knowledge proof
            'verification_key': verification_key,  # For verification
            'wrapped_key': wrapped_key       # User's encrypted session key
        })
    
    # Also create owner's wrapped key (folder creator)
    owner_wrapped_key = wrap_key(session_key, owner_key)
    
    # Encrypt data with session key
    encrypted_data = encrypt_data(data, session_key)
    
    # Create index
    index = {
        'share_type': 'private',
        'access_commitments': commitments,  # One per user
        'owner_wrapped_key': owner_wrapped_key,
        'encrypted_data': encrypted_data,
        'signature': sign_with_folder_key(...)
    }
    
    # Post to Usenet
    post_to_usenet(index)
```

**Authentication Process (Zero-Knowledge Proof)**:
```python
def verify_user_access(user_id: str, commitment: AccessCommitment) -> bool:
    """
    User proves they know user_id without revealing it
    """
    # Generate zero-knowledge proof
    proof = zk_system.prove_knowledge(user_id, commitment.proof_params)
    
    # Verify proof (proves user knows the user_id)
    if not zk_system.verify_proof(proof, commitment.proof_params):
        return False
    
    # Additional verification
    expected_key = hash(user_id + folder_id + commitment.salt)
    return constant_time_compare(expected_key, commitment.verification_key)
```

**Download Process**:
```python
def download_private_share(access_string: str, user_id: str):
    # Parse and download index
    index = download_index(access_string)
    
    # Check if user is the owner (created the folder)
    if is_owner(user_id, folder_id):
        # Owner can use their folder keys
        session_key = unwrap_key(index['owner_wrapped_key'], owner_key)
    else:
        # Find user's commitment
        for commitment in index['access_commitments']:
            # Verify user has access (zero-knowledge proof)
            if verify_user_access(user_id, commitment):
                # Derive user's wrapping key
                user_key = derive_user_key(user_id, folder_id)
                
                # Unwrap session key
                session_key = unwrap_key(commitment['wrapped_key'], user_key)
                break
        else:
            raise AccessDenied("User not authorized")
    
    # Decrypt data with session key
    decrypted = decrypt_data(index['encrypted_data'], session_key)
```

**Key Features**:
- **Zero-Knowledge Proofs**: User proves identity without revealing it
- **Per-User Keys**: Each user has their own wrapped session key
- **Owner Privileges**: Folder creator maintains special access
- **No Central Authority**: All verification is client-side

**Pros**:
- Fine-grained access control
- Can have multiple authorized users
- Users don't reveal identity during verification
- Owner maintains control

**Cons**:
- Cannot add/remove users after publishing
- Requires user ID management
- More complex than public shares

### 3. PROTECTED Access (Password-Based)

**Use Case**: Share with anyone who knows the password. Simple access control.

**Security Model**:
- Data encrypted with key derived from password
- Uses scrypt for key derivation (resistant to brute force)
- Optional password hint
- No user tracking

**Implementation**:
```python
def create_protected_share(folder_id: str, files_data: List, segments_data: Dict,
                          password: str, hint: Optional[str] = None):
    # Generate salt for key derivation
    salt = os.urandom(32)  # 256-bit salt
    
    # Derive key from password using scrypt (slow by design)
    key = scrypt(
        password=password,
        salt=salt,
        n=2**16,  # CPU/memory cost (65536)
        r=8,      # Block size
        p=1,      # Parallelization
        dklen=32  # 256-bit key
    )
    
    # Encrypt data with derived key
    encrypted_data = encrypt_data(data, key)
    
    # Create index
    index = {
        'share_type': 'protected',
        'salt': base64.b64encode(salt),
        'encrypted_data': encrypted_data,
        'password_hint': hint,  # Optional
        'scrypt_params': {'n': 65536, 'r': 8, 'p': 1},  # For key derivation
        'signature': sign_with_folder_key(...)
    }
    
    # Post to Usenet
    post_to_usenet(index)
    
    # Access string does NOT contain password
    access_string = create_access_string({
        'share_id': share_id,
        'index_location': message_id
        # Password must be communicated separately
    })
```

**Download Process**:
```python
def download_protected_share(access_string: str, password: str):
    # Download index
    index = download_index(access_string)
    
    # Show hint if available
    if 'password_hint' in index:
        print(f"Hint: {index['password_hint']}")
    
    # Derive key from password
    salt = base64.b64decode(index['salt'])
    params = index.get('scrypt_params', {'n': 65536, 'r': 8, 'p': 1})
    
    key = scrypt(
        password=password,
        salt=salt,
        n=params['n'],
        r=params['r'],
        p=params['p'],
        dklen=32
    )
    
    # Try to decrypt
    try:
        decrypted = decrypt_data(index['encrypted_data'], key)
        return decrypted
    except DecryptionError:
        raise InvalidPassword("Incorrect password")
```

**Security Features**:
- **Scrypt KDF**: Resistant to GPU/ASIC attacks
- **High Cost Parameters**: n=65536 makes brute force expensive
- **Large Salt**: 256-bit salt prevents rainbow tables
- **Password Hints**: Optional, helps legitimate users

**Pros**:
- Simple to share - just need password
- No user management
- Can share password through different channel
- Password hints help users

**Cons**:
- Password must be shared securely
- Cannot change password after publishing
- No way to know who accessed
- Vulnerable to password sharing

## Security Comparison Table

| Feature | PUBLIC | PRIVATE | PROTECTED |
|---------|---------|---------|-----------|
| **Encryption** | ✅ AES-256-GCM | ✅ AES-256-GCM | ✅ AES-256-GCM |
| **Access Control** | ❌ None | ✅ Per-user | ✅ Password |
| **User Tracking** | ❌ No | ✅ Yes (locally) | ❌ No |
| **Revocable** | ❌ No | ❌ No | ❌ No |
| **Add Users Later** | ❌ No | ❌ No | ❌ No |
| **Zero-Knowledge** | ❌ N/A | ✅ Yes | ❌ No |
| **Brute Force Resistant** | ✅ N/A | ✅ Yes | ✅ Yes (scrypt) |
| **Setup Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Medium |

## Critical Security Points

### 1. All Decryption is Client-Side
```python
# This NEVER happens on servers:
def decrypt_on_server():  # ❌ NEVER DO THIS
    pass

# This ALWAYS happens on client:
def decrypt_on_client():  # ✅ ALWAYS
    # Download encrypted data
    encrypted = download_from_usenet(...)
    # Decrypt locally
    decrypted = decrypt_locally(encrypted, key)
```

### 2. Usenet Sees Only Encrypted Data
- All data posted to Usenet is encrypted
- Even "public" shares are encrypted
- Message IDs and subjects are obfuscated
- No correlation between shares and content

### 3. Access Strings Don't Contain Secrets
```python
# Access string for PUBLIC share:
{
    "share_id": "RANDOMID",
    "index_location": "<obfuscated@message.id>",
    # Key is IN the index on Usenet, not here
}

# Access string for PRIVATE share:
{
    "share_id": "RANDOMID",
    "index_location": "<obfuscated@message.id>",
    # User must provide their user_id separately
}

# Access string for PROTECTED share:
{
    "share_id": "RANDOMID",
    "index_location": "<obfuscated@message.id>",
    # User must provide password separately
}
```

### 4. Zero-Knowledge Proofs for Private Shares
Users prove they have access without revealing their identity:
```python
# User NEVER sends their actual user_id
# Instead, they prove they KNOW it:
proof = prove_knowledge_of(user_id)
is_authorized = verify_proof(proof)  # True/False

# Server/Usenet never learns the user_id
```

### 5. Folder Keys for Signatures
Every folder has Ed25519 keys for signatures:
```python
# Generated when folder first indexed
folder_keys = generate_ed25519_keypair()

# Private key: Stored locally, encrypts owner access
# Public key: Included in index for signature verification

# All indexes are signed
signature = folder_private_key.sign(index_data)
index['signature'] = signature
index['public_key'] = folder_public_key

# Clients verify signature
is_valid = verify_signature(index, index['public_key'])
```

## Implementation in Unified System

### Required Components

1. **SecurityManager**: Handles all encryption/decryption
2. **AccessControlManager**: Manages user authorization
3. **ZeroKnowledgeProofSystem**: For private share authentication
4. **KeyDerivationManager**: For password-based and user keys
5. **FolderKeyManager**: Manages Ed25519 keys per folder

### Database Requirements

```sql
-- Access control table (local only, never uploaded)
CREATE TABLE access_control (
    share_id VARCHAR(24) PRIMARY KEY,
    share_type VARCHAR(10),  -- public/private/protected
    created_by VARCHAR(64),  -- User who created share
    created_at TIMESTAMP,
    -- For private shares
    authorized_users TEXT,    -- JSON array of user IDs (encrypted)
    -- For protected shares  
    password_hint TEXT,       -- Optional hint
    -- Metadata
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

-- Folder keys table (local only)
CREATE TABLE folder_keys (
    folder_id VARCHAR(64) PRIMARY KEY,
    private_key BYTEA,  -- Encrypted with user's master key
    public_key BYTEA,
    created_at TIMESTAMP
);
```

### Testing Requirements

```python
def test_access_control():
    # Test PUBLIC access
    public_share = create_public_share(folder_id, files)
    # Anyone can download
    downloaded = download_public(public_share.access_string)
    assert downloaded == files
    
    # Test PRIVATE access
    authorized = ['user1', 'user2']
    private_share = create_private_share(folder_id, files, authorized)
    # Authorized user can access
    downloaded = download_private(private_share.access_string, 'user1')
    assert downloaded == files
    # Unauthorized user cannot
    with pytest.raises(AccessDenied):
        download_private(private_share.access_string, 'user3')
    
    # Test PROTECTED access
    password = 'SecurePassword123!'
    protected_share = create_protected_share(folder_id, files, password)
    # Correct password works
    downloaded = download_protected(protected_share.access_string, password)
    assert downloaded == files
    # Wrong password fails
    with pytest.raises(InvalidPassword):
        download_protected(protected_share.access_string, 'wrong')
```

## Migration Considerations

When unifying the system:

1. **Preserve all three access modes** - They serve different use cases
2. **Keep zero-knowledge proofs** - Critical for private share security
3. **Maintain scrypt parameters** - Don't reduce security for speed
4. **Keep client-side decryption** - Never decrypt on servers
5. **Preserve folder keys** - Needed for signatures and owner access
6. **Test access control thoroughly** - Security is critical

## Conclusion

The three-tier access system provides flexibility:
- **PUBLIC**: Easy sharing, no authentication
- **PRIVATE**: Controlled access, user tracking
- **PROTECTED**: Password-based, simple security

All three modes encrypt data and keep authentication client-side, ensuring Usenet servers never see sensitive information. The unified system must preserve all three modes as they serve distinct use cases and security requirements.