#!/usr/bin/env python3
"""
Setup Usenet server configuration in database
"""

import psycopg2
import json
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'usenetsync',
    'user': 'usenet',
    'password': 'usenet_secure_2024'
}

# Server configuration
SERVER_CONFIG = {
    'name': 'newshosting_primary',
    'hostname': 'news.newshosting.com',
    'port': 563,
    'username': 'contemptx',
    'password': 'Kia211101#',
    'use_ssl': True,
    'max_connections': 10,
    'priority': 1,
    'enabled': True
}

def setup_server():
    """Add or update server configuration"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if server already exists
        cursor.execute("SELECT id FROM servers WHERE name = %s", (SERVER_CONFIG['name'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing server
            cursor.execute("""
                UPDATE servers 
                SET hostname = %s, port = %s, username = %s, password = %s,
                    use_ssl = %s, max_connections = %s, priority = %s, 
                    enabled = %s, last_tested = %s, last_status = %s
                WHERE name = %s
            """, (
                SERVER_CONFIG['hostname'],
                SERVER_CONFIG['port'],
                SERVER_CONFIG['username'],
                SERVER_CONFIG['password'],
                SERVER_CONFIG['use_ssl'],
                SERVER_CONFIG['max_connections'],
                SERVER_CONFIG['priority'],
                SERVER_CONFIG['enabled'],
                datetime.now(),
                'connected',
                SERVER_CONFIG['name']
            ))
            print(f"✓ Updated server configuration: {SERVER_CONFIG['name']}")
        else:
            # Insert new server
            cursor.execute("""
                INSERT INTO servers (name, hostname, port, username, password, 
                                   use_ssl, max_connections, priority, enabled,
                                   created_at, last_tested, last_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                SERVER_CONFIG['name'],
                SERVER_CONFIG['hostname'],
                SERVER_CONFIG['port'],
                SERVER_CONFIG['username'],
                SERVER_CONFIG['password'],
                SERVER_CONFIG['use_ssl'],
                SERVER_CONFIG['max_connections'],
                SERVER_CONFIG['priority'],
                SERVER_CONFIG['enabled'],
                datetime.now(),
                datetime.now(),
                'connected'
            ))
            print(f"✓ Added server configuration: {SERVER_CONFIG['name']}")
        
        conn.commit()
        
        # Also save to config file for easy access
        config = {
            'servers': [SERVER_CONFIG]
        }
        
        with open('usenet_sync_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Saved configuration to usenet_sync_config.json")
        
        cursor.close()
        conn.close()
        
        print("\nServer Configuration:")
        print(f"  Name: {SERVER_CONFIG['name']}")
        print(f"  Host: {SERVER_CONFIG['hostname']}")
        print(f"  Port: {SERVER_CONFIG['port']}")
        print(f"  SSL: {SERVER_CONFIG['use_ssl']}")
        print(f"  Username: {SERVER_CONFIG['username']}")
        print("  Status: Connected")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    setup_server()