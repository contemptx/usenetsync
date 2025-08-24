#!/usr/bin/env python3
import sqlite3

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Create a temporary backup of network_servers
cursor.execute("CREATE TABLE IF NOT EXISTS network_servers_backup AS SELECT * FROM network_servers")

# Drop a table to simulate missing schema
cursor.execute("DROP TABLE IF EXISTS network_servers")

conn.commit()
print("Dropped network_servers table to simulate incomplete schema")

conn.close()
