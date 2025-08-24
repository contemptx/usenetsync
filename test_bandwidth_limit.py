#!/usr/bin/env python3
import sys
sys.path.insert(0, '/workspace/backend/src')

from unified.networking.bandwidth import UnifiedBandwidth
import time

# Create bandwidth controller with 10 Mbps limit
controller = UnifiedBandwidth(max_rate_mbps=10.0)

print(f"Max rate: {controller.max_rate_mbps} Mbps")
print(f"Max bytes/sec: {controller.max_rate_bytes}")

# Simulate sending data
data_sizes = [1024 * 100, 1024 * 500, 1024 * 1024]  # 100KB, 500KB, 1MB
for size in data_sizes:
    start = time.time()
    controller.throttle(size)
    elapsed = time.time() - start
    print(f"Sent {size/1024:.0f} KB - throttled for {elapsed:.3f} seconds")
    print(f"Current rate: {controller.get_current_rate():.2f} Mbps")
    time.sleep(0.5)
