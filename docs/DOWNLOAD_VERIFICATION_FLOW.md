# UsenetSync Download Verification and Reassembly Flow

## Overview

When a user downloads content using a share ID, they DO NOT have access to our database. Instead, the entire download, verification, and reassembly process relies on the **encrypted index file** that contains all necessary metadata.

## The Index File Structure

The index file is the key to the entire download process. When a share is created, the system generates a comprehensive index containing:

```json
{
  "version": "1.0",
  "folder_id": "abc123",
  "created_at": "2024-01-01T00:00:00",
  "files": [
    {
      "file_id": 1,
      "file_path": "folder/subfolder/file.txt",
      "file_hash": "sha256_hash_of_complete_file",
      "file_size": 1024000,
      "segment_count": 10,
      "segments": [
        {
          "segment_index": 0,
          "segment_hash": "sha256_of_segment",
          "segment_size": 102400,
          "message_id": "<msgid@domain>",
          "usenet_subject": "obfuscated_subject_hash",
          "encrypted_location": "base64_encoded_location"
        },
        // ... more segments
      ]
    }
    // ... more files
  ]
}
```

## Download Flow

### 1. Share Access
- User provides share ID and credentials (password for protected, user ID for private)
- System retrieves the share's `encrypted_index` from database
- Index is decrypted based on share type

### 2. Index Provides Everything Needed

The decrypted index contains **ALL information required** for:

#### A. Segment Retrieval
- **Message IDs**: Direct pointers to Usenet articles
- **Usenet Subjects**: Obfuscated subjects for fallback retrieval
- **Encrypted Locations**: Additional location metadata if needed

#### B. Verification
- **Segment Hashes**: SHA256 hash of each segment for integrity verification
- **File Hashes**: SHA256 hash of complete files for final verification
- **Segment Sizes**: Expected size of each segment

#### C. Reassembly
- **Segment Index**: Exact order for reassembly (0, 1, 2, ...)
- **Segment Count**: Total number of segments per file
- **File Path**: Original folder structure to recreate
- **File Size**: Expected final file size

## Verification Process

### Phase 1: Segment Verification
```python
def verify_segment(segment_data, expected_hash, expected_size):
    # Check size
    if len(segment_data) != expected_size:
        return False
    
    # Check hash
    actual_hash = hashlib.sha256(segment_data).hexdigest()
    return actual_hash == expected_hash
```

### Phase 2: File Verification
```python
def verify_file(reconstructed_file, expected_hash, expected_size):
    # Check size
    if len(reconstructed_file) != expected_size:
        return False
    
    # Check hash
    actual_hash = hashlib.sha256(reconstructed_file).hexdigest()
    return actual_hash == expected_hash
```

## Reassembly Process

### 1. Segment Collection
```python
segments = []
for segment_info in file_info['segments']:
    # Retrieve from Usenet using message_id
    segment_data = retrieve_from_usenet(segment_info['message_id'])
    
    # Verify segment
    if verify_segment(segment_data, segment_info['segment_hash'], segment_info['segment_size']):
        segments.append({
            'index': segment_info['segment_index'],
            'data': segment_data
        })
```

### 2. Ordering and Assembly
```python
# Sort by segment_index from the index file
segments.sort(key=lambda x: x['index'])

# Concatenate in order
file_data = b''.join(segment['data'] for segment in segments)

# Verify complete file
if verify_file(file_data, file_info['file_hash'], file_info['file_size']):
    # Save to disk with original path structure
    save_file(file_data, file_info['file_path'])
```

## Why This Works Without Database Access

The index file is **self-contained** and includes:

1. **Complete Segment Map**: Every segment's location, order, and verification data
2. **Folder Structure**: Original paths to recreate directory hierarchy  
3. **Integrity Checks**: Hashes at both segment and file level
4. **No Database Needed**: All metadata travels with the share

## Subject Obfuscation Note

The two-subject system works as follows:

### Internal Subject (in database, not in index)
- Used for internal tracking and management
- Format: `[folder_id]_[file_id]_[segment_index]`
- Never exposed to downloaders

### Usenet Subject (in index, posted to Usenet)
- Obfuscated hash that reveals nothing about content
- Format: `hash(segment_data + salt + random)`
- Included in index for retrieval
- Cannot be reverse-engineered to reveal content

## Security Benefits

1. **No Database Access Required**: Downloaders never connect to our database
2. **Self-Verifying**: All verification data travels with the share
3. **Tamper-Evident**: Any modification breaks hash verification
4. **Privacy**: Obfuscated subjects reveal nothing about content
5. **Access Control**: Index encryption ensures only authorized users can download

## Example Download Scenario

1. User receives share ID: `a1b2c3d4e5f6`
2. User provides password: `SecretPass123`
3. System retrieves encrypted index from database
4. Index is decrypted using password
5. Index reveals:
   - 3 files with 10 segments each
   - Message IDs for all 30 segments
   - Hashes for verification
   - Original folder structure
6. Downloader retrieves segments from Usenet using message IDs
7. Each segment is verified against its hash
8. Segments are assembled in order (0-9 for each file)
9. Complete files are verified against file hashes
10. Files are saved with original folder structure

## Conclusion

**YES, the index file provides everything needed** for correct download, verification, and reassembly without any database access. The index is a complete, self-contained manifest that enables:

- Finding segments on Usenet (via message IDs)
- Verifying integrity (via hashes)
- Correct ordering (via segment indices)
- Folder reconstruction (via file paths)
- Access control (via encryption)

This design ensures that shares are portable, secure, and completely independent once created.