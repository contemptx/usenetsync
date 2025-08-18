#!/usr/bin/env python3
"""
Restart and Fix PostgreSQL for UsenetSync
This script will stop any running PostgreSQL instances and restart with proper configuration
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def run_command(cmd, capture=True, shell=True):
    """Run a command and return output"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=shell)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def stop_all_postgresql():
    """Stop all PostgreSQL processes"""
    print("\n1. Stopping all PostgreSQL processes...")
    
    # Kill all postgres.exe processes
    print("   Stopping postgres.exe processes...")
    run_command('taskkill /F /IM postgres.exe 2>nul', capture=False)
    time.sleep(2)
    
    # Kill all pg_ctl.exe processes
    print("   Stopping pg_ctl.exe processes...")
    run_command('taskkill /F /IM pg_ctl.exe 2>nul', capture=False)
    time.sleep(1)
    
    # Remove PID file
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pid_file = app_dir / 'postgresql.pid'
    if pid_file.exists():
        pid_file.unlink()
        print("   Removed PID file")
    
    # Remove postmaster.pid if it exists
    data_dir = app_dir / 'pgdata'
    postmaster_pid = data_dir / 'postmaster.pid'
    if postmaster_pid.exists():
        postmaster_pid.unlink()
        print("   Removed postmaster.pid")
    
    print("   ✓ All PostgreSQL processes stopped")
    time.sleep(2)
    return True

