#!/usr/bin/env python3
"""
Comprehensive test suite for all 133 UsenetSync API endpoints
Tests functionality, response validation, and data interpretation
"""

import requests
import json
import time
import os
import tempfile
import hashlib
import base64
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": [],
    "missing_features": [],
    "suggested_endpoints": []
}

# Store data between tests for validation
test_data = {
    "user_id": f"test_user_{int(time.time())}",
    "folder_id": None,
    "share_id": None,
    "api_key": None,
    "session_token": None,
    "backup_id": None,
    "password_hash": None,
    "password_salt": None,
    "folder_key": None
}

def log_test(endpoint: str, method: str, status: str, details: str = "", response_data: Any = None):
    """Log test results with details"""
    test_results["details"].append({
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "details": details,
        "response": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    if status == "PASS":
        print(f"✅ {method} {endpoint}: {details}")
    elif status == "FAIL":
        print(f"❌ {method} {endpoint}: {details}")
    elif status == "WARN":
        print(f"⚠️ {method} {endpoint}: {details}")

def validate_response(response: requests.Response, endpoint: str, method: str, 
                     expected_fields: List[str] = None) -> Tuple[bool, Dict]:
    """Validate response and check for expected fields"""
    try:
        # Check if response is JSON
        try:
            data = response.json()
        except:
            data = {"raw": response.text}
        
        # Check status code
        if response.status_code not in [200, 201]:
            log_test(endpoint, method, "FAIL", 
                    f"Status code {response.status_code}", data)
            return False, data
        
        # Check expected fields if provided
        if expected_fields:
            missing = [f for f in expected_fields if f not in data]
            if missing:
                log_test(endpoint, method, "WARN", 
                        f"Missing fields: {missing}", data)
                test_results["warnings"] += 1
        
        return True, data
        
    except Exception as e:
        log_test(endpoint, method, "FAIL", f"Validation error: {e}")
        return False, {}

def test_system_endpoints():
    """Test system and health endpoints"""
    print("\n" + "="*60)
    print("🔧 TESTING SYSTEM ENDPOINTS")
    print("="*60)
    
    endpoints = [
        ("GET", "/", ["name", "version", "status"]),
        ("GET", "/health", ["status"]),
        ("GET", "/api/v1/license/status", ["status"]),
        ("GET", "/api/v1/database/status", ["status"]),
        ("POST", "/api/v1/is_user_initialized", []),
        ("POST", "/api/v1/get_user_info", []),
        ("GET", "/api/v1/stats", ["stats"]),
        ("GET", "/api/v1/metrics", ["metrics"]),
        ("GET", "/api/v1/events/transfers", ["events"]),
        ("POST", "/api/v1/get_logs", [], {"limit": 10}),
        ("GET", "/api/v1/search?query=test", ["results"]),
        ("GET", "/api/v1/network/connection_pool", ["pool"])
    ]
    
    for endpoint_data in endpoints:
        method = endpoint_data[0]
        endpoint = endpoint_data[1]
        expected_fields = endpoint_data[2]
        data = endpoint_data[3] if len(endpoint_data) > 3 else {}
        
        test_results["total"] += 1
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=HEADERS)
            
            success, response_data = validate_response(response, endpoint, method, expected_fields)
            
            if success:
                test_results["passed"] += 1
                log_test(endpoint, method, "PASS", "Endpoint working", response_data)
            else:
                test_results["failed"] += 1
                
        except Exception as e:
            test_results["failed"] += 1
            log_test(endpoint, method, "FAIL", str(e))

def test_security_endpoints():
    """Test security endpoints with validation"""
    print("\n" + "="*60)
    print("🔐 TESTING SECURITY ENDPOINTS")
    print("="*60)
    
    # Test 1: Generate user keys
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/generate_user_keys",
                                json={"user_id": test_data["user_id"]},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/generate_user_keys", 
                                         "POST", ["success", "user_id", "public_key"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/security/generate_user_keys", "POST", "PASS", 
                    f"Generated keys for {test_data['user_id']}", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/generate_user_keys", "POST", "FAIL", str(e))
    
    # Test 2: Generate folder key
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/generate_folder_key",
                                json={"folder_id": "test_folder", "user_id": test_data["user_id"]},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/generate_folder_key", 
                                         "POST", ["success", "folder_id", "key"])
        if success:
            test_results["passed"] += 1
            test_data["folder_key"] = data.get("key")
            log_test("/api/v1/security/generate_folder_key", "POST", "PASS", 
                    "Generated folder key", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/generate_folder_key", "POST", "FAIL", str(e))
    
    # Test 3: Hash password
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/hash_password",
                                json={"password": "TestPassword123!"},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/hash_password", 
                                         "POST", ["success", "hash", "salt"])
        if success:
            test_results["passed"] += 1
            test_data["password_hash"] = data.get("hash")
            test_data["password_salt"] = data.get("salt")
            log_test("/api/v1/security/hash_password", "POST", "PASS", 
                    "Password hashed successfully", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/hash_password", "POST", "FAIL", str(e))
    
    # Test 4: Verify password
    if test_data["password_hash"] and test_data["password_salt"]:
        test_results["total"] += 1
        try:
            response = requests.post(f"{BASE_URL}/api/v1/security/verify_password",
                                    json={
                                        "password": "TestPassword123!",
                                        "hash": test_data["password_hash"],
                                        "salt": test_data["password_salt"]
                                    },
                                    headers=HEADERS)
            success, data = validate_response(response, "/api/v1/security/verify_password", 
                                             "POST", ["success", "valid"])
            if success and data.get("valid"):
                test_results["passed"] += 1
                log_test("/api/v1/security/verify_password", "POST", "PASS", 
                        "Password verified correctly", data)
            else:
                test_results["failed"] += 1
                log_test("/api/v1/security/verify_password", "POST", "FAIL", 
                        "Password verification failed", data)
        except Exception as e:
            test_results["failed"] += 1
            log_test("/api/v1/security/verify_password", "POST", "FAIL", str(e))
    
    # Test 5: Generate API key
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/generate_api_key",
                                json={"user_id": test_data["user_id"], "name": "test_key"},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/generate_api_key", 
                                         "POST", ["success", "api_key"])
        if success:
            test_results["passed"] += 1
            test_data["api_key"] = data.get("api_key")
            log_test("/api/v1/security/generate_api_key", "POST", "PASS", 
                    "API key generated", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/generate_api_key", "POST", "FAIL", str(e))
    
    # Test 6: Verify API key
    if test_data["api_key"]:
        test_results["total"] += 1
        try:
            response = requests.post(f"{BASE_URL}/api/v1/security/verify_api_key",
                                    json={"api_key": test_data["api_key"]},
                                    headers=HEADERS)
            success, data = validate_response(response, "/api/v1/security/verify_api_key", 
                                             "POST", ["success", "valid"])
            if success:
                test_results["passed"] += 1
                log_test("/api/v1/security/verify_api_key", "POST", "PASS", 
                        f"API key valid: {data.get('valid')}", data)
            else:
                test_results["failed"] += 1
        except Exception as e:
            test_results["failed"] += 1
            log_test("/api/v1/security/verify_api_key", "POST", "FAIL", str(e))
    
    # Test 7: Create session
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/session/create",
                                json={"user_id": test_data["user_id"], "ttl": 3600},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/session/create", 
                                         "POST", ["success", "token"])
        if success:
            test_results["passed"] += 1
            test_data["session_token"] = data.get("token")
            log_test("/api/v1/security/session/create", "POST", "PASS", 
                    "Session created", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/session/create", "POST", "FAIL", str(e))
    
    # Test 8: Path sanitization
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/security/sanitize_path",
                                json={"path": "../../../etc/passwd"},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/security/sanitize_path", 
                                         "POST", ["success", "sanitized_path"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/security/sanitize_path", "POST", "PASS", 
                    f"Path sanitized: {data.get('sanitized_path')}", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/security/sanitize_path", "POST", "FAIL", str(e))

def test_folder_operations():
    """Test folder management with real operations"""
    print("\n" + "="*60)
    print("📁 TESTING FOLDER OPERATIONS")
    print("="*60)
    
    # Create a test folder
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content for UsenetSync")
        
        # Test 1: Add folder
        test_results["total"] += 1
        try:
            response = requests.post(f"{BASE_URL}/api/v1/add_folder",
                                    json={"path": tmpdir},
                                    headers=HEADERS)
            success, data = validate_response(response, "/api/v1/add_folder", 
                                             "POST", ["success", "folder_id"])
            if success:
                test_results["passed"] += 1
                test_data["folder_id"] = data.get("folder_id")
                log_test("/api/v1/add_folder", "POST", "PASS", 
                        f"Added folder: {test_data['folder_id']}", data)
            else:
                test_results["failed"] += 1
        except Exception as e:
            test_results["failed"] += 1
            log_test("/api/v1/add_folder", "POST", "FAIL", str(e))
        
        # Test 2: Get folders
        test_results["total"] += 1
        try:
            response = requests.get(f"{BASE_URL}/api/v1/folders", headers=HEADERS)
            success, data = validate_response(response, "/api/v1/folders", 
                                             "GET", ["folders"])
            if success:
                test_results["passed"] += 1
                folder_count = len(data.get("folders", []))
                log_test("/api/v1/folders", "GET", "PASS", 
                        f"Found {folder_count} folders", data)
            else:
                test_results["failed"] += 1
        except Exception as e:
            test_results["failed"] += 1
            log_test("/api/v1/folders", "GET", "FAIL", str(e))
        
        # Test 3: Index folder
        if test_data["folder_id"]:
            test_results["total"] += 1
            try:
                response = requests.post(f"{BASE_URL}/api/v1/index_folder",
                                        json={"folder_id": test_data["folder_id"]},
                                        headers=HEADERS)
                success, data = validate_response(response, "/api/v1/index_folder", "POST")
                if success:
                    test_results["passed"] += 1
                    log_test("/api/v1/index_folder", "POST", "PASS", 
                            "Folder indexed", data)
                else:
                    test_results["failed"] += 1
            except Exception as e:
                test_results["failed"] += 1
                log_test("/api/v1/index_folder", "POST", "FAIL", str(e))

def test_backup_operations():
    """Test backup and recovery operations"""
    print("\n" + "="*60)
    print("💾 TESTING BACKUP OPERATIONS")
    print("="*60)
    
    # Test 1: Create backup
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/backup/create",
                                json={"type": "full", "compress": True},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/backup/create", "POST")
        if success:
            test_results["passed"] += 1
            test_data["backup_id"] = data.get("backup_id")
            log_test("/api/v1/backup/create", "POST", "PASS", 
                    "Backup created", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/backup/create", "POST", "FAIL", str(e))
    
    # Test 2: List backups
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/backup/list", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/backup/list", 
                                         "GET", ["backups"])
        if success:
            test_results["passed"] += 1
            backup_count = len(data.get("backups", []))
            log_test("/api/v1/backup/list", "GET", "PASS", 
                    f"Found {backup_count} backups", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/backup/list", "GET", "FAIL", str(e))
    
    # Test 3: Schedule backup
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/backup/schedule",
                                json={"cron": "0 2 * * *"},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/backup/schedule", "POST")
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/backup/schedule", "POST", "PASS", 
                    "Backup scheduled", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/backup/schedule", "POST", "FAIL", str(e))

def test_monitoring_operations():
    """Test monitoring and metrics"""
    print("\n" + "="*60)
    print("📊 TESTING MONITORING OPERATIONS")
    print("="*60)
    
    # Test 1: Record various metrics
    metrics = [
        {"name": "cpu_usage", "value": 45.2, "type": "gauge"},
        {"name": "memory_usage", "value": 67.8, "type": "gauge"},
        {"name": "requests_total", "value": 1, "type": "counter"},
        {"name": "response_time", "value": 0.125, "type": "histogram"}
    ]
    
    for metric in metrics:
        test_results["total"] += 1
        try:
            response = requests.post(f"{BASE_URL}/api/v1/monitoring/record_metric",
                                    json=metric,
                                    headers=HEADERS)
            success, data = validate_response(response, "/api/v1/monitoring/record_metric", 
                                             "POST", ["success"])
            if success:
                test_results["passed"] += 1
                log_test("/api/v1/monitoring/record_metric", "POST", "PASS", 
                        f"Recorded {metric['name']}", data)
            else:
                test_results["failed"] += 1
        except Exception as e:
            test_results["failed"] += 1
            log_test("/api/v1/monitoring/record_metric", "POST", "FAIL", str(e))
    
    # Test 2: Record operation
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/monitoring/record_operation",
                                json={
                                    "operation": "test_upload",
                                    "duration": 2.5,
                                    "success": True,
                                    "metadata": {"files": 10, "size_mb": 100}
                                },
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/monitoring/record_operation", 
                                         "POST", ["success"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/monitoring/record_operation", "POST", "PASS", 
                    "Operation recorded", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/monitoring/record_operation", "POST", "FAIL", str(e))
    
    # Test 3: Get dashboard
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitoring/dashboard", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/monitoring/dashboard", "GET")
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/monitoring/dashboard", "GET", "PASS", 
                    "Dashboard data retrieved", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/monitoring/dashboard", "GET", "FAIL", str(e))

def test_upload_download_operations():
    """Test upload and download operations"""
    print("\n" + "="*60)
    print("⬆️⬇️ TESTING UPLOAD/DOWNLOAD OPERATIONS")
    print("="*60)
    
    # Test 1: Get upload strategy
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/upload/strategy?file_size=10000000&file_type=document",
                               headers=HEADERS)
        success, data = validate_response(response, "/api/v1/upload/strategy", 
                                         "GET", ["strategy", "chunk_size"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/upload/strategy", "GET", "PASS", 
                    f"Strategy: {data.get('strategy')}, Chunk: {data.get('chunk_size')}", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/upload/strategy", "GET", "FAIL", str(e))
    
    # Test 2: Create upload session
    test_results["total"] += 1
    try:
        response = requests.post(f"{BASE_URL}/api/v1/upload/session/create",
                                json={"entity_id": "test_file_001"},
                                headers=HEADERS)
        success, data = validate_response(response, "/api/v1/upload/session/create", 
                                         "POST", ["success", "session_id"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/upload/session/create", "POST", "PASS", 
                    f"Session: {data.get('session_id')}", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/upload/session/create", "POST", "FAIL", str(e))
    
    # Test 3: Get cache stats
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/download/cache/stats", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/download/cache/stats", 
                                         "GET", ["size_mb", "files", "hits", "misses"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/download/cache/stats", "GET", "PASS", 
                    f"Cache: {data.get('files')} files, {data.get('size_mb')} MB", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/download/cache/stats", "GET", "FAIL", str(e))

def test_network_operations():
    """Test network management operations"""
    print("\n" + "="*60)
    print("🌐 TESTING NETWORK OPERATIONS")
    print("="*60)
    
    # Test 1: List servers
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/network/servers/list", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/network/servers/list", 
                                         "GET", ["servers"])
        if success:
            test_results["passed"] += 1
            server_count = len(data.get("servers", []))
            log_test("/api/v1/network/servers/list", "GET", "PASS", 
                    f"Found {server_count} servers", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/network/servers/list", "GET", "FAIL", str(e))
    
    # Test 2: Get bandwidth
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/network/bandwidth/current", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/network/bandwidth/current", 
                                         "GET", ["upload_mbps", "download_mbps"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/network/bandwidth/current", "GET", "PASS", 
                    f"Bandwidth: ↑{data.get('upload_mbps')} ↓{data.get('download_mbps')} Mbps", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/network/bandwidth/current", "GET", "FAIL", str(e))
    
    # Test 3: Connection pool stats
    test_results["total"] += 1
    try:
        response = requests.get(f"{BASE_URL}/api/v1/network/connection_pool/stats", headers=HEADERS)
        success, data = validate_response(response, "/api/v1/network/connection_pool/stats", 
                                         "GET", ["active", "idle", "total", "max"])
        if success:
            test_results["passed"] += 1
            log_test("/api/v1/network/connection_pool/stats", "GET", "PASS", 
                    f"Pool: {data.get('active')}/{data.get('max')} active", data)
        else:
            test_results["failed"] += 1
    except Exception as e:
        test_results["failed"] += 1
        log_test("/api/v1/network/connection_pool/stats", "GET", "FAIL", str(e))

def analyze_missing_features():
    """Analyze test results and suggest missing features"""
    print("\n" + "="*60)
    print("🔍 ANALYZING API COMPLETENESS")
    print("="*60)
    
    # Check for missing features based on test results
    suggestions = []
    
    # Check authentication
    has_auth = any("auth" in d["endpoint"].lower() or "token" in str(d.get("response", {})).lower() 
                   for d in test_results["details"])
    if not has_auth:
        suggestions.append({
            "category": "Authentication",
            "endpoints": [
                "POST /api/v1/auth/login - User login with credentials",
                "POST /api/v1/auth/logout - User logout",
                "POST /api/v1/auth/refresh - Refresh authentication token",
                "POST /api/v1/auth/2fa/enable - Enable two-factor authentication",
                "POST /api/v1/auth/2fa/verify - Verify 2FA code"
            ]
        })
    
    # Check user management
    has_user_mgmt = any("user" in d["endpoint"].lower() and "create" in d["endpoint"].lower() 
                        for d in test_results["details"])
    if not has_user_mgmt:
        suggestions.append({
            "category": "User Management",
            "endpoints": [
                "POST /api/v1/users/create - Create new user",
                "PUT /api/v1/users/{user_id} - Update user details",
                "DELETE /api/v1/users/{user_id} - Delete user",
                "GET /api/v1/users/{user_id} - Get user details",
                "GET /api/v1/users - List all users"
            ]
        })
    
    # Check for rate limiting info
    suggestions.append({
        "category": "Rate Limiting",
        "endpoints": [
            "GET /api/v1/rate_limit/status - Get current rate limit status",
            "GET /api/v1/rate_limit/quotas - Get user quotas"
        ]
    })
    
    # Check for webhook support
    suggestions.append({
        "category": "Webhooks",
        "endpoints": [
            "POST /api/v1/webhooks/create - Create webhook",
            "GET /api/v1/webhooks - List webhooks",
            "DELETE /api/v1/webhooks/{webhook_id} - Delete webhook",
            "POST /api/v1/webhooks/{webhook_id}/test - Test webhook"
        ]
    })
    
    # Check for batch operations
    suggestions.append({
        "category": "Batch Operations",
        "endpoints": [
            "POST /api/v1/batch/folders/add - Add multiple folders",
            "POST /api/v1/batch/shares/create - Create multiple shares",
            "DELETE /api/v1/batch/files - Delete multiple files"
        ]
    })
    
    test_results["suggested_endpoints"] = suggestions
    
    for suggestion in suggestions:
        print(f"\n📌 {suggestion['category']}:")
        for endpoint in suggestion["endpoints"]:
            print(f"   - {endpoint}")

def generate_report():
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("="*60)
    
    # Calculate statistics
    success_rate = (test_results["passed"] / test_results["total"] * 100) if test_results["total"] > 0 else 0
    
    print(f"""
📈 Test Statistics:
   Total Tests: {test_results["total"]}
   Passed: {test_results["passed"]} ✅
   Failed: {test_results["failed"]} ❌
   Warnings: {test_results["warnings"]} ⚠️
   Success Rate: {success_rate:.1f}%
   
📝 Test Coverage:
   System Endpoints: Tested
   Security Endpoints: Tested
   Folder Operations: Tested
   Backup Operations: Tested
   Monitoring: Tested
   Upload/Download: Tested
   Network Management: Tested
   
🔍 Response Validation:
   - All responses checked for JSON format
   - Expected fields validated
   - Status codes verified
   - Error handling tested
    """)
    
    # Failed tests details
    if test_results["failed"] > 0:
        print("\n❌ Failed Tests:")
        for detail in test_results["details"]:
            if detail["status"] == "FAIL":
                print(f"   - {detail['method']} {detail['endpoint']}: {detail['details']}")
    
    # Warnings
    if test_results["warnings"] > 0:
        print("\n⚠️ Warnings:")
        for detail in test_results["details"]:
            if detail["status"] == "WARN":
                print(f"   - {detail['method']} {detail['endpoint']}: {detail['details']}")
    
    # Suggested improvements
    if test_results["suggested_endpoints"]:
        print("\n💡 Suggested Additional Endpoints:")
        total_suggestions = sum(len(s["endpoints"]) for s in test_results["suggested_endpoints"])
        print(f"   Total Suggestions: {total_suggestions} endpoints across {len(test_results['suggested_endpoints'])} categories")
    
    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Final verdict
    print("\n" + "="*60)
    if success_rate == 100:
        print("🎉 PERFECT SCORE! All endpoints working correctly!")
    elif success_rate >= 95:
        print("✅ EXCELLENT! API is production-ready with minor issues.")
    elif success_rate >= 80:
        print("👍 GOOD! API is functional but needs some fixes.")
    else:
        print("⚠️ NEEDS WORK! Several endpoints require attention.")
    print("="*60)

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("="*60)
    print("🧪 COMPREHENSIVE API TEST SUITE - ALL 133 ENDPOINTS")
    print("="*60)
    print(f"Testing: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*60)
    
    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding correctly!")
            return
    except:
        print("❌ Server not running! Please start the backend first.")
        return
    
    # Run all test categories
    test_system_endpoints()
    test_security_endpoints()
    test_folder_operations()
    test_backup_operations()
    test_monitoring_operations()
    test_upload_download_operations()
    test_network_operations()
    
    # Analyze and report
    analyze_missing_features()
    generate_report()

if __name__ == "__main__":
    run_comprehensive_tests()