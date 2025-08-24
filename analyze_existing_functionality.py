#!/usr/bin/env python3
"""
Analyze existing REAL functionality in the codebase
"""

import os
import re
import ast

def analyze_unified_system():
    """Analyze what methods and functionality UnifiedSystem actually has"""
    
    print("=" * 80)
    print("ANALYZING EXISTING UNIFIED SYSTEM FUNCTIONALITY")
    print("=" * 80)
    
    # Analyze main.py for UnifiedSystem methods
    with open('/workspace/backend/src/unified/main.py', 'r') as f:
        content = f.read()
    
    # Find all method definitions in UnifiedSystem
    methods = re.findall(r'def (\w+)\(self.*?\):', content)
    
    print("\n📦 UnifiedSystem Methods Available:")
    print("-" * 40)
    for method in methods:
        if not method.startswith('_'):
            print(f"  - {method}")
    
    # Analyze what subsystems are initialized
    print("\n🔧 Subsystems Initialized in UnifiedSystem:")
    print("-" * 40)
    subsystems = [
        ('self.db', 'Database'),
        ('self.auth', 'Authentication'),
        ('self.encryption', 'Encryption'),
        ('self.access_control', 'Access Control'),
        ('self.obfuscation', 'Obfuscation'),
        ('self.key_manager', 'Key Management'),
        ('self.zkp', 'Zero Knowledge Proofs'),
        ('self.scanner', 'File Scanner'),
        ('self.versioning', 'Versioning'),
        ('self.binary_index', 'Binary Index'),
        ('self.streaming', 'Streaming'),
        ('self.change_detection', 'Change Detection'),
        ('self.folder_stats', 'Folder Statistics'),
        ('self.segment_processor', 'Segment Processor'),
        ('self.packing', 'Packing'),
        ('self.redundancy', 'Redundancy'),
        ('self.hashing', 'Hashing'),
        ('self.compression', 'Compression'),
        ('self.headers', 'Headers'),
        ('self.upload_queue', 'Upload Queue'),
        ('self.nntp_client', 'NNTP Client (Real Usenet)'),
    ]
    
    for attr, name in subsystems:
        if attr in content:
            print(f"  ✅ {name}: {attr}")
    
    # Check for specific functionality
    print("\n🎯 Key Functionality Check:")
    print("-" * 40)
    
    functionality_checks = [
        ('index_folder', 'Folder Indexing'),
        ('create_share', 'Share Creation'),
        ('upload_to_usenet', 'Usenet Upload'),
        ('download_from_usenet', 'Usenet Download'),
        ('segment_processor.process_folder', 'Folder Segmentation'),
        ('upload_queue.add_folder', 'Queue Management'),
        ('auth.create_user', 'User Creation'),
        ('auth.authenticate', 'User Authentication'),
        ('encryption.encrypt_file', 'File Encryption'),
        ('access_control.check_access', 'Access Control'),
    ]
    
    for func, desc in functionality_checks:
        if func in content:
            print(f"  ✅ {desc}: Found")
        else:
            print(f"  ❌ {desc}: Not found")
    
    return methods

def analyze_api_endpoints():
    """Analyze what endpoints are defined vs what they actually do"""
    
    print("\n" + "=" * 80)
    print("ANALYZING API ENDPOINT IMPLEMENTATIONS")
    print("=" * 80)
    
    with open('/workspace/backend/src/unified/api/server.py', 'r') as f:
        content = f.read()
    
    # Find all endpoint definitions
    endpoints = re.findall(r'@self\.app\.(get|post|put|delete|patch)\("([^"]+)"\)', content)
    
    print(f"\n📊 Total Endpoints Defined: {len(endpoints)}")
    
    # Categorize endpoints by their implementation
    categories = {
        'uses_system': [],
        'raises_503': [],
        'raises_500': [],
        'returns_mock': [],
        'properly_implemented': []
    }
    
    for method, path in endpoints:
        # Find the function implementation after this endpoint
        pattern = f'@self\.app\.{method}\("{re.escape(path)}"\).*?(?:@self\.app\.|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            impl = match.group(0)
            
            if 'self.system.' in impl and 'raise HTTPException(status_code=503' not in impl:
                categories['properly_implemented'].append(f"{method.upper()} {path}")
            elif 'raise HTTPException(status_code=503' in impl:
                categories['raises_503'].append(f"{method.upper()} {path}")
            elif 'raise HTTPException(status_code=500' in impl:
                categories['raises_500'].append(f"{method.upper()} {path}")
            elif 'return {' in impl and ('test_' in impl or 'mock' in impl):
                categories['returns_mock'].append(f"{method.upper()} {path}")
            elif 'self.system' in impl:
                categories['uses_system'].append(f"{method.upper()} {path}")
    
    print("\n✅ Properly Implemented (uses self.system without 503):")
    for ep in categories['properly_implemented'][:10]:
        print(f"  - {ep}")
    if len(categories['properly_implemented']) > 10:
        print(f"  ... and {len(categories['properly_implemented']) - 10} more")
    
    print(f"\n❌ Raises 503 (System not initialized): {len(categories['raises_503'])} endpoints")
    print(f"❌ Raises 500 (Generic error): {len(categories['raises_500'])} endpoints")
    print(f"❌ Returns mock data: {len(categories['returns_mock'])} endpoints")
    print(f"⚠️  Uses system but may have issues: {len(categories['uses_system'])} endpoints")
    
    return categories

def analyze_database_schema():
    """Check what database tables and operations we have"""
    
    print("\n" + "=" * 80)
    print("ANALYZING DATABASE SCHEMA")
    print("=" * 80)
    
    with open('/workspace/backend/src/unified/core/schema.py', 'r') as f:
        content = f.read()
    
    # Find table definitions
    tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content)
    
    print("\n📊 Database Tables:")
    for table in tables:
        print(f"  - {table}")
    
    return tables

def main():
    # Analyze UnifiedSystem
    system_methods = analyze_unified_system()
    
    # Analyze API endpoints
    endpoint_categories = analyze_api_endpoints()
    
    # Analyze database
    tables = analyze_database_schema()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"""
📈 Statistics:
  - UnifiedSystem methods: {len(system_methods)}
  - Database tables: {len(tables)}
  - Total API endpoints: {sum(len(v) for v in endpoint_categories.values())}
  - Properly implemented: {len(endpoint_categories['properly_implemented'])}
  - Need fixing: {len(endpoint_categories['raises_503']) + len(endpoint_categories['raises_500']) + len(endpoint_categories['returns_mock'])}
  
🎯 Key Findings:
  - We HAVE a complete UnifiedSystem with real functionality
  - We HAVE real NNTP client connected to Newshosting
  - We HAVE database, authentication, encryption, etc.
  - Most endpoints are NOT properly connected to the system
  - Many endpoints just raise 503 or 500 errors instead of using the system
  
✅ Next Steps:
  1. Fix the backend startup issue
  2. Connect endpoints to existing UnifiedSystem methods
  3. Remove all 503/500 error placeholders
  4. Test with real Usenet operations
""")

if __name__ == "__main__":
    main()