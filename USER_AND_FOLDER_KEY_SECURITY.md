# User ID and Folder Key Security Documentation

## Critical Security Fundamentals

This document outlines two foundational security components that MUST be preserved in any system unification: the permanent User ID system and the Folder Key system.

## 1. User ID System

### Core Principle: One-Time Generation, Never Regenerated

The User ID is the cornerstone of the security model. It is generated ONCE and can NEVER be regenerated. This is not a convenience feature - it's a critical security requirement.

### User ID Generation

```python
def generate_user_id() -> str:
    """
    Generate cryptographically secure 64-character hex User ID
    This is permanent and should only be generated once
    """
    # Combine multiple entropy sources
    entropy_sources = [
        os.urandom(32),                    # OS entropy
        str(time.time()).encode(),         # Timestamp
        str(os.getpid()).encode(),         # Process ID
        secrets.token_bytes(32)             # Additional randomness
    ]
    
    combined = b''.join(entropy_sources)
    
    # Generate 64-character hex ID (256 bits)
    user_id = hashlib.sha256(combined).hexdigest()
    
    logger.info(f"Generated new User ID: {user_id[:8]}...")
    return user_id
```

### One-Time Initialization

```python
def initialize_user(self, display_name: Optional[str] = None) -> str:
    """Initialize user with new ID if not exists"""
    if self._user_id:
        logger.info("User already initialized")
        return self._user_id  # NEVER generate a new one
    
    # Generate new ID - ONLY happens once per installation
    user_id = self.generate_user_id()
    
    # Save to database permanently
    self.db.initialize_user(user_id, display_name)
    
    return user_id
```

### Security Implications

#### Why User IDs Cannot Be Regenerated:

1. **Access Control Integrity**
   - Private shares are tied to specific User IDs
   - If users could regenerate IDs, they could potentially:
     - Bypass access controls
     - Impersonate other users
     - Access shares they shouldn't have

2. **Zero-Knowledge Proof System**
   ```python
   # Access commitments are created for specific User IDs
   commitment = create_access_commitment(user_id="abc123...")
   
   # If user could regenerate to "abc123...", they'd gain access
   # This MUST be prevented
   ```

3. **Audit Trail**
   - User actions are tied to their permanent ID
   - Regeneration would break accountability

#### Reinstallation Scenario

```python
# User reinstalls software
# Old User ID: "a1b2c3d4..."  (lost)
# New User ID: "e5f6g7h8..."  (newly generated)

# Result: User must request access again
# This is BY DESIGN for security

# Folder owner must explicitly grant access to new ID:
authorized_users.append("e5f6g7h8...")  # New ID
# Old ID "a1b2c3d4..." no longer has access
```

### Database Storage

```sql
-- User configuration (single row, ID always 1)
CREATE TABLE user_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Only one user
    user_id VARCHAR(64) UNIQUE NOT NULL,    -- 64-char hex, NEVER changes
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Once set, user_id can NEVER be updated
);

-- Prevent updates to user_id
CREATE TRIGGER prevent_user_id_update
BEFORE UPDATE ON user_config
FOR EACH ROW
WHEN OLD.user_id != NEW.user_id
BEGIN
    SELECT RAISE(ABORT, 'User ID cannot be changed');
END;
```

### User ID Usage in Security

The User ID is used for:

1. **Key Derivation**
   ```python
   def derive_user_key(user_id: str, folder_id: str) -> bytes:
       """Derive user-specific key for folder access"""
       return HKDF(
           input=user_id + folder_id,
           salt=folder_salt,
           info=b'user_folder_key'
       )
   ```

2. **Access Commitments**
   ```python
   def create_access_commitment(user_id: str):
       # Hash user_id with salt (never store plaintext)
       salt = secrets.token_hex(16)
       user_id_hash = hash(user_id + salt)
       
       # Create zero-knowledge proof parameters
       zk_params = generate_zk_params(user_id)
       
       return AccessCommitment(
           user_id_hash=user_id_hash,
           salt=salt,
           proof_params=zk_params
       )
   ```

3. **Subject Generation**
   ```python
   def generate_internal_subject(user_id: str, folder_id: str):
       # User ID contributes to subject generation
       subject_data = user_id + folder_id + segment_info
       return hashlib.sha256(subject_data).hexdigest()
   ```

