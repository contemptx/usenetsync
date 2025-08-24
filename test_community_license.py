#!/usr/bin/env python3
import sqlite3

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Delete all license configuration to test community defaults
cursor.execute("DELETE FROM configuration WHERE key LIKE 'license_%'")

conn.commit()
rows_deleted = cursor.rowcount
conn.close()

print(f"Deleted {rows_deleted} license configuration entries")
print("System should now return community license defaults")
