#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Update to expired license
cursor.execute("""
    UPDATE configuration 
    SET value = ?
    WHERE key = 'license_expiry'
""", ((datetime.now() - timedelta(days=5)).isoformat(),))

cursor.execute("""
    UPDATE configuration 
    SET value = 'expired'
    WHERE key = 'license_status'
""")

conn.commit()
conn.close()

print("Updated license to expired state")
print(f"Expiry date set to: {(datetime.now() - timedelta(days=5)).isoformat()}")
