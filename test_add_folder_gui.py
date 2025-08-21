#!/usr/bin/env python3
import requests
import json
import os

# Create a test folder
test_folder = "/workspace/test_data"
os.makedirs(test_folder, exist_ok=True)

# Create some test files
for i in range(3):
    with open(f"{test_folder}/file_{i}.txt", "w") as f:
        f.write(f"Test content for file {i}\n" * 100)

# Add folder via API
url = "http://localhost:8000/api/v1/add_folder"
data = {
    "path": test_folder,
    "name": "Test Data Folder"
}

response = requests.post(url, json=data)
print(f"Add folder response: {response.status_code}")
if response.ok:
    result = response.json()
    print(f"Folder added: {json.dumps(result, indent=2)}")
    folder_id = result.get('folder_id')
    
    # Now index the folder
    if folder_id:
        index_url = "http://localhost:8000/api/v1/index_folder"
        index_data = {"folderId": folder_id}
        index_response = requests.post(index_url, json=index_data)
        print(f"\nIndex response: {index_response.status_code}")
        if index_response.ok:
            print(f"Indexed: {json.dumps(index_response.json(), indent=2)}")
else:
    print(f"Error: {response.text}")