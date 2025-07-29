# Folder ID Standardization Migration Guide

## Overview
The system has been standardized to use `folder_unique_id` (string) consistently throughout all security operations. This ensures cryptographic consistency and prevents confusion between database IDs and unique identifiers.

## What Changed

### Before (Mixed Usage)
```python
# Create folder returns database ID (integer)
folder_db_id = app.db.create_folder(folder_unique_id="my_folder", ...)

# Security operations were inconsistent
keys = app.security.generate_folder_keys("my_folder")  # Used string
app.security.save_folder_keys(folder_db_id, keys)     # Used integer - PROBLEM!
loaded_keys = app.security.load_folder_keys("my_folder")  # Expected string
```

### After (Standardized)
```python
# Create folder still returns database ID, but we use unique_id for security
folder_db_id = app.db.create_folder(folder_unique_id="my_folder", ...)

# All security operations now use folder_unique_id consistently
keys = app.security.generate_folder_keys("my_folder")    # String
app.security.save_folder_keys("my_folder", keys)        # String
loaded_keys = app.security.load_folder_keys("my_folder") # String
```

## Migration Steps

### 1. Update Existing Code

Replace all calls to `save_folder_keys` to use folder_unique_id:

```python
# OLD:
app.security.save_folder_keys(folder_db_id, keys)

# NEW:
app.security.save_folder_keys(folder_unique_id, keys)
```

### 2. Use the Helper Class

For code that needs to convert between ID types:

```python
from folder_id_helper import FolderIDHelper

helper = FolderIDHelper(app.db)

# Convert database ID to unique ID
folder_unique_id = helper.get_unique_id(folder_db_id)

# Convert unique ID to database ID (if needed for database operations)
folder_db_id = helper.get_db_id(folder_unique_id)
```

### 3. Best Practices

1. **Always use folder_unique_id for security operations:**
   - `generate_folder_keys(folder_unique_id)`
   - `save_folder_keys(folder_unique_id, keys)`
   - `load_folder_keys(folder_unique_id)`
   - `sign_data(data, folder_unique_id)`
   - `verify_signature(data, signature, folder_unique_id)`
   - `generate_subject_pair(folder_id=folder_unique_id, ...)`
   - `generate_share_id(folder_unique_id, share_type)`

2. **Store folder_unique_id in your application state:**
   ```python
   # When creating a folder
   folder_db_id = app.db.create_folder(folder_unique_id="my_folder", ...)
   # Store "my_folder" not folder_db_id for future operations
   ```

3. **Use database ID only for database-specific operations:**
   - Updating folder statistics
   - Direct SQL queries
   - Foreign key relationships

## Benefits

1. **Consistency**: All cryptographic operations use the same identifier
2. **Security**: Subject generation and key derivation are consistent
3. **Clarity**: No confusion about which ID type to use
4. **Portability**: Folder unique IDs are portable across systems

## Testing

Run the test script to verify your migration:
```bash
python test_standardized_folder_id.py
```
