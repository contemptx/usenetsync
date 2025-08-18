# Authorized Users Integration Plan

## Current Status

### ✅ Backend Implementation Complete

The backend already has full support for managing authorized users:

1. **Database**: 
   - `authorized_users` table exists
   - Stores folder_id, user_id, access_type, added_by, added_at

2. **Database Functions**:
   - `get_folder_authorized_users(folder_id)`
   - `add_folder_authorized_user(folder_id, user_id)`
   - `remove_folder_authorized_user(folder_id, user_id)`

3. **CLI Commands** (just added):
   - `publish-folder --user-ids <comma-separated-list>`
   - `add-authorized-user --folder-id <id> --user-id <id>`
   - `remove-authorized-user --folder-id <id> --user-id <id>`
   - `list-authorized-users --folder-id <id>`

4. **Tauri Commands** (just added):
   - `publish_folder` - now accepts user_ids and password parameters
   - `add_authorized_user`
   - `remove_authorized_user`
   - `get_authorized_users`

5. **Security System**:
   - `create_access_commitment` - creates ZK proof commitments for each user
   - `verify_user_access` - verifies user has access without revealing ID
   - Full integration with folder index creation

## Frontend Integration Needed

### FolderManagement.tsx Enhancements

The page needs to be updated to:

1. **State Management**:
   ```typescript
   const [selectedAccessType, setSelectedAccessType] = useState('public');
   const [authorizedUsers, setAuthorizedUsers] = useState<string[]>([]);
   const [protectedPassword, setProtectedPassword] = useState('');
   ```

2. **Load Authorized Users**:
   - When selecting a folder, load its authorized users
   - Call `get_authorized_users(folder_id)`

3. **Update Access Control Tab**:
   - Show PrivateShareManager component when access type is "private"
   - Show password field when access type is "protected"
   - Hide irrelevant fields based on selection

4. **Publish with Users**:
   - Pass authorized users to publish_folder when access type is private
   - Pass password when access type is protected

5. **Re-publish for Access Changes**:
   - Allow updating just the access control without re-uploading files
   - This updates only the core index with new access commitments

### Key Features to Highlight

1. **Independent Access Updates**: 
   - Users can be added/removed and the folder re-published without re-uploading files
   - Only the core index is updated with new access commitments

2. **Zero-Knowledge Proofs**:
   - User IDs are never stored directly
   - Only cryptographic commitments are stored in the index
   - Users prove they have access without revealing their ID

3. **Security Model**:
   - Folder owner manages the authorized users list
   - Users share their ID with folder owner out-of-band
   - Access is cryptographically enforced client-side

## Implementation Steps

1. ✅ Backend CLI commands - DONE
2. ✅ Tauri backend integration - DONE
3. ✅ PrivateShareManager component - DONE
4. ⏳ Update FolderManagement page to use existing functionality
5. ⏳ Add TypeScript API functions for the new commands
6. ⏳ Test the complete flow

## Example Usage Flow

1. **Folder Owner**:
   - Creates/uploads folder
   - Sets access type to "private"
   - Adds User IDs of authorized users
   - Publishes folder (creates index with access commitments)

2. **Updating Access** (key feature):
   - Owner adds/removes users from list
   - Re-publishes folder (only updates index, not files)
   - New users can immediately access
   - Removed users lose access

3. **User Access**:
   - User attempts to download private share
   - System uses their User ID to generate ZK proof
   - Proof is verified against commitments in index
   - Access granted if proof is valid

The system is designed so that access control can be updated independently of the folder contents, making it efficient to manage user access over time.