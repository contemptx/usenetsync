#!/usr/bin/env python3
import requests
import json

# Test the metrics endpoint multiple times to see variability
print("=== Testing Metrics Variability ===")
for i in range(3):
    response = requests.get("http://localhost:8000/api/v1/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print(f"Test {i+1}:")
        print(f"  CPU: {metrics['system']['cpu']['percent']}%")
        print(f"  Memory: {metrics['system']['memory']['percent']}%")
        print(f"  Process Memory: {metrics['process']['memory_mb']:.1f} MB")
        print(f"  Process CPU: {metrics['process']['cpu_percent']}%")
    else:
        print(f"Test {i+1}: Error - {response.status_code}")
    
    import time
    time.sleep(1)

# Verify all metrics are numeric
print("\n=== Verifying Data Types ===")
response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

def check_numeric(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            check_numeric(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            check_numeric(item, f"{path}[{i}]")
    elif obj is not None and path != "timestamp":
        if not isinstance(obj, (int, float, bool)):
            print(f"Non-numeric value at {path}: {type(obj).__name__} = {obj}")

check_numeric(metrics)
print("Data type check complete")
