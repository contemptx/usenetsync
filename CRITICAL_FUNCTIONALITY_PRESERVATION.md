# Critical Functionality Preservation Guide

## Overview

This document outlines the critical functionality that MUST be preserved during the system unification, particularly around Usenet posting security and obfuscation.

## 1. Critical Security Features

### 1.1 Two-Layer Subject System

The system uses a **dual-subject architecture** for maximum security:

```python
@dataclass
class SubjectPair:
    """Two-layer subject system"""
    internal_subject: str  # 64 hex chars for verification (never posted to Usenet)
    usenet_subject: str    # 20 random chars for obfuscation (posted to Usenet)
```

**Critical Points:**
- **Internal Subject**: Used for cryptographic verification, stored locally only
- **Usenet Subject**: Completely random 20-character string posted to Usenet
- **No correlation**: Zero relationship between internal and Usenet subjects
- **No patterns**: Usenet subjects are purely random, no type prefixes or patterns

### 1.2 Message ID Obfuscation

Message IDs are generated to blend with legitimate traffic:

```python
def _generate_message_id(self, prefix=None):
    """Generate obfuscated unique message ID"""
    # Completely random, no timestamps or identifying prefixes
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    
    # Use ngPost.com domain to blend with legitimate ngPost traffic
    host_part = "ngPost.com"  # Or configured domain
    
    return f"<{random_str}@{host_part}>"
```

**Critical Points:**
- No timestamps in message IDs
- No identifying prefixes
- Blends with legitimate Usenet posting tools
- Random user agents from common tools

### 1.3 Share ID Security

Share IDs contain NO Usenet information:

```python
def generate_share_id(self, folder_id: str, share_type: str, version: int = 1) -> str:
    """Generate completely random share ID with no patterns"""
    # No underscores, no type prefixes, just random alphanumeric
    unique_data = f"{folder_id}:{share_type}:{version}:{time.time()}:{secrets.token_hex(16)}"
    full_hash = hashlib.sha256(unique_data.encode()).digest()
    
    # Base32 for readability (no 0/O or 1/l confusion)
    share_id = base64.b32encode(full_hash[:15]).decode('ascii').rstrip('=')
    return share_id[:24]  # Consistent length
```

**Critical Points:**
- Share IDs are completely random
- No embedded message IDs or subjects
- No type indicators (PUB/PRV/PWD prefixes)
- Usenet location data stored separately, encrypted

## 2. Data Flow Security

### 2.1 Upload Flow

```
1. File → Segments (768KB each)
2. Generate SubjectPair for each segment:
   - internal_subject = SHA256(private_key + folder_id + version + index + entropy)
   - usenet_subject = random_20_chars()
3. Create headers with obfuscation:
   - Message-ID: <random@ngPost.com>
   - Subject: usenet_subject (random)
   - User-Agent: Random from common tools
4. Post to Usenet:
   - Only usenet_subject and obfuscated message-id visible
   - Internal subject never leaves local system
5. Store mapping locally:
   - segment_id → message_id (encrypted)
   - segment_id → internal_subject (for verification)
```

### 2.2 Download Flow

```
1. Parse access string → get encrypted index location
2. Download index from Usenet (using obfuscated message-id)
3. Decrypt index locally:
   - For PUBLIC: Key included in access string
   - For PRIVATE: User's key required
   - For PROTECTED: Password required
4. Parse decrypted index → get segment mappings
5. Download segments using obfuscated message-ids
6. Verify using internal subjects (optional)
7. Reconstruct files
```

### 2.3 Access String Structure

Access strings contain encrypted references, not direct Usenet data:

```python
# Standard format (JSON, base64 encoded)
{
    "v": 3,                    # Version
    "id": "RANDOMSHARE24CHAR",  # Share ID (no patterns)
    "t": "public",             # Type
    "idx": {                   # Index reference (encrypted)
        "t": "s",              # single/multi
        "m": "<obfuscated@id>", # Obfuscated message ID
        "n": "alt.binaries.test" # Newsgroup
    }
}
```

## 3. Critical Components to Preserve

### 3.1 EnhancedSecuritySystem

**Must Preserve:**
- `generate_subject_pair()` - Two-layer subject generation
- `_generate_internal_subject()` - Cryptographic verification
- `_generate_usenet_subject()` - Random obfuscation
- Folder key management (Ed25519 keys)
- Zero-knowledge proof system for private shares

### 3.2 ProductionNNTPClient

**Must Preserve:**
- `_generate_message_id()` - Obfuscated message IDs
- Random user agent rotation
- `post_data()` with proper header construction
- Binary data handling with base64 encoding
- Connection pooling for performance

### 3.3 ShareIDGenerator

**Must Preserve:**
- Random share ID generation (no patterns)
- Access string creation (standard/compact/legacy)
- No Usenet data in share IDs
- Proper encryption of index references

### 3.4 Upload System

**Must Preserve:**
- Segment creation at 768KB boundaries
- Header obfuscation
- Queue management with priorities
- Retry logic with exponential backoff
- Progress tracking

