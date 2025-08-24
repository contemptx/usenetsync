#!/usr/bin/env python3
import requests
import json

# Get metrics
response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

print("=== System Metrics Summary ===")
print(f"Timestamp: {metrics['timestamp']}")
print()

print("CPU:")
print(f"  Usage: {metrics['system']['cpu']['percent']}%")
print(f"  Cores: {metrics['system']['cpu']['count']}")
print(f"  Frequency: {metrics['system']['cpu']['frequency_mhz']} MHz")
print()

print("Memory:")
mem = metrics['system']['memory']
print(f"  Total: {mem['total_mb']:.1f} MB")
print(f"  Used: {mem['used_mb']:.1f} MB ({mem['percent']}%)")
print(f"  Available: {mem['available_mb']:.1f} MB")
print()

print("Disk:")
disk = metrics['system']['disk']
print(f"  Total: {disk['total_gb']:.1f} GB")
print(f"  Used: {disk['used_gb']:.1f} GB ({disk['percent']}%)")
print(f"  Free: {disk['free_gb']:.1f} GB")
print()

print("Process (API Server):")
proc = metrics['process']
print(f"  PID: {proc['pid']}")
print(f"  CPU: {proc['cpu_percent']}%")
print(f"  Memory: {proc['memory_mb']:.1f} MB")
print(f"  Threads: {proc['threads']}")
print(f"  Open Files: {proc['open_files']}")
print(f"  Connections: {proc['connections']}")
print()

print("Database:")
db = metrics['database']
print(f"  Size: {db['size_mb']:.2f} MB")
print(f"  Folders: {db['folders_count']}")
print(f"  Files: {db['files_count']}")
print(f"  Segments: {db['segments_count']}")
print(f"  Shares: {db['shares_count']}")
print(f"  Users: {db['users_count']}")
print()

print("Network:")
net = metrics['network']
print(f"  NNTP Connected: {net['nntp_connected']}")
if 'pool_size' in net:
    print(f"  Connection Pool Size: {net['pool_size']}")
    print(f"  Active Connections: {net['pool_active']}")
print()

print("Queues:")
q = metrics['queues']
print(f"  Upload: {q['upload_active']}/{q['upload_total']} active")
print(f"  Download: {q['download_active']}/{q['download_total']} active")
