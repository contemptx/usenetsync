#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

today = datetime.now().isoformat()

# Add some completed uploads today
for i in range(5):
    cursor.execute("""
        INSERT INTO upload_queue (
            queue_id, entity_id, entity_type, priority, state, 
            progress, queued_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"completed-upload-{i}",
        f"folder-{i}",
        "folder",
        1,
        "completed",
        100,
        today,
        today
    ))

# Add some failed uploads today
for i in range(3):
    cursor.execute("""
        INSERT INTO upload_queue (
            queue_id, entity_id, entity_type, priority, state, 
            progress, queued_at, completed_at, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"failed-upload-{i}",
        f"folder-fail-{i}",
        "folder",
        1,
        "failed",
        50,
        today,
        today,
        f"Connection timeout on attempt {i+1}"
    ))

# Check download_queue schema first
cursor.execute("PRAGMA table_info(download_queue)")
download_cols = [col[1] for col in cursor.fetchall()]

if 'queued_at' in download_cols:
    queued_col = 'queued_at'
else:
    queued_col = 'created_at'

# Add some completed downloads today
for i in range(7):
    cursor.execute(f"""
        INSERT INTO download_queue (
            queue_id, entity_id, entity_type, priority, state, 
            progress, {queued_col}, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"completed-download-{i}",
        f"share-{i}",
        "share",
        1,
        "completed",
        100,
        today,
        today
    ))

# Add some failed downloads today
for i in range(2):
    cursor.execute(f"""
        INSERT INTO download_queue (
            queue_id, entity_id, entity_type, priority, state, 
            progress, {queued_col}, completed_at, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"failed-download-{i}",
        f"share-fail-{i}",
        "share",
        1,
        "failed",
        30,
        today,
        today,
        f"Invalid segment hash on part {i+1}"
    ))

conn.commit()

# Get summary
cursor.execute("SELECT state, COUNT(*) FROM upload_queue GROUP BY state")
print("Upload queue summary:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.execute("SELECT state, COUNT(*) FROM download_queue GROUP BY state")
print("\nDownload queue summary:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
