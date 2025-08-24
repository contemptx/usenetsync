#!/usr/bin/env python3
import sqlite3
import uuid
from datetime import datetime, timedelta

# Connect directly to the database
conn = sqlite3.connect('data/usenetsync.db')
cursor = conn.cursor()

# Add various alerts for testing
alerts = [
    ("CPU Usage High", "cpu_usage > 80", 80.0, "warning", "CPU usage exceeds 80%", 600, 1, None),
    ("Disk Space Low", "disk_free < 10", 10.0, "critical", "Less than 10GB free disk space", 1800, 1, (datetime.now() - timedelta(minutes=10)).isoformat()),
    ("Queue Backlog", "queue_size > 100", 100.0, "warning", "Upload queue has over 100 items", 300, 1, (datetime.now() - timedelta(minutes=2)).isoformat()),
    ("Database Size", "db_size > 500", 500.0, "info", "Database exceeds 500MB", 3600, 0, None),  # Disabled
    ("Failed Uploads", "failed_uploads > 5", 5.0, "critical", "More than 5 failed uploads", 300, 1, (datetime.now() - timedelta(seconds=100)).isoformat()),
    ("Network Disconnected", "network_status == 0", 0.0, "critical", "Network connection lost", 60, 0, None),  # Disabled
    ("Slow Indexing", "indexing_speed < 10", 10.0, "warning", "Indexing speed below 10 files/sec", 900, 1, None),
    ("Memory Leak", "memory_growth > 100", 100.0, "critical", "Memory usage growing rapidly", 300, 1, (datetime.now() - timedelta(hours=1)).isoformat()),
]

for name, condition, threshold, severity, message, cooldown, enabled, last_triggered in alerts:
    cursor.execute("""
        INSERT INTO alerts (
            alert_id, name, condition, threshold, severity, 
            message, cooldown_seconds, enabled, last_triggered,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        name,
        condition,
        threshold,
        severity,
        message,
        cooldown,
        enabled,
        last_triggered,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

conn.commit()

# Get summary
cursor.execute("SELECT severity, enabled, COUNT(*) FROM alerts GROUP BY severity, enabled ORDER BY severity, enabled")
print("Alert summary:")
for row in cursor.fetchall():
    status = "enabled" if row[1] else "disabled"
    print(f"  {row[0]} ({status}): {row[2]}")

conn.close()