### 3.5 Download System

**Must Preserve:**
- yEnc decoding support
- Base64 decoding for binary data
- Segment assembly with verification
- Resume capability
- Multiple retrieval methods (MESSAGE_ID, REDUNDANCY, SUBJECT_HASH)

## 4. Database Schema Requirements

### 4.1 Critical Tables

**segments table MUST include:**
```sql
CREATE TABLE segments (
    segment_id TEXT PRIMARY KEY,
    file_id TEXT,
    segment_index INTEGER,
    internal_subject TEXT,      -- For verification (never posted)
    usenet_subject TEXT,         -- Random, posted to Usenet
    message_id TEXT,             -- Obfuscated, returned by server
    newsgroup TEXT,
    segment_hash TEXT,           -- SHA256 of data
    encrypted_data BYTEA         -- Optional cached data
);
```

**shares table MUST include:**
```sql
CREATE TABLE shares (
    share_id VARCHAR(24) PRIMARY KEY,  -- Random, no patterns
    share_type VARCHAR(10),            -- public/private/protected
    encrypted_index TEXT,               -- Encrypted index data
    access_control JSONB,               -- Access rules
    -- NO direct Usenet references here
);
```

## 5. Testing Requirements

### 5.1 Security Tests

All tests from `verify_share_security.py` MUST pass:

1. **Share ID Randomness**: No patterns, no type prefixes
2. **No Data Leakage**: No Usenet data in share IDs
3. **Database Security**: No visible message IDs or subjects
4. **Access String Security**: Only encrypted references
5. **Client-Side Decryption**: All sensitive operations local

### 5.2 Functional Tests

1. **Upload/Download Cycle**: Complete roundtrip with verification
2. **Access Control**: Public/private/protected shares work correctly
3. **Large Files**: Handle 20TB+ datasets
4. **Resume Capability**: Downloads can be resumed
5. **Performance**: Meet throughput targets (100MB/s)

## 6. Migration Checklist

When unifying systems, ensure:

- [ ] Two-layer subject system preserved
- [ ] Message ID obfuscation maintained
- [ ] Share ID randomness verified
- [ ] No Usenet data in public interfaces
- [ ] Access strings properly encrypted
- [ ] Database schema includes all security fields
- [ ] Client-side decryption preserved
- [ ] Zero-knowledge proofs for private shares
- [ ] Random user agent rotation
- [ ] Binary data handling (base64/yEnc)
- [ ] All security tests pass
- [ ] Performance targets met

## 7. Code Examples

### 7.1 Unified Segment Upload

```python
class UnifiedUploadManager:
    def upload_segment(self, segment_data: bytes, metadata: dict):
        # 1. Generate subject pair (CRITICAL)
        subject_pair = self.security.generate_subject_pair(
            folder_id=metadata['folder_id'],
            file_version=metadata['version'],
            segment_index=metadata['index']
        )
        
        # 2. Build headers with obfuscation
        headers = {
            'From': 'poster@anonymous.net',
            'Subject': subject_pair.usenet_subject,  # Random 20 chars
            'Message-ID': self.nntp._generate_message_id(),  # Obfuscated
            'User-Agent': self._get_random_user_agent(),
            # NO identifying headers
        }
        
        # 3. Post with encrypted data
        response = self.nntp.post_data(
            subject=subject_pair.usenet_subject,
            data=segment_data,  # Will be base64 encoded if binary
            newsgroup='alt.binaries.test',
            extra_headers=headers
        )
        
        # 4. Store mapping (encrypted in database)
        self.db.store_segment_mapping(
            segment_id=metadata['segment_id'],
            internal_subject=subject_pair.internal_subject,  # Local only
            message_id=response.message_id,  # Obfuscated
            encrypted=True
        )
```

### 7.2 Unified Download

```python
class UnifiedDownloadManager:
    def download_share(self, access_string: str, password: Optional[str] = None):
        # 1. Parse access string (contains encrypted references)
        access_data = self.share_gen.parse_access_string(access_string)
        
        # 2. Download encrypted index
        index_data = self.nntp.retrieve_article(
            access_data['idx']['m'],  # Obfuscated message ID
            access_data['idx']['n']    # Newsgroup
        )
        
        # 3. Decrypt index locally (CRITICAL - client-side only)
        if access_data['t'] == 'public':
            decrypted = self.security.decrypt_public(index_data)
        elif access_data['t'] == 'private':
            decrypted = self.security.decrypt_private(index_data, self.user_id)
        else:  # protected
            decrypted = self.security.decrypt_protected(index_data, password)
        
        # 4. Download segments using obfuscated references
        for segment in decrypted['segments']:
            data = self.nntp.retrieve_article(
                segment['message_id'],  # Obfuscated
                segment['newsgroup']
            )
            # Verify using internal_subject if needed
```

## Conclusion

The unification MUST preserve all security features, particularly:
1. Two-layer subject system
2. Message ID obfuscation
3. Share ID randomness
4. Client-side encryption/decryption
5. No Usenet data exposure

Any changes that compromise these features would break the security model and must be avoided.