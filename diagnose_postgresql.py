#!/usr/bin/env python3
"""
PostgreSQL Diagnostic and Fix Tool for UsenetSync
This script will help diagnose and fix PostgreSQL connection issues
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import time

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

def check_postgresql_service():
    """Check if PostgreSQL service is running"""
    print("\n1. Checking PostgreSQL service status...")
    
    # Check for Windows service
    success, output, _ = run_command('sc query postgresql-x64-14')
    if success and 'RUNNING' in output:
        print("   ✓ PostgreSQL service is running (System installation)")
        return True, "system"
    
    # Check for portable PostgreSQL
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pid_file = app_dir / 'postgresql.pid'
    
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        
        # Check if process is running
        success, output, _ = run_command(f'tasklist /FI "PID eq {pid}"')
        if success and pid in output:
            print(f"   ✓ PostgreSQL is running (Portable installation, PID: {pid})")
            return True, "portable"
    
    print("   ✗ PostgreSQL is not running")
    return False, None

def find_postgresql_installation():
    """Find PostgreSQL installation"""
    print("\n2. Looking for PostgreSQL installation...")
    
    locations = []
    
    # Check portable installation
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    portable_pg = app_dir / 'postgresql'
    if portable_pg.exists():
        locations.append(('portable', portable_pg))
        print(f"   ✓ Found portable installation: {portable_pg}")
    
    # Check Program Files
    program_files = [
        Path("C:/Program Files/PostgreSQL"),
        Path("C:/Program Files (x86)/PostgreSQL")
    ]
    
    for pf in program_files:
        if pf.exists():
            for version_dir in pf.iterdir():
                if version_dir.is_dir():
                    locations.append(('system', version_dir))
                    print(f"   ✓ Found system installation: {version_dir}")
    
    if not locations:
        print("   ✗ No PostgreSQL installation found")
    
    return locations

def test_connection(host='localhost', port=5432, user='usenet', password='usenetsync', database='usenet'):
    """Test PostgreSQL connection"""
    print(f"\n3. Testing connection to {host}:{port} as user '{user}'...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=3
        )
        conn.close()
        print(f"   ✓ Successfully connected to database '{database}'")
        return True
    except ImportError:
        print("   ✗ psycopg2 module not installed")
        print("     Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False

def fix_postgresql_auth(pg_dir):
    """Fix PostgreSQL authentication"""
    print("\n4. Attempting to fix PostgreSQL authentication...")
    
    if isinstance(pg_dir, tuple):
        pg_type, pg_dir = pg_dir
    else:
        pg_type = 'unknown'
    
    psql_exe = pg_dir / 'bin' / 'psql.exe'
    
    if not psql_exe.exists():
        print(f"   ✗ psql.exe not found at {psql_exe}")
        return False
    
    print("   Creating database and user...")
    
    # SQL commands to create user and database
    sql_commands = """