## 2. Folder Key System

### Core Principle: Every Folder Has Unique Ed25519 Keys

When a folder is first indexed, it receives a permanent Ed25519 key pair. These keys are fundamental to the security model.

### Folder Key Generation

```python
def generate_folder_keys(self, folder_id: str) -> FolderKeys:
    """Generate Ed25519 key pair for folder"""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    return FolderKeys(
        private_key=private_key,
        public_key=public_key,
        folder_id=folder_id,
        created_at=datetime.now()
    )
```

### Key Storage

```python
def save_folder_keys(self, folder_id: str, keys: FolderKeys):
    """Save folder keys to database (encrypted)"""
    # Private key is encrypted with user's master key
    encrypted_private = encrypt_with_user_key(
        keys.private_key.private_bytes(),
        self.user_master_key
    )
    
    # Public key can be stored plaintext
    public_bytes = keys.public_key.public_bytes()
    
    self.db.save_folder_keys(
        folder_id=folder_id,
        private_key=encrypted_private,
        public_key=public_bytes
    )
```

### Folder Key Usage

#### 1. Index Signing
Every index posted to Usenet is signed with the folder's private key:

```python
def sign_index(index_data: dict, folder_keys: FolderKeys):
    """Sign index with folder private key"""
    # Serialize index
    index_bytes = json.dumps(index_data, sort_keys=True).encode()
    
    # Sign with private key
    signature = folder_keys.private_key.sign(index_bytes)
    
    # Include public key for verification
    index_data['public_key'] = base64.b64encode(
        folder_keys.public_key.public_bytes()
    )
    index_data['signature'] = base64.b64encode(signature)
    
    return index_data
```

#### 2. Owner Privileges
The folder creator (owner) has special access through folder keys:

```python
def create_owner_access(folder_keys: FolderKeys, session_key: bytes):
    """Create owner's wrapped key using folder keys"""
    # Derive wrapping key from folder private key
    owner_wrapping_key = derive_from_private_key(
        folder_keys.private_key
    )
    
    # Wrap session key for owner
    owner_wrapped_key = wrap_key(session_key, owner_wrapping_key)
    
    return owner_wrapped_key
```

#### 3. Subject Generation
Folder keys contribute to subject generation for segments:

```python
def generate_internal_subject(folder_keys: FolderKeys, segment_info: dict):
    """Generate internal subject using folder keys"""
    private_bytes = folder_keys.private_key.private_bytes()
    
    subject_data = (
        private_bytes +
        segment_info['file_id'].encode() +
        segment_info['segment_index'].to_bytes(4, 'big')
    )
    
    return hashlib.sha256(subject_data).hexdigest()
```

#### 4. Signature Verification
Clients verify index signatures using the public key:

```python
def verify_index_signature(index_data: dict) -> bool:
    """Verify index was signed by folder owner"""
    # Extract public key
    public_key_bytes = base64.b64decode(index_data['public_key'])
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(
        public_key_bytes
    )
    
    # Extract signature
    signature = base64.b64decode(index_data['signature'])
    
    # Prepare data (without signature/public_key fields)
    verify_data = index_data.copy()
    del verify_data['signature']
    del verify_data['public_key']
    
    # Verify
    try:
        public_key.verify(
            signature,
            json.dumps(verify_data, sort_keys=True).encode()
        )
        return True
    except InvalidSignature:
        return False
```

### Database Schema

```sql
-- Folder keys table (local only, never uploaded)
CREATE TABLE folder_keys (
    folder_id VARCHAR(64) PRIMARY KEY,
    private_key BYTEA NOT NULL,  -- ENCRYPTED with user's key
    public_key BYTEA NOT NULL,   -- Can be plaintext
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Keys are permanent once created
    CONSTRAINT no_key_updates CHECK (false) ON UPDATE
);

-- Folders table references keys
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    folder_unique_id VARCHAR(64) UNIQUE,
    has_keys BOOLEAN DEFAULT FALSE,
    -- ... other fields
    FOREIGN KEY (folder_unique_id) REFERENCES folder_keys(folder_id)
);
```

## 3. Integration of User ID and Folder Keys

### Access Control Flow

