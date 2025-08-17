# Version Control Feature Explanation for UsenetSync

## What is Version Control in UsenetSync Context?

Version control for UsenetSync would allow users to:

### 1. **File Versioning**
- Keep multiple versions of the same file when uploading updates
- Track changes over time
- Restore previous versions if needed

### 2. **How It Would Work with Usenet**

Since Usenet posts are immutable (can't be edited once posted), version control would work by:

```
Example:
- User uploads "document.pdf" → Creates Share ID: ABC123 (v1)
- User updates document and re-uploads → Creates new Share ID: DEF456 (v2)
- System maintains a version chain linking ABC123 → DEF456
```

### 3. **Implementation Approach**

```python
# Database would track version relationships
file_versions = {
    "document.pdf": [
        {
            "version": 1,
            "share_id": "ABC123",
            "uploaded": "2024-01-01",
            "size": 1024000,
            "hash": "sha256:abcd..."
        },
        {
            "version": 2,
            "share_id": "DEF456", 
            "uploaded": "2024-01-15",
            "size": 1124000,
            "hash": "sha256:efgh...",
            "changes": "Updated section 3"
        }
    ]
}
```

### 4. **UI Features Needed**

- **Version History Panel**: Show all versions of a file
- **Diff Viewer**: Compare what changed between versions (for text files)
- **Version Selector**: Choose which version to download
- **Auto-versioning**: Automatically create new version when re-uploading same filename

### 5. **Benefits**
- Never lose old versions of important files
- Track document evolution
- Collaborate with version notes
- Rollback to previous versions if needed

### 6. **Challenges with Usenet**
- Each version consumes new storage (no in-place updates)
- Old versions remain on Usenet servers (can't delete)
- Need to maintain version metadata locally

## Is This Feature Needed?

**Probably NOT for MVP** because:
1. Users can manually manage versions by uploading with different names
2. Adds complexity to the share system
3. Usenet storage costs increase with each version
4. Most users just need latest version

**Could be useful if**:
- Users frequently update shared documents
- Need audit trail of changes
- Collaborative document workflows
- Legal/compliance requirements

## Recommendation

This is a "nice to have" feature that could be added later if users request it. The core sharing functionality works fine without it. Users who need versioning can use naming conventions like:
- `document_v1.pdf`
- `document_v2.pdf`
- `document_2024-01-15.pdf`