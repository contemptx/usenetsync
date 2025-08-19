# Database Schema Analysis - UsenetSync

## Executive Summary
The current database has **29 tables** with significant duplication and inconsistency across different operations. Multiple tables store similar or overlapping data, leading to confusion and inefficiency.

## Major Issues Identified

### 1. **Duplicate Folder Management Tables**
- `folders` - Main folder table (currently using)
- `managed_folders` - Contains ALL columns from `folders` PLUS 20+ additional columns
  - This is complete duplication! 
  - We already fixed the code to use only `folders`, but `managed_folders` still exists

### 2. **Multiple Upload Tracking Systems**
We have FOUR different tables tracking uploads:
- `uploads` - Upload sessions (barely used: 1 SELECT)
- `upload_sessions` - Another upload session table (used: 3 queries)
- `upload_queue` - General upload queue (used: 4 queries)
- `segment_upload_queue` - Segment-specific queue (used: 6 queries)

**Problem**: Different parts of the system use different tables for the same purpose!

### 3. **Overlapping Share/Publication Tables**
- `shares` - Share information (heavily used: 29 queries)
- `publications` - Publication tracking (used: 6 queries)
- `published_indexes` - Published indexes (NOT USED AT ALL!)
- `authorized_users` - User authorization
- `access_control_local` - Access control

**Problem**: Share information is scattered across 5 tables!

### 4. **Inconsistent Column Naming**
Same data with different names across tables:
- Folder ID: `folder_id` vs `folder_unique_id`
- Timestamps: `created_at` vs `created_at TIMESTAMP` vs `created_at DATETIME`
- States: `state` vs `status` vs `current_operation`
- Sizes: `size` vs `file_size` vs `segment_size`

### 5. **Unused Tables**
Tables that exist but aren't used:
- `published_indexes` - 0 queries
- `managed_folders` - Only 1 SELECT (we migrated away from it)

## Current Operation Flow Analysis

### INDEXING Operation
Currently uses:
- `folders` - Store folder metadata
- `files` - Store file information
- `folder_operations` - Track operation progress

### SEGMENTATION Operation
Currently uses:
- `folders` - Get folder info
- `files` - Get files to segment
- `segments` - Store segment data
- `folder_operations` - Track progress

### UPLOAD Operation
Currently uses (INCONSISTENT!):
- `segments` - Get segments to upload
- `upload_sessions` - Track session
- `upload_queue` - Queue segments
- `segment_upload_queue` - Also queue segments (duplicate!)
- `folder_operations` - Track progress

### SHARING/PUBLICATION Operation
Currently uses (SCATTERED!):
- `folders` - Update access_type
- `shares` - Store share info
- `publications` - Also store publication info
- `authorized_users` - Store authorized users
- `access_control_local` - Also store access control

## Recommendations for Improvement

### 1. **Consolidate Folder Tables**
- Remove `managed_folders` completely (already migrated)
- Keep only `folders` as single source of truth

### 2. **Unify Upload Tracking**
Consolidate into single `upload_operations` table:
```sql
upload_operations (
  id, folder_id, segment_id, 
  operation_type (queue/upload/complete),
  state, priority, retry_count,
  started_at, completed_at, error_message
)
```
Remove: `uploads`, `upload_sessions`, `upload_queue`, `segment_upload_queue`

### 3. **Consolidate Sharing System**
Single `folder_shares` table:
```sql
folder_shares (
  id, folder_id, share_id, access_type,
  password_hash, authorized_users (JSON),
  created_at, expires_at, revoked_at
)
```
Remove: `shares`, `publications`, `published_indexes`, `authorized_users`, `access_control_local`

### 4. **Standardize Naming Conventions**
- Always use `folder_id` for folder references
- Always use `TIMESTAMP` for time columns
- Always use `state` for status tracking
- Always use `_size` suffix for sizes

### 5. **Create Clear Operation Tables**
```
folders -> files -> segments -> uploads -> shares
```
Each operation has ONE table for its data and uses `folder_operations` for progress.

## Benefits of Consolidation

1. **Reduced Complexity**: From 29 tables to ~15 tables
2. **Consistent Operations**: Each operation uses predictable tables
3. **Easier Maintenance**: No duplicate data to keep in sync
4. **Better Performance**: Fewer JOINs, clearer indexes
5. **Clearer Code**: Developers know exactly which table to use

## Migration Path

1. **Phase 1**: Remove unused tables (immediate)
   - Drop `published_indexes`
   - Drop `managed_folders` (after verifying no data)

2. **Phase 2**: Consolidate upload tables
   - Migrate data to new `upload_operations`
   - Update code to use single table

3. **Phase 3**: Consolidate sharing tables
   - Migrate to `folder_shares`
   - Update access control code

4. **Phase 4**: Standardize naming
   - Add migrations for column renames
   - Update all queries

## Current Table Usage Summary

### Heavily Used (Keep)
- `folders` (38 queries)
- `files` (28 queries)
- `segments` (36 queries)
- `shares` (29 queries)

### Lightly Used (Review)
- `upload_sessions` (3 queries)
- `upload_queue` (4 queries)
- `segment_upload_queue` (6 queries)
- `publications` (6 queries)

### Unused (Remove)
- `published_indexes` (0 queries)
- `managed_folders` (1 query - migration leftover)
- `uploads` (1 query)

## Conclusion

The current schema evolved organically with different developers adding tables for similar purposes. This has led to:
- **Duplication**: Same data in multiple places
- **Confusion**: Unclear which table to use
- **Inefficiency**: Extra JOINs and data syncing
- **Maintenance burden**: More tables to manage

A consolidation effort would significantly improve the system's clarity and performance.
