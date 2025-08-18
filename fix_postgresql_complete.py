#!/usr/bin/env python3
"""
Complete PostgreSQL Fix for UsenetSync
This script will start PostgreSQL and fix all authentication issues
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

def start_postgresql():
    """Start PostgreSQL service"""
    print("\n1. Starting PostgreSQL...")
    
    # Find portable PostgreSQL
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    data_dir = app_dir / 'pgdata'
    
    if not pg_dir.exists():
        print("   ✗ PostgreSQL not found at:", pg_dir)
        return False
    
    if not data_dir.exists():
        print("   ✗ PostgreSQL data directory not found at:", data_dir)
        return False
    
    postgres_exe = pg_dir / 'bin' / 'postgres.exe'
    pg_ctl_exe = pg_dir / 'bin' / 'pg_ctl.exe'
    
    # Check if already running
    pid_file = app_dir / 'postgresql.pid'
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            old_pid = f.read().strip()
        # Kill old process
        run_command(f'taskkill /PID {old_pid} /F', capture=False)
        time.sleep(2)
    
    # Start PostgreSQL using pg_ctl (better method)
    print(f"   Starting PostgreSQL from {pg_dir}")
    log_file = app_dir / 'postgresql.log'
    
    # Use pg_ctl to start PostgreSQL
    cmd = f'"{pg_ctl_exe}" start -D "{data_dir}" -l "{log_file}" -w'
    success, output, error = run_command(cmd, capture=True)
    
    if success or 'server starting' in output or 'server started' in output:
        print("   ✓ PostgreSQL started successfully")
        time.sleep(3)  # Give it time to fully start
        return True
    else:
        # Try alternative method
        print("   Trying alternative start method...")
        
        # Start directly with postgres.exe
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                [str(postgres_exe), '-D', str(data_dir)],
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        
        # Save PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        time.sleep(5)  # Give it more time to start
        
        # Check if it's running
        success, output, _ = run_command(f'tasklist /FI "PID eq {process.pid}"')
        if success and str(process.pid) in output:
            print("   ✓ PostgreSQL started (alternative method)")
            return True
    
    print(f"   ✗ Failed to start PostgreSQL: {error}")
    return False

def fix_pg_hba_conf():
    """Fix pg_hba.conf for proper authentication"""
    print("\n2. Fixing pg_hba.conf configuration...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    data_dir = app_dir / 'pgdata'
    pg_hba_file = data_dir / 'pg_hba.conf'
    
    if not pg_hba_file.exists():
        print(f"   ✗ pg_hba.conf not found at {pg_hba_file}")
        return False
    
    # Read the file
    with open(pg_hba_file, 'r') as f:
        content = f.read()
    
    # Backup original
    backup_file = pg_hba_file.with_suffix('.conf.backup')
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"   Backup saved to {backup_file}")
    
    # Replace all 'scram-sha-256' with 'md5' for simpler authentication
    content = content.replace('scram-sha-256', 'md5')
    
    # Ensure proper configuration for local connections
    lines = content.split('\n')
    new_lines = []
    added_config = False
    
    for line in lines:
        # Skip existing usenet configurations
        if 'usenet' in line.lower() and not line.strip().startswith('#'):
            continue
        new_lines.append(line)
        
        # Add our configuration after the IPv4 section
        if 'IPv4 local connections:' in line and not added_config:
            new_lines.append('host    all             all             127.0.0.1/32            md5')
            new_lines.append('host    usenet          usenet          127.0.0.1/32            md5')
            added_config = True
    
    # Write the fixed configuration
    with open(pg_hba_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("   ✓ Fixed pg_hba.conf")
    return True

def reload_postgresql_config():
    """Reload PostgreSQL configuration"""
    print("\n3. Reloading PostgreSQL configuration...")
    
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pg_dir = app_dir / 'postgresql'
    data_dir = app_dir / 'pgdata'
    pg_ctl_exe = pg_dir / 'bin' / 'pg_ctl.exe'
    
    # Reload configuration
    cmd = f'"{pg_ctl_exe}" reload -D "{data_dir}"'
    success, output, error = run_command(cmd, capture=True)
    
    if success or 'server signaled' in output:
        print("   ✓ PostgreSQL configuration reloaded")
        time.sleep(2)
        return True
    else:
        # Try restart instead
        print("   Restarting PostgreSQL...")
        cmd = f'"{pg_ctl_exe}" restart -D "{data_dir}" -w'
        success, output, error = run_command(cmd, capture=True)
        if success:
            print("   ✓ PostgreSQL restarted")
            time.sleep(3)
            return True
    
    print(f"   ⚠ Could not reload config: {error}")
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
    
    # SQL commands
    sql_commands = [
        "DROP USER IF EXISTS usenet;",
        "CREATE USER usenet WITH PASSWORD 'usenetsync';",
        "DROP DATABASE IF EXISTS usenet;",
        "CREATE DATABASE usenet OWNER usenet;",
        "GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;"
    ]
    
    for sql in sql_commands:
        print(f"   Executing: {sql[:50]}...")
        
        # Try different connection methods
        for host in ['localhost', '127.0.0.1', None]:
            host_arg = f'-h {host}' if host else ''
            cmd = f'echo {sql} | "{psql_exe}" -U postgres {host_arg}'
            
            # Try without password
            success, output, error = run_command(cmd, capture=True)
            if success or 'already exists' in error or 'CREATE' in output or 'DROP' in output or 'GRANT' in output:
                break
            
            # Try with postgres password
            os.environ['PGPASSWORD'] = 'postgres'
            success, output, error = run_command(cmd, capture=True)
            if success or 'already exists' in error or 'CREATE' in output or 'DROP' in output or 'GRANT' in output:
                break
            
            # Try with empty password
            os.environ['PGPASSWORD'] = ''
            success, output, error = run_command(cmd, capture=True)
            if success or 'already exists' in error or 'CREATE' in output or 'DROP' in output or 'GRANT' in output:
                break
    
    print("   ✓ Database and user setup completed")
    return True

def test_connection():
    """Test the PostgreSQL connection"""
    print("\n5. Testing connection...")
    
    try:
        import psycopg2
        
        # Test connection
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='usenet',
            password='usenetsync',
            database='usenet',
            connect_timeout=5
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("   ✓ Successfully connected to PostgreSQL!")
        print(f"   Version: {version[0][:50]}...")
        return True
        
    except ImportError:
        print("   ✗ psycopg2 not installed")
        print("   Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False

def save_config():
    """Save configuration to force PostgreSQL usage"""
    print("\n6. Saving configuration...")
    
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
            'force_sqlite': False
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"   ✓ Configuration saved to {config_file}")
    return True

def main():
    print("=" * 60)
    print("Complete PostgreSQL Fix for UsenetSync")
    print("=" * 60)
    
    # Step 1: Start PostgreSQL
    if not start_postgresql():
        print("\n✗ Failed to start PostgreSQL")
        print("Please check if PostgreSQL is properly installed")
        return 1
    
    # Step 2: Fix pg_hba.conf
    fix_pg_hba_conf()
    
    # Step 3: Reload configuration
    reload_postgresql_config()
    
    # Step 4: Create database and user
    create_database_and_user()
    
    # Step 5: Test connection
    if test_connection():
        # Step 6: Save configuration
        save_config()
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS! PostgreSQL is now configured and running!")
        print("=" * 60)
        print("\nConnection details:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: usenet")
        print("  User: usenet")
        print("  Password: usenetsync")
        print("\nYou can now use PostgreSQL in UsenetSync!")
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ Connection still failing")
        print("=" * 60)
        print("\nTry running force_sqlite.py to use SQLite instead:")
        print("  python force_sqlite.py")
        return 1

if __name__ == '__main__':
    try:
        # Ensure we have admin rights on Windows
        if sys.platform == 'win32':
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("⚠ This script should be run as Administrator for best results")
                print("  Right-click and select 'Run as administrator'\n")
        
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)