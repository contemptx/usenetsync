#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Configuration entries to add
configs = [
    ('license_type', 'professional'),
    ('license_status', 'active'),
    ('license_expiry', (datetime.now() + timedelta(days=30)).isoformat()),
    ('license_key', 'PROF-2024-ABCD-EFGH-IJKL-MNOP'),
    ('licensed_features', json.dumps([
        'basic',
        'advanced_indexing',
        'unlimited_folders',
        'priority_support',
        'api_access',
        'encryption',
        'backup_restore'
    ])),
    ('license_max_folders', '1000'),
    ('license_max_users', '50'),
    ('license_max_shares', '500')
]

# Insert configuration
for key, value in configs:
    cursor.execute("""
        INSERT OR REPLACE INTO configuration (key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """, (key, value, datetime.now().isoformat(), datetime.now().isoformat()))

# Also add some expired license config for testing
cursor.execute("""
    INSERT OR REPLACE INTO configuration (key, value, created_at, updated_at)
    VALUES (?, ?, ?, ?)
""", ('expired_license_expiry', (datetime.now() - timedelta(days=10)).isoformat(), 
      datetime.now().isoformat(), datetime.now().isoformat()))

conn.commit()

# Verify the configuration
cursor.execute("SELECT key, value FROM configuration WHERE key LIKE 'license_%' ORDER BY key")
print("License configuration added:")
for row in cursor.fetchall():
    if 'features' in row[0]:
        features = json.loads(row[1])
        print(f"  {row[0]}: {len(features)} features")
    elif 'key' in row[0]:
        print(f"  {row[0]}: {row[1][:8]}...")
    else:
        print(f"  {row[0]}: {row[1]}")

conn.close()
