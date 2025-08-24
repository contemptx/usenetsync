#!/usr/bin/env python3
import requests
import json
import time

# Make multiple calls to see bandwidth changes
print("=== BANDWIDTH MONITORING TEST ===\n")

for i in range(3):
    response = requests.get("http://localhost:8000/api/v1/network/bandwidth/current")
    data = response.json()
    
    print(f"Call #{i+1}:")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"  Current bandwidth:")
    print(f"    Upload: {data['current']['upload_mbps']} Mbps")
    print(f"    Download: {data['current']['download_mbps']} Mbps")
    print(f"    Total: {data['current']['total_mbps']} Mbps")
    print(f"  Active transfers:")
    print(f"    Uploads: {data['active_transfers']['uploads']}")
    print(f"    Downloads: {data['active_transfers']['downloads']}")
    print(f"  Cumulative stats:")
    print(f"    Bytes sent: {data['cumulative']['bytes_sent']:,}")
    print(f"    Bytes received: {data['cumulative']['bytes_recv']:,}")
    print(f"    Packet errors: in={data['cumulative']['errors_in']}, out={data['cumulative']['errors_out']}")
    print(f"  Network interfaces: {len(data['network_interfaces'])}")
    for iface in data['network_interfaces']:
        print(f"    - {iface['name']}: {iface.get('ipv4_addresses', ['N/A'])[0] if iface.get('ipv4_addresses') else 'N/A'} (MTU: {iface['mtu']})")
    if 'measurement_period_seconds' in data:
        print(f"  Measurement period: {data['measurement_period_seconds']} seconds")
    print()
    
    if i < 2:
        time.sleep(2)
