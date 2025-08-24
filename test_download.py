#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create a test download entry
download_id = str(uuid.uuid4())
entity_id = str(uuid.uuid4())

# Insert test download
cursor.execute("""
    INSERT INTO download_queue (
        queue_id, entity_id, entity_type, state, progress,
        total_size, downloaded_size, retry_count,
        queued_at, started_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    download_id,
    entity_id,
    'share',
    'downloading',
    45,  # 45% progress
    1048576,  # 1MB total
    471859,  # ~450KB downloaded
    0,
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created test download with ID: {download_id}")
