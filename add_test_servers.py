#!/usr/bin/env python3
import sqlite3
import uuid

conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Add additional test servers
servers = [
    ("Newshosting Backup", "news2.newshosting.com", 563, True, "contemptx", "Kia211101#", 5, 2, 1),
    ("Test Server 1", "test.usenet.com", 119, False, "testuser", "testpass", 3, 3, 0),
]

for name, host, port, ssl, username, password, max_conn, priority, enabled in servers:
    cursor.execute("""
        INSERT INTO network_servers (
            server_id, name, host, port, ssl_enabled, 
            username, password, max_connections, priority, enabled,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (
        str(uuid.uuid4()),
        name,
        host,
        port,
        ssl,
        username,
        password,
        max_conn,
        priority,
        enabled
    ))

conn.commit()

# Show all servers
cursor.execute("SELECT name, host, port, enabled FROM network_servers")
print("Network servers in database:")
for row in cursor.fetchall():
    status = "enabled" if row[3] else "disabled"
    print(f"  - {row[0]}: {row[1]}:{row[2]} ({status})")

conn.close()
