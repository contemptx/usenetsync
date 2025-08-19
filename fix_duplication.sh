#!/bin/bash
# Fix table duplication by using only folders table

echo "Fixing table duplication..."

# Replace managed_folders with folders in FolderManager
sed -i 's/managed_folders/folders/g' /workspace/src/folder_management/folder_manager.py

# Update column names to match folders table
sed -i 's/folder_id/folder_unique_id/g' /workspace/src/folder_management/folder_manager.py
sed -i 's/\bpath\b/folder_path/g' /workspace/src/folder_management/folder_manager.py  
sed -i 's/\bname\b/display_name/g' /workspace/src/folder_management/folder_manager.py

echo "Done! Now using only folders table."
