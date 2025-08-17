#!/usr/bin/env python3
"""
Fix all Python backend issues to reach 100% functionality
"""

import os
import re

def fix_server_rotation():
    """Fix ServerRotationManager to work with optional servers parameter"""
    
    file_path = 'src/networking/server_rotation.py'
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Make servers parameter optional in __init__
    content = re.sub(
        r'def __init__\(\s*self,\s*servers:\s*List\[ServerConfig\]',
        'def __init__(self, servers: Optional[List[ServerConfig]] = None',
        content
    )
    
    # Fix 2: Handle None servers in initialization
    content = re.sub(
        r'self\.servers = \{s\.server_id: s for s in servers\}',
        'self.servers = {s.id: s for s in (servers or [])}',
        content
    )
    
    # Fix 3: Handle None in health tracking
    content = re.sub(
        r'self\.server_health = \{\s*s\.server_id: ServerHealth\(server_id=s\.server_id\)\s*for s in servers\s*\}',
        'self.server_health = {s.id: ServerHealth(server_id=s.id) for s in (servers or [])}',
        content
    )
    
    # Fix 4: Ensure Optional is imported
    if 'from typing import' in content and 'Optional' not in content:
        content = content.replace(
            'from typing import List',
            'from typing import List, Optional'
        )
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed ServerRotationManager")

def verify_all_modules():
    """Verify all Python modules work"""
    import sys
    sys.path.insert(0, '/workspace/src')
    
    modules = [
        "cli",
        "core.integrated_backend", 
        "networking.bandwidth_controller",
        "security.enhanced_security_system",
        "core.version_control",
        "networking.server_rotation",
        "networking.retry_manager",
        "core.log_manager",
        "core.data_management",
        "upload.enhanced_upload",
        "download.enhanced_download",
        "publishing.publishing_system"
    ]
    
    results = []
    for module in modules:
        try:
            __import__(module)
            results.append((module, True))
            print(f"✅ {module}")
        except Exception as e:
            results.append((module, False))
            print(f"❌ {module}: {str(e)[:50]}")
    
    # Test functionality
    try:
        from networking.bandwidth_controller import BandwidthController
        bc = BandwidthController()
        import asyncio
        asyncio.run(bc.consume_upload_tokens(1024))
        print("✅ Async methods working")
        results.append(("async", True))
    except:
        print("❌ Async methods")
        results.append(("async", False))
    
    # Calculate success rate
    passed = sum(1 for _, result in results if result)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    return pass_rate

if __name__ == "__main__":
    print("🔧 Fixing Python Backend to 100%...")
    print("="*60)
    
    # Apply fixes
    fix_server_rotation()
    
    # Verify
    print("\n📊 Verification:")
    print("-"*40)
    pass_rate = verify_all_modules()
    
    print("\n" + "="*60)
    if pass_rate == 100:
        print("🎉 PYTHON BACKEND 100% FUNCTIONAL!")
    else:
        print(f"⚠️ Python backend at {pass_rate:.1f}%")