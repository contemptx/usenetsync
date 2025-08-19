# Unified Folder Management Solution

## Current Duplication Issue
- folders table: Original system with INTEGER id
- managed_folders table: Duplicate data from FolderManager
- Both tables store the same folders!

## Proposed Solution

### Option 1: Use ONLY folders table (RECOMMENDED)
- Modify FolderManager to use existing folders table
- Map columns appropriately:
  - folder_unique_id (UUID string) instead of folder_id
  - folder_path instead of path
  - display_name instead of name
- Add any missing columns to folders table if needed
- Remove managed_folders table entirely

### Option 2: Use managed_folders as primary
- Would require updating ALL existing code
- Would break file references (INTEGER vs UUID)
- Not recommended due to extensive changes needed

## Implementation Steps

1. Update FolderManager methods to query folders table
2. Use folder_unique_id for UUID storage
3. Keep INTEGER id for file references
4. Remove INSERT INTO managed_folders
5. Drop managed_folders table

This eliminates data duplication while maintaining compatibility!
