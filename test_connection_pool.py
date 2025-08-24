#!/usr/bin/env python3
import sys
sys.path.insert(0, '/workspace/backend/src')

from unified.networking.connection_pool import UnifiedConnectionPool
import time

# Create pool with test server
servers = [{
    'host': 'news.newshosting.com',
    'port': 563,
    'ssl': True,
    'username': 'contemptx',
    'password': 'Kia211101#'
}]

pool = UnifiedConnectionPool(servers=servers, max_connections_per_server=5)

print("=== Testing Connection Pool ===")

# Test getting connections
print("\n1. Getting connections from pool...")
for i in range(3):
    try:
        with pool.get_connection() as conn:
            print(f"   Connection {i+1}: Got connection")
            # Simulate some work
            time.sleep(0.1)
    except Exception as e:
        print(f"   Connection {i+1}: Failed - {e}")

# Get statistics
stats = pool.get_statistics()
print("\n2. Pool Statistics:")
for server_id, server_stats in stats.items():
    print(f"   Server: {server_id}")
    print(f"   - Connections created: {server_stats['connections_created']}")
    print(f"   - Connections reused: {server_stats['connections_reused']}")
    print(f"   - Pool size: {server_stats['pool_size']}")

# Test health check
print("\n3. Health Check:")
try:
    health = pool.health_check()
    for server_id, is_healthy in health.items():
        print(f"   {server_id}: {'Healthy' if is_healthy else 'Unhealthy'}")
except Exception as e:
    print(f"   Health check failed: {e}")

# Clean up
pool.close()
print("\n4. Pool closed")
