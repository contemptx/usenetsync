#!/usr/bin/env python3
import sqlite3

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Remove the latest migrations to simulate pending ones
cursor.execute("DELETE FROM schema_migrations WHERE version > 5")
conn.commit()

# Check current state
cursor.execute("SELECT MAX(version) as latest FROM schema_migrations")
result = cursor.fetchone()
print(f"Current latest migration: v{result[0]}")

cursor.execute("SELECT COUNT(*) as count FROM schema_migrations")
result = cursor.fetchone()
print(f"Total applied migrations: {result[0]}")

conn.close()
