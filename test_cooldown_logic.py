#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Update an alert to have been triggered very recently (within cooldown)
cursor.execute("""
    UPDATE alerts 
    SET last_triggered = ?
    WHERE name = 'Queue Backlog'
""", ((datetime.now() - timedelta(seconds=30)).isoformat(),))

# Update another to have been triggered outside cooldown
cursor.execute("""
    UPDATE alerts 
    SET last_triggered = ?
    WHERE name = 'Failed Uploads'
""", ((datetime.now() - timedelta(minutes=10)).isoformat(),))

conn.commit()

print("Updated alert trigger times:")
print("- Queue Backlog: triggered 30 seconds ago (300s cooldown)")
print("- Failed Uploads: triggered 10 minutes ago (300s cooldown)")

conn.close()
