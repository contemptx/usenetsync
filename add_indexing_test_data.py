#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Add some folders with different statuses
folders_to_add = [
    ("pending", 2),  # 2 pending folders
    ("failed", 1),   # 1 more failed folder
    ("indexing", 1), # 1 currently indexing
]

for status, count in folders_to_add:
    for i in range(count):
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
            f"/test/{status}_folder_{i}",
            f"{status}_folder_{i}",
            "default_user",
            100000 * (i + 1),
            5 * (i + 1),
            10 * (i + 1),
            1,
            1, 1, 3,
            status,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

# Add a recently indexed folder (within last 24 hours)
folder_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO folders (
        folder_id, path, name, owner_id, 
        total_size, file_count, segment_count, version,
        encryption_enabled, compression_enabled, redundancy_level,
        status, last_indexed, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    folder_id,
    "/test/recent_indexed",
    "recent_indexed_folder",
    "default_user",
    250000,
    10,
    20,
    1,
    1, 1, 3,
    "indexed",
    (datetime.now() - timedelta(hours=2)).isoformat(),  # Indexed 2 hours ago
    (datetime.now() - timedelta(hours=3)).isoformat(),  # Created 3 hours ago
    datetime.now().isoformat()
))

# Add files with duplicates to test duplicate detection
file_hashes = [
    ("duplicate_file_1.txt", "hash_dup_001", 50000),
    ("duplicate_file_2.txt", "hash_dup_001", 50000),  # Same hash as above
    ("duplicate_file_3.txt", "hash_dup_001", 50000),  # Same hash again
    ("unique_file_1.txt", "hash_unique_001", 75000),
    ("unique_file_2.txt", "hash_unique_002", 100000),
]

for name, hash_val, size in file_hashes:
    cursor.execute("""
        INSERT INTO files (
            file_id, folder_id, path, name, size, hash,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        folder_id,  # Use the recent folder
        f"/test/recent_indexed/{name}",
        name,
        size,
        hash_val,
        datetime.now().isoformat()
    ))

# Add a very large file
cursor.execute("""
    INSERT INTO files (
        file_id, folder_id, path, name, size, hash,
        created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    folder_id,
    "/test/recent_indexed/huge_file.bin",
    "huge_file.bin",
    50000000,  # 50MB
    "hash_huge_file",
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print("Added test data for indexing stats:")
print("- 2 pending folders")
print("- 1 additional failed folder")
print("- 1 indexing folder")
print("- 1 recently indexed folder (2 hours ago)")
print("- 3 duplicate files with same hash")
print("- 2 unique files")
print("- 1 huge file (50MB)")
