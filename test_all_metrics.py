#!/usr/bin/env python3
import requests
import json

metrics = [
    'cpu_usage', 'memory_usage', 'disk_usage', 'network_bandwidth',
    'upload_speed', 'download_speed', 'active_connections',
    'queue_size', 'error_rate', 'success_rate'
]

print("=== Testing All Metrics ===")
for metric in metrics:
    response = requests.get(f"http://localhost:8000/api/v1/monitoring/metrics/{metric}/stats?period_hours=12")
    if response.status_code == 200:
        data = response.json()
        print(f"\n{metric}:")
        print(f"  Current: {data['current_value']} {data['unit']}")
        print(f"  Stats: min={data['statistics']['min']}, max={data['statistics']['max']}, avg={data['statistics']['average']}")
        print(f"  Trend: {data['trend']}")
        print(f"  Data points: {data['statistics']['data_points']}")
    else:
        print(f"\n{metric}: ERROR - {response.status_code}")
