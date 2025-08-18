#!/usr/bin/env python3
"""
Comprehensive test to verify all functionality works
"""

import subprocess
import json
import sys
import os
import tempfile
from pathlib import Path

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def test_cli_import():
    """Test that CLI can be imported without errors"""
    print("\n" + "="*60)
    print("TEST: CLI Import")
    print("="*60)
    
    stdout, stderr, code = run_command("python3 -c \"import sys; sys.path.insert(0, 'src'); import cli; print('OK')\"")
    
    if code == 0 and "OK" in stdout:
        print("✓ CLI imports successfully")
        return True
    else:
        print(f"✗ CLI import failed: {stderr}")
        return False

def test_create_share():
    """Test share creation"""
    print("\n" + "="*60)
    print("TEST: Create Share")
    print("="*60)
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content for share")
        test_file = f.name
    
    try:
        cmd = f"python3 src/cli.py create-share --files {test_file} --type public"
        stdout, stderr, code = run_command(cmd)
        
        if code == 0:
            try:
                share = json.loads(stdout)
                if 'shareId' in share:
                    print(f"✓ Share created: {share['shareId']}")
                    print(f"  Type: {share.get('type')}")
                    print(f"  Size: {share.get('size')} bytes")
                    return True
            except json.JSONDecodeError:
                pass
        
        print(f"✗ Share creation failed: {stderr}")
        return False
    finally:
        os.unlink(test_file)

def test_connection():
    """Test NNTP connection handling"""
    print("\n" + "="*60)
    print("TEST: NNTP Connection")
    print("="*60)
    
    # Test with fake server (should fail gracefully)
    cmd = "python3 src/cli.py test-connection --hostname test.example.com --port 119 --username test --password test --no-ssl"
    stdout, stderr, code = run_command(cmd)
    
    if code != 0:  # Should fail
        try:
            error_data = json.loads(stderr)
            if 'error' in error_data:
                print(f"✓ Connection test handled error gracefully")
                print(f"  Error: {error_data['error']}")
                return True
        except:
            pass
    
    print(f"✗ Connection test didn't handle error properly")
    return False

def test_index_folder():
    """Test folder indexing"""
    print("\n" + "="*60)
    print("TEST: Folder Indexing")
    print("="*60)
    
    # Create temp directory with files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        for i in range(3):
            Path(tmpdir, f"file{i}.txt").write_text(f"Content {i}")
        
        cmd = f"python3 src/cli.py index-folder --path {tmpdir}"
        stdout, stderr, code = run_command(cmd)
        
        if code == 0:
            try:
                tree = json.loads(stdout)
                if 'children' in tree and len(tree['children']) == 3:
                    print(f"✓ Indexed folder: {tree['name']}")
                    print(f"  Files found: {len(tree['children'])}")
                    print(f"  Total size: {tree['size']} bytes")
                    return True
            except json.JSONDecodeError:
                pass
        
        print(f"✗ Folder indexing failed: {stderr}")
        return False

def test_database():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("TEST: Database Connection")
    print("="*60)
    
    cmd = """python3 -c "
import sys
sys.path.insert(0, 'src')
from database.postgresql_manager import PostgresConfig, ShardedPostgreSQLManager
import json

try:
    # Try to load db config
    with open('db_config.json') as f:
        db_config = json.load(f)
    
    config = PostgresConfig(
        host=db_config.get('host', 'localhost'),
        port=db_config.get('port', 5432),
        database=db_config.get('database', 'usenetsync'),
        user=db_config.get('user', 'usenet'),
        password=db_config.get('password', 'usenet_secure_2024')
    )
    
    db = ShardedPostgreSQLManager(config)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM shares')
        count = cursor.fetchone()[0]
        print(f'OK:{count}')
except Exception as e:
    print(f'ERROR:{e}')
" """
    
    stdout, stderr, code = run_command(cmd)
    
    if "OK:" in stdout:
        count = stdout.split("OK:")[1].strip()
        print(f"✓ Database connected")
        print(f"  Shares in database: {count}")
        return True
    else:
        error = stdout.split("ERROR:")[1].strip() if "ERROR:" in stdout else stderr
        print(f"⚠ Database not available: {error[:100]}")
        return False  # Database is optional

def test_python_modules():
    """Test that all required Python modules can be imported"""
    print("\n" + "="*60)
    print("TEST: Python Module Imports")
    print("="*60)
    
    modules = [
        ('upload.enhanced_upload', 'Upload module'),
        ('download.enhanced_download', 'Download module'),
        ('networking.production_nntp_client', 'NNTP client'),
        ('database.postgresql_manager', 'Database manager'),
        ('security.enhanced_security_system', 'Security system'),
        ('indexing.share_id_generator', 'Share ID generator')
    ]
    
    all_ok = True
    for module, name in modules:
        cmd = f"""python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    import {module.replace('.', ' as mod; from ')} import *
    print('OK')
except ImportError as e:
    print(f'ERROR:{{e}}')
" """
        
        stdout, stderr, code = run_command(cmd)
        
        if "OK" in stdout:
            print(f"  ✓ {name}: Available")
        else:
            error = stdout.split("ERROR:")[1].strip() if "ERROR:" in stdout else "Import failed"
            print(f"  ✗ {name}: {error[:50]}")
            all_ok = False
    
    return all_ok

def main():
    """Run all tests"""
    print("="*60)
    print("COMPREHENSIVE FUNCTIONALITY TEST")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("CLI Import", test_cli_import()))
    results.append(("Python Modules", test_python_modules()))
    results.append(("Database", test_database()))
    results.append(("Create Share", test_create_share()))
    results.append(("NNTP Connection", test_connection()))
    results.append(("Folder Indexing", test_index_folder()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())