#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create a test folder
folder_id = str(uuid.uuid4())
folder_path = f"/workspace/uploading_folder_{datetime.now().timestamp()}"

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
    "uploading_test_folder",
    "default_user",
    500000,  # 500KB total
    10,      # 10 files
    20,      # 20 segments
    1,
    1, 1, 3,
    "uploading",
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

# Add upload queue status - in progress
cursor.execute("""
    INSERT INTO upload_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, uploaded_size, queued_at, started_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    folder_id,
    "folder",
    "uploading",
    65.5,  # 65.5% progress
    500000,
    327500,  # 327.5KB uploaded
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created uploading test folder with ID: {folder_id}")
print(f"- Status: uploading")
print(f"- Upload progress: 65.5%")
