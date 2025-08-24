#!/usr/bin/env python3
import time
import threading

def cpu_stress():
    """Generate CPU load"""
    end_time = time.time() + 2  # Run for 2 seconds
    while time.time() < end_time:
        _ = sum(i*i for i in range(10000))

def memory_stress():
    """Allocate some memory"""
    data = []
    for _ in range(5):
        data.append([0] * 1000000)  # Allocate ~40MB
    time.sleep(2)

# Run stress in threads
cpu_thread = threading.Thread(target=cpu_stress)
memory_thread = threading.Thread(target=memory_stress)

print("Starting stress test...")
cpu_thread.start()
memory_thread.start()

# Wait a moment then check metrics
time.sleep(1)
import requests
response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()

print(f"CPU Usage: {metrics['system']['cpu']['percent']}%")
print(f"Memory Used: {metrics['system']['memory']['used_mb']:.1f} MB")
print(f"Process Memory: {metrics['process']['memory_mb']:.1f} MB")
print(f"Process CPU: {metrics['process']['cpu_percent']}%")

cpu_thread.join()
memory_thread.join()
print("Stress test completed")
