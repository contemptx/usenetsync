#!/usr/bin/env python3
import requests
import json

# Test the dashboard
response = requests.get("http://localhost:8000/api/v1/monitoring/dashboard")
data = response.json()

print("=== System Health Summary ===")
print(f"Overall Health: {data['overall_health']}")
print(f"Health Issues: {data['health_issues']}")

print("\n=== System Metrics ===")
for metric, values in data['system_metrics'].items():
    print(f"{metric.upper()}:")
    print(f"  Status: {values['status']}")
    if metric == 'cpu':
        print(f"  Usage: {values['percent']}% ({values['cores']} cores)")
    elif metric == 'memory':
        print(f"  Usage: {values['percent']}% ({values['used_gb']}/{values['total_gb']} GB)")
    elif metric == 'disk':
        print(f"  Usage: {values['percent']}% ({values['used_gb']}/{values['total_gb']} GB)")
        print(f"  Free: {values['free_gb']} GB")

print("\n=== Database Statistics ===")
print(f"Connected: {data['database']['connected']}")
print(f"Total Records: {data['database']['total_records']}")
for table, count in data['database']['statistics'].items():
    if count > 0:
        print(f"  {table}: {count}")

print("\n=== Operations Today ===")
print("Uploads:")
for key, value in data['operations']['uploads'].items():
    print(f"  {key}: {value}")
print("Downloads:")
for key, value in data['operations']['downloads'].items():
    print(f"  {key}: {value}")

print("\n=== Network Status ===")
print(f"Servers: {data['network']['servers']['healthy']}/{data['network']['servers']['total']} healthy")
print(f"Bandwidth: {data['network']['bandwidth']['current_mbps']} Mbps current")

print("\n=== Uptime ===")
print(f"Duration: {data['uptime']['duration_hours']} hours")