CREATE USER usenet WITH PASSWORD 'usenetsync';
CREATE DATABASE usenet OWNER usenet;
GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;
"""
    
    # Try to connect as postgres user (no password)
    print("   Attempting to connect as postgres user...")
    success, output, error = run_command(
        f'echo {sql_commands} | "{psql_exe}" -U postgres -h localhost',
        capture=True
    )
    
    if success or 'already exists' in error:
        print("   ✓ Database and user created/verified")
        return True
    
    # Try with default password
    print("   Trying with default postgres password...")
    os.environ['PGPASSWORD'] = 'postgres'
    success, output, error = run_command(
        f'echo {sql_commands} | "{psql_exe}" -U postgres -h localhost',
        capture=True
    )
    
    if success or 'already exists' in error:
        print("   ✓ Database and user created/verified")
        return True
    
    print(f"   ✗ Could not create database/user: {error}")
    return False

def update_pg_hba_conf(pg_dir):
    """Update pg_hba.conf to allow password authentication"""
    print("\n5. Checking pg_hba.conf configuration...")
    
    if isinstance(pg_dir, tuple):
        pg_type, pg_dir = pg_dir
    else:
        pg_type = 'unknown'
    
    # Find data directory
    data_dirs = [
        pg_dir / 'data',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'UsenetSync' / 'pgdata',
        Path('C:/ProgramData/PostgreSQL/14/data'),
    ]
    
    pg_hba_file = None
    for data_dir in data_dirs:
        if data_dir.exists():
            hba = data_dir / 'pg_hba.conf'
            if hba.exists():
                pg_hba_file = hba
                break
    
    if not pg_hba_file:
        print("   ✗ pg_hba.conf not found")
        return False
    
    print(f"   Found pg_hba.conf at: {pg_hba_file}")
    
    # Read current configuration
    with open(pg_hba_file, 'r') as f:
        lines = f.readlines()
    
    # Check if already configured
    has_usenet_config = any('usenet' in line for line in lines)
    
    if not has_usenet_config:
        print("   Adding UsenetSync configuration...")
        
        # Find the right place to insert (after IPv4 local connections comment)
        insert_index = -1
        for i, line in enumerate(lines):
            if 'IPv4 local connections:' in line:
                insert_index = i + 1
                break
        
        if insert_index == -1:
            # Just add at the end
            insert_index = len(lines)
        
        # Add configuration for usenet user
        new_lines = [
            "# UsenetSync configuration\n",
            "host    usenet          usenet          127.0.0.1/32            md5\n",
            "host    usenet          usenet          ::1/128                 md5\n",
        ]
        
        for i, new_line in enumerate(new_lines):
            lines.insert(insert_index + i, new_line)
        
        # Write back
        with open(pg_hba_file, 'w') as f:
            f.writelines(lines)
        
        print("   ✓ Updated pg_hba.conf")
        print("   ⚠ PostgreSQL needs to be restarted for changes to take effect")
        return True
    else:
        print("   ✓ pg_hba.conf already configured for UsenetSync")
        return True

def restart_postgresql(pg_dir):
    """Restart PostgreSQL to apply configuration changes"""
    print("\n6. Restarting PostgreSQL...")
    
    # Try Windows service first
    success, _, _ = run_command('net stop postgresql-x64-14', capture=False)
    if success:
        time.sleep(2)
        success, _, _ = run_command('net start postgresql-x64-14', capture=False)
        if success:
            print("   ✓ PostgreSQL service restarted")
            return True
    
    # Try portable PostgreSQL
    app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
    pid_file = app_dir / 'postgresql.pid'
    
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        
        # Stop the process
        run_command(f'taskkill /PID {pid} /F', capture=False)
        time.sleep(2)
        
        # Start it again
        if isinstance(pg_dir, tuple):
            _, pg_dir = pg_dir
        
        postgres_exe = pg_dir / 'bin' / 'postgres.exe'
        data_dir = app_dir / 'pgdata'
        
        if postgres_exe.exists() and data_dir.exists():
            log_file = app_dir / 'postgresql.log'
            subprocess.Popen(
                [str(postgres_exe), '-D', str(data_dir)],
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print("   ✓ PostgreSQL restarted")
            return True
    
    print("   ✗ Could not restart PostgreSQL")
    return False

def main():
    print("=" * 60)
    print("PostgreSQL Diagnostic Tool for UsenetSync")
    print("=" * 60)
    
    # Check if PostgreSQL is running
    is_running, pg_type = check_postgresql_service()
    
    # Find PostgreSQL installation
    installations = find_postgresql_installation()
    
    if not installations:
        print("\n✗ PostgreSQL is not installed. Please run the auto-install from Settings.")
        return 1
    
    # Use the first installation found
    pg_installation = installations[0]
    
    # Test connection
    connected = test_connection()
    
    if not connected:
        print("\n7. Attempting to fix the issue...")
        
        # Update pg_hba.conf
        update_pg_hba_conf(pg_installation)
        
        # Restart PostgreSQL if needed
        if is_running:
            restart_postgresql(pg_installation)
            time.sleep(3)
        
        # Try to fix authentication
        fix_postgresql_auth(pg_installation)
        
        # Test connection again
        print("\n8. Testing connection after fixes...")
        connected = test_connection()
    
    if connected:
        print("\n" + "=" * 60)
        print("✓ PostgreSQL is configured correctly!")
        print("=" * 60)
        print("\nConnection details:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: usenet")
        print("  User: usenet")
        print("  Password: usenetsync")
        
        # Save configuration
        config_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / '.usenetsync'
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / 'config.json'
        
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        config['database'] = {
            'type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'usenet',
            'user': 'usenet'
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✓ Configuration saved to {config_file}")
    else:
        print("\n" + "=" * 60)
        print("✗ Could not establish PostgreSQL connection")
        print("=" * 60)
        print("\nManual fix instructions:")
        print("1. Open Command Prompt as Administrator")
        print("2. Navigate to PostgreSQL bin directory")
        print("3. Run: psql -U postgres")
        print("4. Execute these commands:")
        print("   CREATE USER usenet WITH PASSWORD 'usenetsync';")
        print("   CREATE DATABASE usenet OWNER usenet;")
        print("   GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;")
        print("   \\q")
        
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)