```python
def grant_access_to_folder(folder_id: str, user_id: str):
    """Grant user access to folder"""
    # 1. Load folder keys (proves ownership)
    folder_keys = load_folder_keys(folder_id)
    if not folder_keys:
        raise Error("Not folder owner")
    
    # 2. Create access commitment for user
    commitment = create_access_commitment(user_id, folder_id)
    
    # 3. Derive user-specific key
    user_key = derive_user_key(user_id, folder_id)
    
    # 4. Wrap session key for user
    wrapped_key = wrap_key(session_key, user_key)
    
    # 5. Sign with folder keys
    signature = folder_keys.private_key.sign(commitment)
    
    return AccessGrant(
        commitment=commitment,
        wrapped_key=wrapped_key,
        signature=signature
    )
```

### Security Properties

1. **Non-Repudiation**: Folder keys sign all indexes
2. **Access Control**: User IDs determine who can decrypt
3. **Forward Secrecy**: Lost User IDs cannot be recovered
4. **Owner Control**: Folder creator maintains special access

## 4. Critical Implementation Requirements

### MUST Preserve:

1. **User ID Permanence**
   - Once generated, NEVER allow regeneration
   - Database constraints to prevent updates
   - Clear warnings about lost IDs

2. **Folder Key Persistence**
   - Keys generated on first index
   - Never regenerated or changed
   - Private keys always encrypted

3. **Security Workflows**
   - User must request access after reinstall
   - Folder owner must explicitly grant access
   - No backdoors or recovery mechanisms

### MUST NOT Implement:

1. **User ID Recovery**
   ```python
   def recover_user_id():  # ❌ NEVER
       """This must NEVER exist"""
       pass
   ```

2. **Key Regeneration**
   ```python
   def regenerate_folder_keys():  # ❌ NEVER
       """This must NEVER exist"""
       pass
   ```

3. **Bypass Mechanisms**
   ```python
   def admin_override():  # ❌ NEVER
       """No admin overrides"""
       pass
   ```

## 5. Testing Requirements

### User ID Tests

```python
def test_user_id_permanence():
    """Test that User ID cannot be regenerated"""
    # Initialize user
    user_id_1 = security.initialize_user("Alice")
    
    # Try to initialize again
    user_id_2 = security.initialize_user("Alice")
    
    # Must be the same
    assert user_id_1 == user_id_2
    
    # Try to force regeneration
    with pytest.raises(SecurityError):
        security.generate_user_id()  # Should fail if already initialized

def test_reinstall_scenario():
    """Test that reinstall requires new access"""
    # User 1 creates folder
    user1_id = initialize_user()
    folder_id = index_folder()
    share = create_private_share(folder_id, [user1_id])
    
    # Simulate reinstall (new database)
    reset_database()
    user2_id = initialize_user()  # Different ID
    
    # Old user cannot access
    assert user1_id != user2_id
    with pytest.raises(AccessDenied):
        download_share(share, user2_id)
```

### Folder Key Tests

```python
def test_folder_keys_permanent():
    """Test that folder keys are permanent"""
    # Generate keys
    folder_id = "test_folder"
    keys1 = generate_folder_keys(folder_id)
    save_folder_keys(folder_id, keys1)
    
    # Load keys
    keys2 = load_folder_keys(folder_id)
    
    # Must be identical
    assert keys1.private_key == keys2.private_key
    assert keys1.public_key == keys2.public_key
    
    # Cannot regenerate
    with pytest.raises(SecurityError):
        generate_folder_keys(folder_id)  # Should fail if exists

def test_signature_verification():
    """Test index signature verification"""
    # Create and sign index
    folder_keys = generate_folder_keys("test")
    index = create_index(...)
    signed_index = sign_index(index, folder_keys)
    
    # Verify with public key
    assert verify_index_signature(signed_index)
    
    # Tampered index fails
    signed_index['data'] = "tampered"
    assert not verify_index_signature(signed_index)
```

## Conclusion

The User ID and Folder Key systems are foundational to UsenetSync's security model:

1. **User IDs** are permanent, ensuring access control integrity
2. **Folder Keys** provide ownership proof and signing capability
3. **No regeneration** prevents security bypasses
4. **Reinstalls require re-authorization** by design

These are not convenience features but critical security requirements. Any system unification MUST preserve these exact behaviors to maintain security integrity.