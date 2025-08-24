#!/usr/bin/env python3
"""
Comprehensive test suite for ALL 148 UsenetSync API endpoints
Tests every single endpoint for basic functionality
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# All 148 endpoints from server.py
ALL_ENDPOINTS = [
    ("DELETE", "/api/v1/backup/{backup_id}", "Delete backup"),
    ("DELETE", "/api/v1/batch/files", "Batch delete files"),
    ("DELETE", "/api/v1/folders/{folder_id}", "Delete folder"),
    ("DELETE", "/api/v1/monitoring/alerts/{alert_id}", "Delete alert"),
    ("DELETE", "/api/v1/network/servers/{server_id}", "Delete server"),
    ("DELETE", "/api/v1/upload/queue/{queue_id}", "Delete upload queue item"),
    ("DELETE", "/api/v1/users/{user_id}", "Delete user"),
    ("DELETE", "/api/v1/webhooks/{webhook_id}", "Delete webhook"),
    ("GET", "/", "Root endpoint"),
    ("GET", "/api/v1/auth/permissions", "Get auth permissions"),
    ("GET", "/api/v1/backup/{backup_id}/metadata", "Get backup metadata"),
    ("GET", "/api/v1/backup/list", "List backups"),
    ("GET", "/api/v1/database/status", "Database status"),
    ("GET", "/api/v1/download/cache/stats", "Download cache stats"),
    ("GET", "/api/v1/download/progress/{download_id}", "Download progress"),
    ("GET", "/api/v1/events/transfers", "Transfer events"),
    ("GET", "/api/v1/folders", "List folders"),
    ("GET", "/api/v1/folders/{folder_id}", "Get folder"),
    ("GET", "/api/v1/indexing/stats", "Indexing stats"),
    ("GET", "/api/v1/indexing/version/{file_hash}", "File version"),
    ("GET", "/api/v1/license/status", "License status"),
    ("GET", "/api/v1/logs", "Get logs"),
    ("GET", "/api/v1/metrics", "System metrics"),
    ("GET", "/api/v1/migration/status", "Migration status"),
    ("GET", "/api/v1/monitoring/alerts/list", "List alerts"),
    ("GET", "/api/v1/monitoring/dashboard", "Monitoring dashboard"),
    ("GET", "/api/v1/monitoring/metrics/{metric_name}/stats", "Metric stats"),
    ("GET", "/api/v1/monitoring/metrics/{metric_name}/values", "Metric values"),
    ("GET", "/api/v1/monitoring/system_status", "System status"),
    ("GET", "/api/v1/network/bandwidth/current", "Current bandwidth"),
    ("GET", "/api/v1/network/connection_pool", "Connection pool"),
    ("GET", "/api/v1/network/connection_pool/stats", "Connection pool stats"),
    ("GET", "/api/v1/network/servers/list", "List servers"),
    ("GET", "/api/v1/network/servers/{server_id}/health", "Server health"),
    ("GET", "/api/v1/progress", "All progress"),
    ("GET", "/api/v1/progress/{progress_id}", "Specific progress"),
    ("GET", "/api/v1/publishing/authorized_users/list", "List authorized users"),
    ("GET", "/api/v1/publishing/commitment/list", "List commitments"),
    ("GET", "/api/v1/publishing/expiry/check", "Check expiry"),
    ("GET", "/api/v1/rate_limit/quotas", "Rate limit quotas"),
    ("GET", "/api/v1/rate_limit/status", "Rate limit status"),
    ("GET", "/api/v1/search", "Search"),
    ("GET", "/api/v1/security/check_access", "Check access"),
    ("GET", "/api/v1/segmentation/info/{file_hash}", "Segmentation info"),
    ("GET", "/api/v1/shares", "List shares"),
    ("GET", "/api/v1/shares/{share_id}", "Get share"),
    ("GET", "/api/v1/stats", "Statistics"),
    ("GET", "/api/v1/upload/queue/{queue_id}", "Upload queue item"),
    ("GET", "/api/v1/upload/status", "Upload status"),
    ("GET", "/api/v1/upload/strategy", "Upload strategy"),
    ("GET", "/api/v1/users/{user_id}", "Get user"),
    ("GET", "/api/v1/webhooks", "List webhooks"),
    ("GET", "/health", "Health check"),
    ("POST", "/api/v1/add_folder", "Add folder"),
    ("POST", "/api/v1/auth/login", "Login"),
    ("POST", "/api/v1/auth/logout", "Logout"),
    ("POST", "/api/v1/auth/refresh", "Refresh token"),
    ("POST", "/api/v1/backup/create", "Create backup"),
    ("POST", "/api/v1/backup/export", "Export backup"),
    ("POST", "/api/v1/backup/import", "Import backup"),
    ("POST", "/api/v1/backup/restore", "Restore backup"),
    ("POST", "/api/v1/backup/schedule", "Schedule backup"),
    ("POST", "/api/v1/backup/verify", "Verify backup"),
    ("POST", "/api/v1/batch/folders", "Batch add folders"),
    ("POST", "/api/v1/batch/shares", "Batch create shares"),
    ("POST", "/api/v1/create_share", "Create share"),
    ("POST", "/api/v1/download/batch", "Batch download"),
    ("POST", "/api/v1/download/cache/clear", "Clear cache"),
    ("POST", "/api/v1/download/cache/optimize", "Optimize cache"),
    ("POST", "/api/v1/download/cancel", "Cancel download"),
    ("POST", "/api/v1/download/pause", "Pause download"),
    ("POST", "/api/v1/download/reconstruct", "Reconstruct file"),
    ("POST", "/api/v1/download/resume", "Resume download"),
    ("POST", "/api/v1/download_share", "Download share"),
    ("POST", "/api/v1/download/start", "Start download"),
    ("POST", "/api/v1/download/streaming/start", "Start streaming"),
    ("POST", "/api/v1/download/verify", "Verify download"),
    ("POST", "/api/v1/folder_info", "Folder info"),
    ("POST", "/api/v1/folders/index", "Index folder"),
    ("POST", "/api/v1/get_logs", "Get logs"),
    ("POST", "/api/v1/get_user_info", "Get user info"),
    ("POST", "/api/v1/index_folder", "Index folder"),
    ("POST", "/api/v1/indexing/binary", "Binary index"),
    ("POST", "/api/v1/indexing/deduplicate", "Deduplicate"),
    ("POST", "/api/v1/indexing/rebuild", "Rebuild index"),
    ("POST", "/api/v1/indexing/sync", "Sync index"),
    ("POST", "/api/v1/indexing/verify", "Verify index"),
    ("POST", "/api/v1/initialize_user", "Initialize user"),
    ("POST", "/api/v1/is_user_initialized", "Check user initialized"),
    ("POST", "/api/v1/migration/backup_old", "Backup old"),
    ("POST", "/api/v1/migration/rollback", "Rollback migration"),
    ("POST", "/api/v1/migration/start", "Start migration"),
    ("POST", "/api/v1/migration/verify", "Verify migration"),
    ("POST", "/api/v1/monitoring/alerts/add", "Add alert"),
    ("POST", "/api/v1/monitoring/export", "Export monitoring"),
    ("POST", "/api/v1/monitoring/record_error", "Record error"),
    ("POST", "/api/v1/monitoring/record_metric", "Record metric"),
    ("POST", "/api/v1/monitoring/record_operation", "Record operation"),
    ("POST", "/api/v1/monitoring/record_throughput", "Record throughput"),
    ("POST", "/api/v1/network/bandwidth/limit", "Set bandwidth limit"),
    ("POST", "/api/v1/network/retry/configure", "Configure retry"),
    ("POST", "/api/v1/network/servers/add", "Add server"),
    ("POST", "/api/v1/network/servers/{server_id}/test", "Test server"),
    ("POST", "/api/v1/process_folder", "Process folder"),
    ("POST", "/api/v1/publishing/authorized_users/add", "Add authorized user"),
    ("POST", "/api/v1/publishing/authorized_users/remove", "Remove authorized user"),
    ("POST", "/api/v1/publishing/commitment/add", "Add commitment"),
    ("POST", "/api/v1/publishing/commitment/remove", "Remove commitment"),
    ("POST", "/api/v1/publishing/expiry/set", "Set expiry"),
    ("POST", "/api/v1/publishing/publish", "Publish"),
    ("POST", "/api/v1/publishing/unpublish", "Unpublish"),
    ("POST", "/api/v1/save_server_config", "Save server config"),
    ("POST", "/api/v1/security/decrypt_file", "Decrypt file"),
    ("POST", "/api/v1/security/encrypt_file", "Encrypt file"),
    ("POST", "/api/v1/security/generate_api_key", "Generate API key"),
    ("POST", "/api/v1/security/generate_folder_key", "Generate folder key"),
    ("POST", "/api/v1/security/generate_user_keys", "Generate user keys"),
    ("POST", "/api/v1/security/grant_access", "Grant access"),
    ("POST", "/api/v1/security/hash_password", "Hash password"),
    ("POST", "/api/v1/security/revoke_access", "Revoke access"),
    ("POST", "/api/v1/security/sanitize_path", "Sanitize path"),
    ("POST", "/api/v1/security/session/create", "Create session"),
    ("POST", "/api/v1/security/session/verify", "Verify session"),
    ("POST", "/api/v1/security/verify_api_key", "Verify API key"),
    ("POST", "/api/v1/security/verify_password", "Verify password"),
    ("POST", "/api/v1/segmentation/hash/calculate", "Calculate hash"),
    ("POST", "/api/v1/segmentation/headers/generate", "Generate headers"),
    ("POST", "/api/v1/segmentation/pack", "Pack segments"),
    ("POST", "/api/v1/segmentation/redundancy/add", "Add redundancy"),
    ("POST", "/api/v1/segmentation/redundancy/verify", "Verify redundancy"),
    ("POST", "/api/v1/segmentation/unpack", "Unpack segments"),
    ("POST", "/api/v1/shares", "Create share"),
    ("POST", "/api/v1/shares/{share_id}/verify", "Verify share"),
    ("POST", "/api/v1/test_server_connection", "Test server connection"),
    ("POST", "/api/v1/upload/batch", "Batch upload"),
    ("POST", "/api/v1/upload_folder", "Upload folder"),
    ("POST", "/api/v1/upload/queue", "Queue upload"),
    ("POST", "/api/v1/upload/queue/pause", "Pause queue"),
    ("POST", "/api/v1/upload/queue/resume", "Resume queue"),
    ("POST", "/api/v1/upload/session/create", "Create session"),
    ("POST", "/api/v1/upload/session/{session_id}/end", "End session"),
    ("POST", "/api/v1/upload/worker/add", "Add worker"),
    ("POST", "/api/v1/upload/worker/{worker_id}/stop", "Stop worker"),
    ("POST", "/api/v1/users", "Create user"),
    ("POST", "/api/v1/webhooks", "Create webhook"),
    ("PUT", "/api/v1/publishing/update", "Update publishing"),
    ("PUT", "/api/v1/upload/queue/{queue_id}/priority", "Update priority"),
    ("PUT", "/api/v1/users/{user_id}", "Update user"),
]

def get_test_data(method: str, endpoint: str) -> dict:
    """Get appropriate test data for endpoint"""
    # Basic test data for different endpoint types
    if "folder" in endpoint.lower():
        return {"path": "/tmp/test", "folder_id": "test_folder_123"}
    elif "user" in endpoint.lower():
        return {"username": "testuser", "email": "test@example.com", "user_id": "test_user_123"}
    elif "share" in endpoint.lower():
        return {"folder_id": "test_folder", "share_id": "test_share_123", "share_type": "public"}
    elif "backup" in endpoint.lower():
        return {"backup_id": "test_backup_123", "backup_dir": "/tmp/backup"}
    elif "metric" in endpoint.lower():
        return {"name": "test_metric", "value": 100}
    elif "server" in endpoint.lower():
        return {"server_id": "test_server", "host": "news.example.com", "port": 563}
    elif "webhook" in endpoint.lower():
        return {"webhook_id": "test_webhook", "url": "http://example.com/webhook"}
    elif "auth" in endpoint.lower() or "login" in endpoint:
        return {"username": "testuser", "password": "testpass123"}
    elif "password" in endpoint:
        return {"password": "testpass123", "salt": "testsalt"}
    elif "file" in endpoint.lower():
        return {"file_path": "/tmp/test.txt", "file_hash": "testhash123"}
    elif "download" in endpoint.lower() or "upload" in endpoint.lower():
        return {"share_id": "test_share", "queue_id": "test_queue", "download_id": "test_download"}
    elif "session" in endpoint:
        return {"user_id": "test_user", "session_token": "test_token"}
    elif "segment" in endpoint.lower():
        return {"file_hash": "test_hash", "segments": [], "file_paths": ["/tmp/test.txt"]}
    else:
        return {}

def test_endpoint(method: str, endpoint: str, description: str) -> Tuple[bool, str]:
    """Test a single endpoint"""
    # Replace path parameters with test values
    test_endpoint = endpoint
    test_endpoint = test_endpoint.replace("{backup_id}", "test_backup")
    test_endpoint = test_endpoint.replace("{folder_id}", "test_folder")
    test_endpoint = test_endpoint.replace("{alert_id}", "test_alert")
    test_endpoint = test_endpoint.replace("{server_id}", "test_server")
    test_endpoint = test_endpoint.replace("{queue_id}", "test_queue")
    test_endpoint = test_endpoint.replace("{user_id}", "test_user")
    test_endpoint = test_endpoint.replace("{webhook_id}", "test_webhook")
    test_endpoint = test_endpoint.replace("{download_id}", "test_download")
    test_endpoint = test_endpoint.replace("{file_hash}", "test_hash")
    test_endpoint = test_endpoint.replace("{progress_id}", "test_progress")
    test_endpoint = test_endpoint.replace("{metric_name}", "test_metric")
    test_endpoint = test_endpoint.replace("{share_id}", "test_share")
    test_endpoint = test_endpoint.replace("{session_id}", "test_session")
    test_endpoint = test_endpoint.replace("{worker_id}", "test_worker")
    
    url = f"{BASE_URL}{test_endpoint}"
    
    try:
        if method == "GET":
            # Add query params for search endpoint
            if "search" in endpoint:
                url += "?query=test"
            response = requests.get(url, headers=HEADERS, timeout=5)
        elif method == "POST":
            data = get_test_data(method, endpoint)
            response = requests.post(url, json=data, headers=HEADERS, timeout=5)
        elif method == "PUT":
            data = get_test_data(method, endpoint)
            response = requests.put(url, json=data, headers=HEADERS, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=5)
        else:
            return False, f"Unknown method: {method}"
        
        # Check if response is successful (2xx or specific expected codes)
        if response.status_code >= 200 and response.status_code < 300:
            return True, f"✅ {response.status_code}"
        elif response.status_code == 404 and method == "GET" and "{" in endpoint:
            # 404 is acceptable for GET with path params (item not found)
            return True, f"✅ {response.status_code} (Not found - OK)"
        elif response.status_code == 400:
            # Bad request - likely missing required params
            return False, f"❌ 400 Bad Request"
        elif response.status_code == 500:
            # Server error
            return False, f"❌ 500 Server Error"
        elif response.status_code == 503:
            # Service unavailable
            return False, f"❌ 503 Service Unavailable"
        else:
            return False, f"❌ {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "❌ Timeout"
    except requests.exceptions.ConnectionError:
        return False, "❌ Connection Error"
    except Exception as e:
        return False, f"❌ {str(e)}"

def main():
    """Run comprehensive endpoint tests"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE API TEST - ALL 148 ENDPOINTS")
    print("=" * 80)
    print(f"Testing: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)
    
    results = {
        "passed": [],
        "failed": [],
        "total": len(ALL_ENDPOINTS)
    }
    
    # Group endpoints by category for organized output
    categories = {}
    for method, endpoint, desc in ALL_ENDPOINTS:
        # Determine category
        if "/auth/" in endpoint:
            category = "Authentication"
        elif "/security/" in endpoint:
            category = "Security"
        elif "/backup/" in endpoint:
            category = "Backup"
        elif "/monitoring/" in endpoint or "/metrics" in endpoint:
            category = "Monitoring"
        elif "/migration/" in endpoint:
            category = "Migration"
        elif "/publishing/" in endpoint:
            category = "Publishing"
        elif "/indexing/" in endpoint or "index" in endpoint:
            category = "Indexing"
        elif "/upload/" in endpoint or "upload" in endpoint:
            category = "Upload"
        elif "/download/" in endpoint or "download" in endpoint:
            category = "Download"
        elif "/network/" in endpoint:
            category = "Network"
        elif "/segmentation/" in endpoint:
            category = "Segmentation"
        elif "/folder" in endpoint:
            category = "Folders"
        elif "/share" in endpoint:
            category = "Shares"
        elif "/user" in endpoint:
            category = "Users"
        elif "/batch/" in endpoint:
            category = "Batch"
        elif "/webhook" in endpoint:
            category = "Webhooks"
        elif "/rate_limit/" in endpoint:
            category = "Rate Limiting"
        else:
            category = "System"
        
        if category not in categories:
            categories[category] = []
        categories[category].append((method, endpoint, desc))
    
    # Test each category
    for category in sorted(categories.keys()):
        print(f"\n📁 Testing {category} Endpoints")
        print("-" * 40)
        
        for method, endpoint, desc in categories[category]:
            success, message = test_endpoint(method, endpoint, desc)
            
            result = {
                "method": method,
                "endpoint": endpoint,
                "description": desc,
                "status": message
            }
            
            if success:
                results["passed"].append(result)
                print(f"{message} {method:6} {endpoint:50} - {desc}")
            else:
                results["failed"].append(result)
                print(f"{message} {method:6} {endpoint:50} - {desc}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (len(results["passed"]) / results["total"]) * 100
    
    print(f"\n✅ Passed: {len(results['passed'])}/{results['total']}")
    print(f"❌ Failed: {len(results['failed'])}/{results['total']}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if results["failed"]:
        print("\n❌ Failed Endpoints:")
        for item in results["failed"]:
            print(f"  - {item['method']} {item['endpoint']}: {item['status']}")
    
    # Save detailed report
    report_file = f"endpoint_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Exit with appropriate code
    if success_rate == 100:
        print("\n🎉 PERFECT! All endpoints working!")
        sys.exit(0)
    elif success_rate >= 90:
        print("\n✅ Good! Most endpoints working.")
        sys.exit(0)
    elif success_rate >= 70:
        print("\n⚠️ Needs improvement. Many endpoints failing.")
        sys.exit(1)
    else:
        print("\n❌ Critical! Most endpoints failing.")
        sys.exit(1)

if __name__ == "__main__":
    main()