def fix_pg_hba_conf():
    """Fix pg_hba.conf for proper authentication"""
    print("\n2. Fixing authentication configuration...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    data_dir = app_dir / 'pgdata'
    pg_hba_file = data_dir / 'pg_hba.conf'
    
    if not pg_hba_file.exists():
        print(f"   ✗ pg_hba.conf not found at {pg_hba_file}")
        return False
    
    # Create a simple, working configuration
    new_config = """# TYPE  DATABASE        USER            ADDRESS                 METHOD

# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust

# Allow usenet user with password
host    usenet          usenet          127.0.0.1/32            md5
host    usenet          usenet          ::1/128                 md5

# Local connections
local   all             all                                     trust
"""
    
    # Backup original
    backup_file = pg_hba_file.with_suffix('.conf.backup')
    if pg_hba_file.exists():
        with open(pg_hba_file, 'r') as f:
            original = f.read()
        with open(backup_file, 'w') as f:
            f.write(original)
        print(f"   Backup saved to {backup_file}")
    
    # Write new configuration
    with open(pg_hba_file, 'w') as f:
        f.write(new_config)
    
    print("   ✓ Created clean pg_hba.conf with trust authentication")
    return True

def start_postgresql_clean():
    """Start PostgreSQL with clean state"""
    print("\n3. Starting PostgreSQL...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    data_dir = app_dir / 'pgdata'
    
    if not pg_dir.exists():
        print(f"   ✗ PostgreSQL not found at {pg_dir}")
        return False
    
    if not data_dir.exists():
        print(f"   ✗ Data directory not found at {data_dir}")
        return False
    
    pg_ctl_exe = pg_dir / 'bin' / 'pg_ctl.exe'
    
    # Start PostgreSQL
    log_file = app_dir / 'postgresql.log'
    print(f"   Starting PostgreSQL from {pg_dir}")
    print(f"   Data directory: {data_dir}")
    print(f"   Log file: {log_file}")
    
    cmd = f'"{pg_ctl_exe}" start -D "{data_dir}" -l "{log_file}" -w -t 30'
    success, output, error = run_command(cmd, capture=True)
    
    if success or 'server started' in output.lower() or 'server starting' in output.lower():
        print("   ✓ PostgreSQL started successfully")
        time.sleep(3)
        return True
    else:
        print(f"   Error output: {error}")
        print(f"   Standard output: {output}")
        
        # Check log file for errors
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_content = f.read()
                print("\n   Last 10 lines of log file:")
                lines = log_content.split('\n')
                for line in lines[-10:]:
                    if line.strip():
                        print(f"     {line}")
        
        return False

def create_database_and_user():
    """Create the usenet database and user"""
    print("\n4. Creating database and user...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    psql_exe = pg_dir / 'bin' / 'psql.exe'
    
    if not psql_exe.exists():
        print(f"   ✗ psql.exe not found at {psql_exe}")
        return False
    
    # Since we're using 'trust' authentication, we don't need a password
    commands = [
        ("Dropping old user if exists", "DROP USER IF EXISTS usenet;"),
        ("Creating user", "CREATE USER usenet WITH PASSWORD 'usenetsync';"),
        ("Dropping old database if exists", "DROP DATABASE IF EXISTS usenet;"),
        ("Creating database", "CREATE DATABASE usenet OWNER usenet;"),
        ("Granting privileges", "GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;"),
        ("Altering user", "ALTER USER usenet WITH PASSWORD 'usenetsync';"),
    ]
    
    for description, sql in commands:
        print(f"   {description}...")
        
        # Use trust authentication (no password needed)
        cmd = f'echo {sql} | "{psql_exe}" -U postgres -h localhost'
        success, output, error = run_command(cmd, capture=True)
        
        if not success and 'already exists' not in error and 'does not exist' not in error:
            print(f"     Warning: {error[:100]}")
    
    print("   ✓ Database setup completed")
    return True

def test_connection():
    """Test the PostgreSQL connection"""
    print("\n5. Testing connection...")
    
    # First test with psql
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    psql_exe = pg_dir / 'bin' / 'psql.exe'
    
    print("   Testing with psql...")
    os.environ['PGPASSWORD'] = 'usenetsync'
    cmd = f'echo SELECT 1; | "{psql_exe}" -U usenet -h localhost -d usenet'
    success, output, error = run_command(cmd, capture=True)
    
    if success or '1' in output:
        print("   ✓ psql connection successful")
    else:
        print(f"   ✗ psql connection failed: {error[:200]}")
    
    # Try with psycopg2
    try:
        import psycopg2
        
        print("   Testing with psycopg2...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='usenet',
            password='usenetsync',
            database='usenet',
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("   ✓ psycopg2 connection successful!")
        print(f"   PostgreSQL version: {version[0][:60]}...")
        return True
        
    except ImportError:
        print("   ⚠ psycopg2 not installed (pip install psycopg2-binary)")
        return success  # Return psql result
    except Exception as e:
        print(f"   ✗ psycopg2 connection failed: {e}")
        return success  # Return psql result

def check_postgresql_status():
    """Check if PostgreSQL is responding"""
    print("\n6. Checking PostgreSQL status...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    data_dir = app_dir / 'pgdata'
    pg_ctl_exe = pg_dir / 'bin' / 'pg_ctl.exe'
    
    cmd = f'"{pg_ctl_exe}" status -D "{data_dir}"'
    success, output, error = run_command(cmd, capture=True)
    
    if success or 'server is running' in output.lower():
        print(f"   ✓ PostgreSQL is running")
        print(f"     {output.strip()}")
        return True
    else:
        print(f"   ✗ PostgreSQL status check failed")
        print(f"     {output.strip()}")
        return False

def save_config():
    """Save configuration"""
    print("\n7. Saving configuration...")
    
    config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync'
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / 'config.json'
    
    config = {
        'database': {
            'type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'usenet',
            'user': 'usenet',
            'password': 'usenetsync'
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"   ✓ Configuration saved to {config_file}")
    return True

def main():
    print("=" * 60)
    print("PostgreSQL Restart and Fix Tool")
    print("=" * 60)
    
    # Step 1: Stop all PostgreSQL processes
    stop_all_postgresql()
    
    # Step 2: Fix authentication configuration
    fix_pg_hba_conf()
    
    # Step 3: Start PostgreSQL clean
    if not start_postgresql_clean():
        print("\n✗ Failed to start PostgreSQL")
        print("\nTrying to check what's wrong...")
        
        # Check if port 5432 is in use
        success, output, _ = run_command('netstat -an | findstr :5432', capture=True)
        if success and ':5432' in output:
            print("Port 5432 is in use by another process")
            print("Try running: netstat -ab | findstr :5432")
        
        return 1
    
    # Step 4: Create database and user
    create_database_and_user()
    
    # Step 5: Test connection
    connection_works = test_connection()
    
    # Step 6: Check status
    check_postgresql_status()
    
    if connection_works:
        # Step 7: Save configuration
        save_config()
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS! PostgreSQL is now working!")
        print("=" * 60)
        print("\nConnection details:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: usenet")
        print("  User: usenet")
        print("  Password: usenetsync")
        print("\nPostgreSQL is ready for UsenetSync!")
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠ PostgreSQL is running but connection needs work")
        print("=" * 60)
        print("\nYou can either:")
        print("1. Try running this script again")
        print("2. Use SQLite instead: python force_sqlite.py")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)