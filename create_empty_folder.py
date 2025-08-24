#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create an empty test folder
folder_id = str(uuid.uuid4())
folder_path = f"/workspace/empty_folder_{datetime.now().timestamp()}"

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
    "empty_test_folder",
    "default_user",
    0,  # No size
    0,  # No files
    0,  # No segments
    1,
    1, 1, 3,
    "active",  # Not indexed yet
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created empty test folder with ID: {folder_id}")
