#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Update to enterprise license with lower limits to test usage warnings
configs = [
    ('license_type', 'enterprise'),
    ('license_status', 'active'),
    ('license_expiry', (datetime.now() + timedelta(days=365)).isoformat()),
    ('license_key', 'ENT-2024-XXXX-YYYY-ZZZZ-9999'),
    ('licensed_features', json.dumps([
        'basic',
        'advanced_indexing',
        'unlimited_folders',
        'priority_support',
        'api_access',
        'encryption',
        'backup_restore',
        'multi_server',
        'redundancy_control',
        'custom_branding',
        'white_label',
        'sla_guarantee'
    ])),
    ('license_max_folders', '100'),  # Set low to be close to current usage (99)
    ('license_max_users', '10'),     # Set moderate
    ('license_max_shares', '5')      # Set to current usage (5)
]

for key, value in configs:
    cursor.execute("""
        UPDATE configuration 
        SET value = ?, updated_at = ?
        WHERE key = ?
    """, (value, datetime.now().isoformat(), key))

conn.commit()
conn.close()

print("Updated to enterprise license with usage near limits:")
print("- Max folders: 100 (current: 99)")
print("- Max users: 10 (current: 5)")
print("- Max shares: 5 (current: 5)")
