#!/usr/bin/env python3
import requests
import json

response = requests.get("http://localhost:8000/api/v1/monitoring/system_status")
data = response.json()

print("=== SYSTEM STATUS SUMMARY ===")
print(f"Status: {data['status']}")
print(f"Health: {data['health']}")
print(f"Timestamp: {data['timestamp']}")

print("\n=== CORE SYSTEM ===")
core = data['core']
print(f"Operational: {core['operational']}")
print(f"Uptime: {core['uptime_seconds']} seconds")
print(f"Version: {core['version']}")
print(f"Environment: {core['environment']}")

print("\n=== DATABASE ===")
db = data['database']
print(f"Connected: {db['connected']}")
print(f"Type: {db['type']}")
print(f"Health: {db['health']}")
print(f"Size: {db['size_mb']} MB")
print(f"Total Records: {db['total_records']}")

print("\n=== NNTP/USENET ===")
nntp = data['nntp']
print(f"Connected: {nntp['connected']}")
print(f"Health: {nntp['health']}")
print(f"Servers: {len(nntp['servers'])} configured")
for server in nntp['servers']:
    print(f"  - {server['name']}: {server['host']}:{server['port']} ({server['status']})")

print("\n=== QUEUES ===")
queues = data['queues']
print("Upload Queue:")
for key, val in queues['upload_queue'].items():
    print(f"  {key}: {val}")
print("Download Queue:")
for key, val in queues['download_queue'].items():
    print(f"  {key}: {val}")

print("\n=== RESOURCES ===")
res = data['resources']
print(f"CPU: {res['cpu']['percent']}% ({res['cpu']['cores']} cores)")
print(f"Memory: {res['memory']['percent']}% ({res['memory']['used_gb']}/{res['memory']['total_gb']} GB)")
print(f"Disk: {res['disk']['percent']}% ({res['disk']['used_gb']}/{res['disk']['total_gb']} GB)")
print(f"Network: {res['network']['established']}/{res['network']['connections']} connections")

print("\n=== SUBSYSTEMS ===")
for name, info in data['subsystems'].items():
    print(f"{name}: {info['status']} ({info['health']})")

print("\n=== PERFORMANCE ===")
perf = data['performance']
print(f"Response Time: {perf['response_time_ms']} ms")
print(f"Error Rate: {perf['error_rate']}%")
print(f"Requests/sec: {perf['requests_per_second']}")
print(f"Throughput: {perf['throughput_mbps']} Mbps")
if 'active_uploads' in perf:
    print(f"Active Uploads: {perf['active_uploads']}")

print("\n=== HEALTH CHECKS ===")
for check in data['health_checks']:
    print(f"{check['component']}: {check['status']} - {check['message']}")

print("\n=== ACTIVE ALERTS ===")
print(f"Total: {len(data['active_alerts'])}")
for alert in data['active_alerts'][:3]:
    print(f"  - {alert['name']} ({alert['severity']})")
