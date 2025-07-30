# UsenetSync GUI - Quick Reference Guide

## Key Concepts

### User ID
- **One-time generation** - Created once during initialization
- **Permanent identity** - Cannot be regenerated or exported
- **Secure storage** - Private keys remain in the system
- **Used for** - Identifying you in private shares

### Folder Keys
- **Per-folder encryption** - Each folder has unique keys
- **Managed automatically** - Created during indexing
- **Used for** - Encrypting folder contents

### Access Control
- **Folder-specific** - Each folder has its own access list
- **Three types**:
  - **Public**: Anyone with link can access
  - **Private**: Only authorized User IDs
  - **Protected**: Password required

## Common Operations

### Managing Folder Access

1. **View Current Access**
   - Select folder in navigation tree
   - Click "Access Control" tab
   - See list of authorized users

2. **Add Users to Private Folder**
   - In Access Control tab, click "Add User"
   - Enter User IDs (one per line)
   - Click "Add Users"

3. **Remove User Access**
   - Select users in access list
   - Click "Remove Selected"
   - Confirm removal

4. **Change Share Type**
   - Select new type (Public/Private/Protected)
   - For Protected: enter password and hint
   - Click "Update Access Settings"

### Segment Management

1. **View All Segments**
   - Select folder → "Segments" tab
   - See list with upload status (✓ or ⚠)

2. **Upload Specific Segments**
   - Select segments using checkboxes
   - Use quick filters (Failed/Missing)
   - Click "Upload Selected Segments"

3. **Verify Segment Integrity**
   - Actions tab → "Verify Integrity"
   - Checks all segments for corruption

### Selective Downloads

1. **Start Download**
   - Click "Download" in toolbar
   - Paste share access string
   - Click "Verify Share"

2. **Select Files**
   - Use checkboxes in file tree
   - Click folders to select all contents
   - Use "Select All/None" buttons

3. **Download Options**
   - **Preserve structure**: Keep original folders
   - **Skip existing**: Don't re-download files
   - **Verify integrity**: Check file hashes

## Important Notes

### Security Best Practices
- Never share your User ID private key
- Use strong passwords for protected shares
- Regularly verify folder integrity
- Monitor access logs

### Performance Tips
- Index folders during off-peak hours
- Upload segments in batches
- Use selective download for large shares
- Enable "Skip existing" to resume downloads

### Troubleshooting
- **Can't add user**: Verify User ID format
- **Upload fails**: Check NNTP connection
- **Download stuck**: Check segment availability
- **Access denied**: Verify you're authorized

## Keyboard Shortcuts

- `Ctrl+I` - Initialize/view user
- `Ctrl+F` - Index folder
- `Ctrl+P` - Publish share
- `Ctrl+D` - Download share
- `F5` - Refresh all data
- `Space` - Toggle checkbox in trees
- `Ctrl+A` - Select all (in trees)
- `Ctrl+N` - Select none (in trees)

## Status Indicators

### File/Folder States
- ✓ - Successfully uploaded/verified
- ⚠ - Failed or missing segments
- 🔒 - Encrypted content
- 📁 - Folder with subfolders

### Share Types
- `[PUB]` - Public share
- `[PRV]` - Private share
- `[PWD]` - Password-protected

### Connection Status
- Green - Connected to NNTP
- Yellow - Connecting/Retrying
- Red - Disconnected/Error