#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Clear existing migrations for testing
cursor.execute("DELETE FROM schema_migrations")

# Add migration history
migrations = [
    (1, "Initial schema creation", (datetime.now() - timedelta(days=30)).isoformat()),
    (2, "Add user permissions", (datetime.now() - timedelta(days=25)).isoformat()),
    (3, "Add network_servers table", (datetime.now() - timedelta(days=20)).isoformat()),
    (4, "Add indexing optimization", (datetime.now() - timedelta(days=15)).isoformat()),
    (5, "Add backup_recovery tables", (datetime.now() - timedelta(days=10)).isoformat()),
    (6, "Add monitoring alerts", (datetime.now() - timedelta(days=5)).isoformat()),
    (7, "Add download cache indexes", (datetime.now() - timedelta(days=2)).isoformat()),
]

for version, name, applied_at in migrations:
    cursor.execute("""
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES (?, ?, ?)
    """, (version, name, applied_at))

conn.commit()

# Verify
cursor.execute("SELECT * FROM schema_migrations ORDER BY version DESC")
print("Applied migrations:")
for row in cursor.fetchall():
    print(f"  v{row[0]}: {row[1]} (applied: {row[2]})")

conn.close()
