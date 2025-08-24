#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Add more items to upload queue with different states
states = ['queued', 'uploading', 'uploading', 'paused', 'failed']
for state in states:
    cursor.execute("""
        INSERT INTO upload_queue (
            queue_id, entity_id, entity_type, state, progress,
            total_size, uploaded_size, queued_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        'folder',
        state,
        50 if state == 'uploading' else 0,
        1000000,
        500000 if state == 'uploading' else 0,
        datetime.now().isoformat()
    ))

# Add more items to download queue
states = ['queued', 'downloading', 'downloading', 'downloading', 'completed']
for state in states:
    cursor.execute("""
        INSERT INTO download_queue (
            queue_id, entity_id, entity_type, state, progress,
            total_size, downloaded_size, queued_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        'share',
        state,
        75 if state == 'downloading' else 100 if state == 'completed' else 0,
        2000000,
        1500000 if state == 'downloading' else 2000000 if state == 'completed' else 0,
        datetime.now().isoformat()
    ))

conn.commit()

# Get current counts
cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN state = 'uploading' THEN 1 ELSE 0 END) as active FROM upload_queue")
upload = cursor.fetchone()
cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN state = 'downloading' THEN 1 ELSE 0 END) as active FROM download_queue")
download = cursor.fetchone()

print(f"Upload queue: {upload[0]} total, {upload[1]} active")
print(f"Download queue: {download[0]} total, {download[1]} active")

conn.close()
