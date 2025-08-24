#!/usr/bin/env python3
"""
Test all new endpoints added to the API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test an endpoint and return result"""
    try:
        headers = {"Content-Type": "application/json"}
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return False, "Unknown method"
        
        success = response.status_code in [200, 201, 404]
        return success, response.json() if response.text else {}
    except Exception as e:
        return False, str(e)

def test_new_endpoints():
    """Test all newly added endpoints"""
    print("="*60)
    print("🧪 TESTING NEW ENDPOINTS")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {"passed": 0, "failed": 0}
    
    # Test Authentication
    print("\n📂 AUTHENTICATION")
    print("-"*40)
    
    # Login
    success, data = test_endpoint("POST", "/api/v1/auth/login", 
                                  {"username": "admin", "password": "admin123"})
    token = data.get("token") if success else None
    print(f"{'✅' if success else '❌'} POST /api/v1/auth/login - {data}")
    results["passed" if success else "failed"] += 1
    
    # Refresh token
    if token:
        success, data = test_endpoint("POST", "/api/v1/auth/refresh", {"token": token})
        new_token = data.get("token") if success else token
        print(f"{'✅' if success else '❌'} POST /api/v1/auth/refresh - {data}")
        results["passed" if success else "failed"] += 1
    
    # Get permissions
    success, data = test_endpoint("GET", f"/api/v1/auth/permissions?token={token}")
    print(f"{'✅' if success else '❌'} GET /api/v1/auth/permissions - {data}")
    results["passed" if success else "failed"] += 1
    
    # Logout
    if token:
        success, data = test_endpoint("POST", "/api/v1/auth/logout", {"token": token})
        print(f"{'✅' if success else '❌'} POST /api/v1/auth/logout - {data}")
        results["passed" if success else "failed"] += 1
    
    # Test User Management
    print("\n📂 USER MANAGEMENT")
    print("-"*40)
    
    # Create user
    success, data = test_endpoint("POST", "/api/v1/users", 
                                  {"username": "newuser", "password": "pass123", "email": "test@example.com"})
    user_id = data.get("user_id") if success else "test_id"
    print(f"{'✅' if success else '❌'} POST /api/v1/users - {data}")
    results["passed" if success else "failed"] += 1
    
    # Get user
    success, data = test_endpoint("GET", f"/api/v1/users/{user_id}")
    print(f"{'✅' if success else '❌'} GET /api/v1/users/{user_id} - {data}")
    results["passed" if success else "failed"] += 1
    
    # Update user
    success, data = test_endpoint("PUT", f"/api/v1/users/{user_id}", 
                                  {"email": "updated@example.com"})
    print(f"{'✅' if success else '❌'} PUT /api/v1/users/{user_id} - {data}")
    results["passed" if success else "failed"] += 1
    
    # Delete user
    success, data = test_endpoint("DELETE", f"/api/v1/users/{user_id}")
    print(f"{'✅' if success else '❌'} DELETE /api/v1/users/{user_id} - {data}")
    results["passed" if success else "failed"] += 1
    
    # Test Batch Operations
    print("\n📂 BATCH OPERATIONS")
    print("-"*40)
    
    # Batch add folders
    success, data = test_endpoint("POST", "/api/v1/batch/folders", 
                                  {"paths": ["/tmp/folder1", "/tmp/folder2", "/tmp/folder3"]})
    print(f"{'✅' if success else '❌'} POST /api/v1/batch/folders - Added {data.get('added', 0)} folders")
    results["passed" if success else "failed"] += 1
    
    # Batch create shares
    success, data = test_endpoint("POST", "/api/v1/batch/shares", 
                                  {"folder_ids": ["folder1", "folder2"], "access_level": "public"})
    print(f"{'✅' if success else '❌'} POST /api/v1/batch/shares - Created {data.get('created', 0)} shares")
    results["passed" if success else "failed"] += 1
    
    # Batch delete files
    success, data = test_endpoint("DELETE", "/api/v1/batch/files", 
                                  {"file_ids": ["file1", "file2", "file3", "file4", "file5"]})
    print(f"{'✅' if success else '❌'} DELETE /api/v1/batch/files - Deleted {data.get('total_deleted', 0)} files")
    results["passed" if success else "failed"] += 1
    
    # Test Webhooks
    print("\n📂 WEBHOOKS")
    print("-"*40)
    
    # Create webhook
    success, data = test_endpoint("POST", "/api/v1/webhooks", 
                                  {"url": "https://example.com/webhook", "events": ["upload", "download"]})
    webhook_id = data.get("webhook_id") if success else "test_webhook"
    print(f"{'✅' if success else '❌'} POST /api/v1/webhooks - {data}")
    results["passed" if success else "failed"] += 1
    
    # List webhooks
    success, data = test_endpoint("GET", "/api/v1/webhooks")
    print(f"{'✅' if success else '❌'} GET /api/v1/webhooks - Found {data.get('total', 0)} webhooks")
    results["passed" if success else "failed"] += 1
    
    # Delete webhook
    success, data = test_endpoint("DELETE", f"/api/v1/webhooks/{webhook_id}")
    print(f"{'✅' if success else '❌'} DELETE /api/v1/webhooks/{webhook_id} - {data}")
    results["passed" if success else "failed"] += 1
    
    # Test Rate Limiting
    print("\n📂 RATE LIMITING")
    print("-"*40)
    
    # Get rate limit status
    success, data = test_endpoint("GET", "/api/v1/rate_limit/status")
    print(f"{'✅' if success else '❌'} GET /api/v1/rate_limit/status - Remaining: {data.get('remaining', 0)}/{data.get('limit', 0)}")
    results["passed" if success else "failed"] += 1
    
    # Get quotas
    success, data = test_endpoint("GET", "/api/v1/rate_limit/quotas")
    print(f"{'✅' if success else '❌'} GET /api/v1/rate_limit/quotas - Tier: {data.get('tier', 'unknown')}")
    results["passed" if success else "failed"] += 1
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    total = results["passed"] + results["failed"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    print(f"Total Tests: {total}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    print("="*60)
    
    return results

if __name__ == "__main__":
    test_new_endpoints()