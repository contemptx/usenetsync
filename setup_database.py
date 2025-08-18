#!/usr/bin/env python3
"""
PostgreSQL Database Setup for UsenetSync
Automatically creates database, user, and tables
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import platform
import time

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'usenetsync',
    'user': 'usenet',
    'password': 'usenet_secure_2024'
}

def check_postgresql_installed():
    """Check if PostgreSQL is installed"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PostgreSQL is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ PostgreSQL is not installed")
    return False

def install_postgresql():
    """Provide instructions or attempt to install PostgreSQL"""
    system = platform.system()
    
    if system == "Windows":
        print("\nTo install PostgreSQL on Windows:")
        print("1. Download from: https://www.postgresql.org/download/windows/")
        print("2. Run the installer")
        print("3. Remember the superuser password you set")
        print("\nOr use Chocolatey: choco install postgresql")
        
    elif system == "Darwin":  # macOS
        print("\nTo install PostgreSQL on macOS:")
        print("Using Homebrew: brew install postgresql")
        print("Then start it: brew services start postgresql")
        
    elif system == "Linux":
        print("\nInstalling PostgreSQL on Linux...")
        try:
            # Try to install using apt (Ubuntu/Debian)
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'postgresql', 'postgresql-contrib'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
            print("✓ PostgreSQL installed successfully")
            return True
        except:
            print("\nTo install PostgreSQL manually:")
            print("Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib")
            print("RHEL/CentOS: sudo yum install postgresql-server postgresql-contrib")
            print("Arch: sudo pacman -S postgresql")
    
    return False

def check_postgresql_running():
    """Check if PostgreSQL service is running"""
    try:
        # Try to connect to PostgreSQL on default port
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
        )
        conn.close()
        print("✓ PostgreSQL is running")
        return True
    except:
        print("✗ PostgreSQL is not running or not accessible")
        
        # Try to start it
        system = platform.system()
        if system == "Linux":
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
                time.sleep(2)
                print("✓ Started PostgreSQL service")
                return True
            except:
                pass
        elif system == "Darwin":
            try:
                subprocess.run(['brew', 'services', 'start', 'postgresql'], check=True)
                time.sleep(2)
                print("✓ Started PostgreSQL service")
                return True
            except:
                pass
        
        print("\nPlease start PostgreSQL manually:")
        print("Linux: sudo systemctl start postgresql")
        print("macOS: brew services start postgresql")
        print("Windows: Start from Services or pg_ctl start")
        return False

def create_database_and_user():
    """Create the UsenetSync database and user"""
    try:
        # Connect as superuser (postgres)
        print("\nConnecting to PostgreSQL as superuser...")
        
        # Try different authentication methods
        for password in [os.environ.get('POSTGRES_PASSWORD'), 'postgres', '', None]:
            try:
                if password is None:
                    # Try peer authentication (Linux)
                    conn = psycopg2.connect(
                        database='postgres',
                        user='postgres'
                    )
                else:
                    conn = psycopg2.connect(
                        host='localhost',
                        port=5432,
                        database='postgres',
                        user='postgres',
                        password=password
                    )
                break
            except:
                continue
        else:
            print("✗ Could not connect as postgres user")
            print("\nPlease set POSTGRES_PASSWORD environment variable:")
            print("export POSTGRES_PASSWORD=your_postgres_password")
            return False
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if not exists
        print(f"Creating user '{DB_CONFIG['user']}'...")
        cursor.execute(
            "SELECT 1 FROM pg_user WHERE usename = %s",
            (DB_CONFIG['user'],)
        )
        if not cursor.fetchone():
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_CONFIG['user'])
                ),
                (DB_CONFIG['password'],)
            )
            print(f"✓ Created user '{DB_CONFIG['user']}'")
        else:
            # Update password
            cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_CONFIG['user'])
                ),
                (DB_CONFIG['password'],)
            )
            print(f"✓ User '{DB_CONFIG['user']}' already exists, updated password")
        
        # Create database if not exists
        print(f"Creating database '{DB_CONFIG['database']}'...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_CONFIG['database'],)
        )
        if not cursor.fetchone():
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_CONFIG['database']),
                    sql.Identifier(DB_CONFIG['user'])
                )
            )
            print(f"✓ Created database '{DB_CONFIG['database']}'")
        else:
            print(f"✓ Database '{DB_CONFIG['database']}' already exists")
        
        # Grant all privileges
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(DB_CONFIG['database']),
                sql.Identifier(DB_CONFIG['user'])
            )
        )
        print(f"✓ Granted privileges to user '{DB_CONFIG['user']}'")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creating database/user: {e}")
        return False

def create_tables():
    """Create all required tables"""
    try:
        print("\nCreating tables...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create shares table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shares (
                id TEXT PRIMARY KEY,
                share_id TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                name TEXT,
                size BIGINT,
                file_count INTEGER,
                folder_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                password_hash TEXT,
                metadata JSONB
            )
        """)
        print("✓ Created 'shares' table")
        
        # Create files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                share_id TEXT REFERENCES shares(share_id) ON DELETE CASCADE,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size BIGINT,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        print("✓ Created 'files' table")
        
        # Create servers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                hostname TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                password TEXT,
                use_ssl BOOLEAN DEFAULT TRUE,
                max_connections INTEGER DEFAULT 10,
                priority INTEGER DEFAULT 1,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_tested TIMESTAMP,
                last_status TEXT
            )
        """)
        print("✓ Created 'servers' table")
        
        # Create uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                share_id TEXT REFERENCES shares(share_id),
                file_path TEXT NOT NULL,
                file_size BIGINT,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        print("✓ Created 'uploads' table")
        
        # Create downloads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                share_id TEXT,
                destination TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        print("✓ Created 'downloads' table")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_share_id ON shares(share_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_share_id ON files(share_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
        print("✓ Created indexes")
        
        # Create migration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                status TEXT DEFAULT 'success'
            )
        """)
        print("✓ Created 'schema_migrations' table")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ All tables created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def test_connection():
    """Test the database connection"""
    try:
        print("\nTesting database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✓ Connected successfully to PostgreSQL")
        print(f"  Version: {version}")
        
        # Count tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"  Tables: {table_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("UsenetSync PostgreSQL Database Setup")
    print("=" * 60)
    
    # Step 1: Check PostgreSQL installation
    if not check_postgresql_installed():
        if not install_postgresql():
            print("\n⚠ Please install PostgreSQL and run this script again")
            return False
    
    # Step 2: Check if PostgreSQL is running
    if not check_postgresql_running():
        print("\n⚠ Please start PostgreSQL and run this script again")
        return False
    
    # Step 3: Create database and user
    if not create_database_and_user():
        print("\n⚠ Failed to create database/user")
        print("You may need to run this script with sudo or as postgres user")
        return False
    
    # Step 4: Create tables
    if not create_tables():
        print("\n⚠ Failed to create tables")
        return False
    
    # Step 5: Test connection
    if not test_connection():
        print("\n⚠ Connection test failed")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Database setup completed successfully!")
    print("=" * 60)
    print("\nDatabase Configuration:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")
    print(f"  Password: {DB_CONFIG['password']}")
    print("\nYou can now run UsenetSync!")
    
    # Save configuration
    config_file = os.path.join(os.path.dirname(__file__), 'db_config.json')
    import json
    with open(config_file, 'w') as f:
        json.dump(DB_CONFIG, f, indent=2)
    print(f"\nConfiguration saved to: {config_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)