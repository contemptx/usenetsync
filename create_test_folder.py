#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create a test folder
folder_id = str(uuid.uuid4())
folder_path = f"/workspace/test_folder_{datetime.now().timestamp()}"

# Insert folder
cursor.execute("""
    INSERT INTO folders (
        folder_id, path, name, owner_id, 
        total_size, file_count, segment_count, version,
        encryption_enabled, compression_enabled, redundancy_level,
        status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    folder_id,
    folder_path,
    "test_folder_18",
    "default_user",
    150000,  # 150KB total
    3,       # 3 files
    6,       # 6 segments
    1,
    1, 1, 3,
    "indexed",
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

# Add some files
file_ids = []
for i in range(3):
    file_id = str(uuid.uuid4())
    file_ids.append(file_id)
    cursor.execute("""
        INSERT INTO files (
            file_id, folder_id, path, name, size, hash,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        file_id,
        folder_id,
        f"{folder_path}/file_{i+1}.txt",
        f"file_{i+1}.txt",
        50000,  # 50KB each
        f"hash_{i+1}_" + uuid.uuid4().hex[:16],
        datetime.now().isoformat()
    ))

# Add some segments for each file
for file_id in file_ids:
    for j in range(2):  # 2 segments per file
        cursor.execute("""
            INSERT INTO segments (
                segment_id, file_id, segment_index, size, hash,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            file_id,
            j,
            25000,  # 25KB per segment
            f"segment_hash_{j}_" + uuid.uuid4().hex[:8],
            datetime.now().isoformat()
        ))

# Add a full share for the folder
share_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO shares (
        share_id, folder_id, owner_id, share_type, 
        access_type, access_level, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    share_id,
    folder_id,
    "default_user",
    "full",      # share_type must be: full, partial, incremental
    "public",    # access_type must be: public, private, protected
    "public",    # access_level must be: public, private, protected
    datetime.now().isoformat()
))

# Add another partial share
share_id2 = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO shares (
        share_id, folder_id, owner_id, share_type, 
        access_type, access_level, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    share_id2,
    folder_id,
    "default_user",
    "partial",   # share_type
    "private",   # access_type
    "private",   # access_level
    datetime.now().isoformat()
))

# Add upload queue status
cursor.execute("""
    INSERT INTO upload_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, uploaded_size, queued_at, started_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    folder_id,
    "folder",
    "completed",
    100,
    150000,
    150000,
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created test folder with ID: {folder_id}")
print(f"- 3 files")
print(f"- 6 segments")
print(f"- 2 shares (1 full/public, 1 partial/private)")
print(f"- Upload status: completed")
