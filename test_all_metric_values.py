#!/usr/bin/env python3
import requests
import json

# All metrics including new ones
metrics = [
    'cpu_usage', 'memory_usage', 'disk_usage', 'network_bandwidth',
    'upload_speed', 'download_speed', 'active_connections',
    'queue_size', 'error_rate', 'success_rate', 
    'throughput', 'latency', 'cache_hit_rate'
]

print("=== Testing All Metric Values ===")
for metric in metrics:
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/monitoring/metrics/{metric}/values",
            params={"interval_seconds": 300, "limit": 10}
        )
        if response.status_code == 200:
            data = response.json()
            metadata = data['metadata']
            values = data['values']
            print(f"\n{metric}:")
            print(f"  Type: {metadata['metric_type']}, Unit: {metadata['unit']}")
            print(f"  Source: {metadata['source']}")
            if values:
                print(f"  Current: {values[-1]['value']} {metadata['unit']}")
            else:
                print(f"  No values available")
            if 'summary' in metadata:
                print(f"  Summary: min={metadata['summary']['min']}, max={metadata['summary']['max']}, avg={metadata['summary']['avg']}")
        else:
            print(f"\n{metric}: ERROR - {response.status_code}")
            print(f"  {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"\n{metric}: EXCEPTION - {e}")
