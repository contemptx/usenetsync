#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Test scenario 1: Completed download
download_id_1 = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO download_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, downloaded_size, retry_count,
        queued_at, started_at, completed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    download_id_1,
    str(uuid.uuid4()),
    'folder',
    'completed',
    100,
    5242880,  # 5MB
    5242880,  # 5MB (fully downloaded)
    0,
    (datetime.now() - timedelta(minutes=10)).isoformat(),
    (datetime.now() - timedelta(minutes=10)).isoformat(),
    (datetime.now() - timedelta(minutes=5)).isoformat()
))
print(f"Created completed download: {download_id_1}")

# Test scenario 2: Failed download with error
download_id_2 = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO download_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, downloaded_size, retry_count, error_message,
        queued_at, started_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    download_id_2,
    str(uuid.uuid4()),
    'file',
    'failed',
    15,
    2097152,  # 2MB
    314572,   # ~300KB
    3,
    'Connection timeout after 3 retries',
    (datetime.now() - timedelta(minutes=20)).isoformat(),
    (datetime.now() - timedelta(minutes=19)).isoformat()
))
print(f"Created failed download: {download_id_2}")

# Test scenario 3: Queued download (not started)
download_id_3 = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO download_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, downloaded_size, retry_count,
        queued_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    download_id_3,
    str(uuid.uuid4()),
    'share',
    'queued',
    0,
    10485760,  # 10MB
    0,
    0,
    datetime.now().isoformat()
))
print(f"Created queued download: {download_id_3}")

conn.commit()
conn.close()
