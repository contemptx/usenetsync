"""
Automatic PostgreSQL Setup for Windows
Handles downloading, installing, and configuring PostgreSQL automatically
"""

import os
import sys
import subprocess
import platform
import tempfile
import urllib.request
import zipfile
import json
import time
import shutil
import winreg
import ctypes
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PostgreSQLAutoSetup:
    """Automatically install and configure PostgreSQL on Windows"""
    
    # PostgreSQL portable version URLs (no admin rights required)
    POSTGRES_PORTABLE_URL = "https://get.enterprisedb.com/postgresql/postgresql-14.9-1-windows-x64-binaries.zip"
    POSTGRES_VERSION = "14.9"
    
    def __init__(self):
        self.app_dir = self._get_app_directory()
        self.postgres_dir = self.app_dir / "postgresql"
        self.data_dir = self.app_dir / "pgdata"
        self.config_file = self.app_dir / "pg_config.json"
        self.is_windows = platform.system() == "Windows"
        
    def _get_app_directory(self) -> Path:
        """Get the application directory"""
        if platform.system() == "Windows":
            app_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'UsenetSync'
        else:
            app_dir = Path.home() / '.usenetsync'
        
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    
    def is_admin(self) -> bool:
        """Check if running with admin privileges on Windows"""
        if not self.is_windows:
            return os.geteuid() == 0
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def check_existing_postgres(self) -> Optional[Dict[str, Any]]:
        """Check if PostgreSQL is already installed"""
        # Check if our portable PostgreSQL exists
        if self.postgres_dir.exists() and (self.postgres_dir / "bin" / "postgres.exe").exists():
            return {
                "type": "portable",
                "path": str(self.postgres_dir),
                "version": self.POSTGRES_VERSION,
                "data_dir": str(self.data_dir)
            }
        
        # Check system PostgreSQL
        if self.is_windows:
            # Check common installation paths
            common_paths = [
                Path("C:/Program Files/PostgreSQL"),
                Path("C:/PostgreSQL"),
            ]
            
            for base_path in common_paths:
                if base_path.exists():
                    for version_dir in base_path.iterdir():
                        pg_exe = version_dir / "bin" / "postgres.exe"
                        if pg_exe.exists():
                            return {
                                "type": "system",
                                "path": str(version_dir),
                                "version": version_dir.name,
                                "data_dir": None
                            }
        
        # Check if postgres is in PATH
        try:
            result = subprocess.run(["postgres", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                return {
                    "type": "system",
                    "path": "PATH",
                    "version": version,
                    "data_dir": None
                }
        except:
            pass
        
        return None
    
    def download_postgres(self, progress_callback=None) -> bool:
        """Download PostgreSQL portable binaries"""
        try:
            logger.info(f"Downloading PostgreSQL {self.POSTGRES_VERSION} portable...")
            
            # Create temp directory for download
            temp_dir = Path(tempfile.mkdtemp())
            zip_path = temp_dir / "postgresql.zip"
            
            # Download with progress
            def download_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(downloaded * 100 / total_size, 100)
                if progress_callback:
                    progress_callback(percent, f"Downloading PostgreSQL... {percent:.1f}%")
                else:
                    # Write to stderr to avoid corrupting JSON output
                    sys.stderr.write(f"\rDownloading PostgreSQL... {percent:.1f}%")
                    sys.stderr.flush()
            
            urllib.request.urlretrieve(self.POSTGRES_PORTABLE_URL, zip_path, download_hook)
            if not progress_callback:
                sys.stderr.write("\n")  # New line after progress
                sys.stderr.flush()
            
            logger.info("Extracting PostgreSQL...")
            if progress_callback:
                progress_callback(50, "Extracting PostgreSQL...")
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the extracted directory (usually named 'pgsql')
            extracted_dir = None
            for item in temp_dir.iterdir():
                if item.is_dir() and item.name.startswith('pgsql'):
                    extracted_dir = item
                    break
            
            if not extracted_dir:
                raise Exception("Could not find extracted PostgreSQL directory")
            
            # Move to final location
            if self.postgres_dir.exists():
                shutil.rmtree(self.postgres_dir)
            
            shutil.move(str(extracted_dir), str(self.postgres_dir))
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"PostgreSQL installed to {self.postgres_dir}")
            if progress_callback:
                progress_callback(100, "PostgreSQL installation complete")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download PostgreSQL: {e}")
            return False
    
    def initialize_database(self, password: str = "usenetsync") -> bool:
        """Initialize PostgreSQL database"""
        try:
            if not self.postgres_dir.exists():
                logger.error("PostgreSQL not installed")
                return False
            
            initdb_exe = self.postgres_dir / "bin" / "initdb.exe"
            if not initdb_exe.exists():
                logger.error(f"initdb.exe not found at {initdb_exe}")
                return False
            
            # Create data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Initializing database at {self.data_dir}...")
            
            # Initialize database
            result = subprocess.run([
                str(initdb_exe),
                "-D", str(self.data_dir),
                "-U", "postgres",
                "--auth-local=trust",
                "--auth-host=md5",
                "-E", "UTF8",
                "--locale=C"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Database initialization failed: {result.stderr}")
                return False
            
            # Update postgresql.conf for better defaults
            conf_file = self.data_dir / "postgresql.conf"
            if conf_file.exists():
                with open(conf_file, 'a') as f:
                    f.write("\n# UsenetSync Configuration\n")
                    f.write("listen_addresses = 'localhost'\n")
                    f.write("port = 5432\n")
                    f.write("max_connections = 20\n")
                    f.write("shared_buffers = 128MB\n")
                    f.write("logging_collector = off\n")  # Disable logging to reduce overhead
            
            # Save configuration
            config = {
                "postgres_dir": str(self.postgres_dir),
                "data_dir": str(self.data_dir),
                "version": self.POSTGRES_VERSION,
                "password": password,
                "port": 5432,
                "initialized": True
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Database initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def start_postgres(self) -> bool:
        """Start PostgreSQL server"""
        try:
            if not self.data_dir.exists():
                logger.error("Database not initialized")
                return False
            
            postgres_exe = self.postgres_dir / "bin" / "postgres.exe"
            if not postgres_exe.exists():
                logger.error(f"postgres.exe not found at {postgres_exe}")
                return False
            
            # Check if already running
            if self.is_postgres_running():
                logger.info("PostgreSQL is already running")
                return True
            
            logger.info("Starting PostgreSQL server...")
            
            # Start PostgreSQL in background
            # Using subprocess.Popen to run in background
            log_file = self.app_dir / "postgresql.log"
            
            with open(log_file, 'w') as log:
                process = subprocess.Popen([
                    str(postgres_exe),
                    "-D", str(self.data_dir)
                ], stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0)
            
            # Save PID for later management
            pid_file = self.app_dir / "postgresql.pid"
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if server started successfully
            if self.is_postgres_running():
                logger.info("PostgreSQL server started successfully")
                return True
            else:
                logger.error("PostgreSQL server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL: {e}")
            return False
    
    def stop_postgres(self) -> bool:
        """Stop PostgreSQL server"""
        try:
            pid_file = self.app_dir / "postgresql.pid"
            
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                if self.is_windows:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, 15)  # SIGTERM
                
                pid_file.unlink()
                logger.info("PostgreSQL server stopped")
                return True
            
            # Try pg_ctl stop as fallback
            pg_ctl = self.postgres_dir / "bin" / "pg_ctl.exe"
            if pg_ctl.exists():
                result = subprocess.run([
                    str(pg_ctl),
                    "stop",
                    "-D", str(self.data_dir),
                    "-m", "fast"
                ], capture_output=True, text=True)
                
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop PostgreSQL: {e}")
            return False
    
    def is_postgres_running(self) -> bool:
        """Check if PostgreSQL is running"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                database="postgres",
                connect_timeout=3
            )
            conn.close()
            return True
        except:
            return False
    
    def create_usenet_database(self) -> bool:
        """Create the UsenetSync database and user"""
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect as postgres user
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create user (ignore if exists)
            try:
                cursor.execute("CREATE USER usenet WITH PASSWORD 'usenetsync';")
            except psycopg2.errors.DuplicateObject:
                pass
            
            # Create database (ignore if exists)
            try:
                cursor.execute("CREATE DATABASE usenet OWNER usenet;")
            except psycopg2.errors.DuplicateDatabase:
                pass
            
            # Grant privileges
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;")
            
            cursor.close()
            conn.close()
            
            logger.info("UsenetSync database created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    def full_setup(self, progress_callback=None) -> Tuple[bool, str]:
        """Perform full PostgreSQL setup"""
        try:
            # Check if already setup
            existing = self.check_existing_postgres()
            if existing:
                if existing["type"] == "portable":
                    # Our portable installation exists
                    if not self.is_postgres_running():
                        if self.start_postgres():
                            self.create_usenet_database()
                            return True, "PostgreSQL is ready (existing installation)"
                    else:
                        return True, "PostgreSQL is already running"
                else:
                    # System PostgreSQL exists
                    if self.is_postgres_running():
                        self.create_usenet_database()
                        return True, f"Using system PostgreSQL {existing['version']}"
            
            # Download PostgreSQL
            if progress_callback:
                progress_callback(10, "Downloading PostgreSQL...")
            
            if not self.download_postgres(progress_callback):
                return False, "Failed to download PostgreSQL"
            
            # Initialize database
            if progress_callback:
                progress_callback(70, "Initializing database...")
            
            if not self.initialize_database():
                return False, "Failed to initialize database"
            
            # Start PostgreSQL
            if progress_callback:
                progress_callback(85, "Starting PostgreSQL server...")
            
            if not self.start_postgres():
                return False, "Failed to start PostgreSQL server"
            
            # Create UsenetSync database
            if progress_callback:
                progress_callback(95, "Creating UsenetSync database...")
            
            if not self.create_usenet_database():
                return False, "Failed to create UsenetSync database"
            
            if progress_callback:
                progress_callback(100, "Setup complete!")
            
            return True, "PostgreSQL setup completed successfully"
            
        except Exception as e:
            return False, f"Setup failed: {e}"
    
    def ensure_running(self) -> bool:
        """Ensure PostgreSQL is running (start if needed)"""
        if self.is_postgres_running():
            return True
        
        if self.postgres_dir.exists() and self.data_dir.exists():
            return self.start_postgres()
        
        # Need full setup
        success, message = self.full_setup()
        return success


# Windows Service Manager (optional - for running as Windows service)
class PostgreSQLWindowsService:
    """Manage PostgreSQL as a Windows service"""
    
    SERVICE_NAME = "UsenetSyncPostgreSQL"
    SERVICE_DISPLAY = "UsenetSync PostgreSQL Database"
    
    @staticmethod
    def install_service(postgres_dir: Path, data_dir: Path) -> bool:
        """Install PostgreSQL as Windows service (requires admin)"""
        try:
            pg_ctl = postgres_dir / "bin" / "pg_ctl.exe"
            
            result = subprocess.run([
                str(pg_ctl),
                "register",
                "-N", PostgreSQLWindowsService.SERVICE_NAME,
                "-D", str(data_dir),
                "-S", "auto",  # Auto start
                "-w"  # Wait for completion
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to install service: {e}")
            return False
    
    @staticmethod
    def uninstall_service(postgres_dir: Path) -> bool:
        """Uninstall PostgreSQL Windows service"""
        try:
            pg_ctl = postgres_dir / "bin" / "pg_ctl.exe"
            
            result = subprocess.run([
                str(pg_ctl),
                "unregister",
                "-N", PostgreSQLWindowsService.SERVICE_NAME
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to uninstall service: {e}")
            return False
    
    @staticmethod
    def start_service() -> bool:
        """Start the PostgreSQL service"""
        try:
            result = subprocess.run([
                "net", "start", PostgreSQLWindowsService.SERVICE_NAME
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    @staticmethod
    def stop_service() -> bool:
        """Stop the PostgreSQL service"""
        try:
            result = subprocess.run([
                "net", "stop", PostgreSQLWindowsService.SERVICE_NAME
            ], capture_output=True, text=True, shell=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False


# Auto-setup function for easy integration
def ensure_postgresql_windows() -> Tuple[bool, str]:
    """Ensure PostgreSQL is installed and running on Windows"""
    if platform.system() != "Windows":
        return True, "Not Windows, skipping auto-setup"
    
    setup = PostgreSQLAutoSetup()
    return setup.full_setup()


if __name__ == "__main__":
    # Test the setup
    logging.basicConfig(level=logging.INFO)
    
    print("PostgreSQL Auto-Setup for Windows")
    print("-" * 40)
    
    setup = PostgreSQLAutoSetup()
    
    # Check existing installation
    existing = setup.check_existing_postgres()
    if existing:
        print(f"Found existing PostgreSQL: {existing}")
    
    # Perform full setup
    success, message = setup.full_setup()
    print(f"\nSetup result: {message}")
    
    if success:
        print("\nPostgreSQL is ready to use!")
        print("Connection details:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: usenet")
        print("  User: usenet")
        print("  Password: usenetsync")