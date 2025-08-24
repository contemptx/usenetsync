#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create a folder for versioned files
folder_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO folders (
        folder_id, path, name, owner_id, 
        total_size, file_count, segment_count, version,
        encryption_enabled, compression_enabled, redundancy_level,
        status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    folder_id,
    "/workspace/versioned_folder",
    "versioned_folder",
    "default_user",
    300000, 3, 6, 1,
    1, 1, 3,
    "indexed",
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

# Create a file with multiple versions
file_id_base = str(uuid.uuid4())
base_hash = "hash_v1_" + uuid.uuid4().hex

# Version 1 - Original
cursor.execute("""
    INSERT INTO files (
        file_id, folder_id, path, name, size, hash,
        version, change_type, created_at, modified_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    file_id_base,  # Use same file_id for version tracking
    folder_id,
    "/workspace/versioned_folder/document.txt",
    "document.txt",
    10000,
    base_hash,
    1,
    "added",  # Valid change_type
    (datetime.now() - timedelta(days=5)).isoformat(),
    (datetime.now() - timedelta(days=5)).isoformat()
))

# Update the same file to version 2
cursor.execute("""
    UPDATE files 
    SET hash = ?, size = ?, version = ?, previous_version = ?, 
        change_type = ?, modified_at = ?
    WHERE file_id = ?
""", (
    "hash_v2_" + uuid.uuid4().hex,
    12000,
    2,
    1,
    "modified",
    (datetime.now() - timedelta(days=3)).isoformat(),
    file_id_base
))

# Update to version 3
final_hash = "hash_v3_" + uuid.uuid4().hex
cursor.execute("""
    UPDATE files 
    SET hash = ?, size = ?, version = ?, previous_version = ?, 
        change_type = ?, modified_at = ?
    WHERE file_id = ?
""", (
    final_hash,
    15000,
    3,
    2,
    "modified",
    (datetime.now() - timedelta(days=1)).isoformat(),
    file_id_base
))

# Add segments for the latest version
for i in range(3):
    cursor.execute("""
        INSERT INTO segments (
            segment_id, file_id, segment_index, size, hash,
            message_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        file_id_base,
        i,
        5000,
        f"segment_hash_{i}_" + uuid.uuid4().hex[:8],
        f"<msgid_{i}@news.example.com>",
        datetime.now().isoformat()
    ))

# Also create another file with the same hash (duplicate)
cursor.execute("""
    INSERT INTO files (
        file_id, folder_id, path, name, size, hash,
        version, change_type, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    folder_id,
    "/workspace/versioned_folder/document_backup.txt",
    "document_backup.txt",
    15000,
    final_hash,
    1,
    "added",
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created versioned file test data:")
print(f"- File with 3 versions (same file_id, updated)")
print(f"- Latest hash: {final_hash}")
print(f"- 3 segments for latest version")
print(f"- 1 duplicate file with same hash")
