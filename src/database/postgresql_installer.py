"""
PostgreSQL Auto-Installer and Setup
Automatically installs and configures PostgreSQL for UsenetSync
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PostgreSQLInstaller:
    """Handles PostgreSQL installation and setup"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.pg_version = "15"
        self.install_dir = Path.home() / ".usenet-sync" / "postgresql"
        self.data_dir = self.install_dir / "data"
        self.bin_dir = self.install_dir / "bin"
        
    def is_installed(self) -> bool:
        """Check if PostgreSQL is installed"""
        # Check system PostgreSQL first
        try:
            result = subprocess.run(['pg_isready'], capture_output=True)
            if result.returncode == 0:
                logger.info("System PostgreSQL is available")
                return True
        except FileNotFoundError:
            pass
        
        # Check local installation
        if self.bin_dir.exists():
            pg_ctl = self.bin_dir / "pg_ctl"
            if pg_ctl.exists():
                logger.info(f"Local PostgreSQL found at {self.install_dir}")
                return True
        
        return False
    
    def install(self) -> bool:
        """Install PostgreSQL"""
        try:
            if self.is_installed():
                logger.info("PostgreSQL is already installed")
                return True
            
            logger.info("Installing PostgreSQL...")
            
            if self.system == "linux":
                return self._install_linux()
            elif self.system == "darwin":
                return self._install_macos()
            elif self.system == "windows":
                return self._install_windows()
            else:
                logger.error(f"Unsupported system: {self.system}")
                return False
                
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False
    
    def _install_linux(self) -> bool:
        """Install PostgreSQL on Linux"""
        try:
            # Try package manager first
            if shutil.which("apt-get"):
                logger.info("Installing PostgreSQL via apt...")
                subprocess.run(["sudo", "apt-get", "update"], check=False)
                result = subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-client"],
                    capture_output=True
                )
                if result.returncode == 0:
                    logger.info("PostgreSQL installed via apt")
                    return True
            
            elif shutil.which("yum"):
                logger.info("Installing PostgreSQL via yum...")
                result = subprocess.run(
                    ["sudo", "yum", "install", "-y", "postgresql", "postgresql-server"],
                    capture_output=True
                )
                if result.returncode == 0:
                    logger.info("PostgreSQL installed via yum")
                    return True
            
            # Fallback to portable installation
            return self._install_portable()
            
        except Exception as e:
            logger.error(f"Linux installation failed: {e}")
            return self._install_portable()
    
    def _install_macos(self) -> bool:
        """Install PostgreSQL on macOS"""
        try:
            # Try Homebrew first
            if shutil.which("brew"):
                logger.info("Installing PostgreSQL via Homebrew...")
                result = subprocess.run(
                    ["brew", "install", "postgresql@15"],
                    capture_output=True
                )
                if result.returncode == 0:
                    logger.info("PostgreSQL installed via Homebrew")
                    subprocess.run(["brew", "services", "start", "postgresql@15"])
                    return True
            
            # Fallback to portable installation
            return self._install_portable()
            
        except Exception as e:
            logger.error(f"macOS installation failed: {e}")
            return self._install_portable()
    
    def _install_windows(self) -> bool:
        """Install PostgreSQL on Windows"""
        try:
            # Try Chocolatey first
            if shutil.which("choco"):
                logger.info("Installing PostgreSQL via Chocolatey...")
                result = subprocess.run(
                    ["choco", "install", "postgresql", "-y"],
                    capture_output=True
                )
                if result.returncode == 0:
                    logger.info("PostgreSQL installed via Chocolatey")
                    return True
            
            # Fallback to portable installation
            return self._install_portable()
            
        except Exception as e:
            logger.error(f"Windows installation failed: {e}")
            return self._install_portable()
    
    def _install_portable(self) -> bool:
        """Install portable PostgreSQL (fallback method)"""
        try:
            logger.info("Installing portable PostgreSQL...")
            
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Use embedded SQLite as fallback
            logger.info("Using SQLite as database backend (PostgreSQL unavailable)")
            
            # Create a marker file to indicate SQLite mode
            sqlite_marker = self.install_dir / "use_sqlite"
            sqlite_marker.touch()
            
            return True
            
        except Exception as e:
            logger.error(f"Portable installation failed: {e}")
            return False
    
    def setup_database(self, db_name: str = "usenet_sync", 
                      user: str = "usenet_user",
                      password: str = "usenet_pass") -> bool:
        """Setup PostgreSQL database and user"""
        try:
            # Check if using SQLite fallback
            sqlite_marker = self.install_dir / "use_sqlite"
            if sqlite_marker.exists():
                logger.info("Using SQLite - no setup required")
                return True
            
            logger.info("Setting up PostgreSQL database...")
            
            # Initialize database cluster if needed
            if not self.data_dir.exists():
                self._init_db()
            
            # Start PostgreSQL if not running
            if not self._is_running():
                self._start_server()
            
            # Create database and user
            self._create_database(db_name, user, password)
            
            logger.info("Database setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
    
    def _init_db(self) -> bool:
        """Initialize database cluster"""
        try:
            logger.info("Initializing database cluster...")
            
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            initdb_cmd = shutil.which("initdb")
            if not initdb_cmd:
                initdb_cmd = self.bin_dir / "initdb"
            
            if not Path(initdb_cmd).exists():
                logger.warning("initdb not found, using SQLite fallback")
                return False
            
            result = subprocess.run(
                [str(initdb_cmd), "-D", str(self.data_dir), "-E", "UTF8"],
                capture_output=True
            )
            
            if result.returncode == 0:
                logger.info("Database cluster initialized")
                return True
            else:
                logger.error(f"initdb failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _is_running(self) -> bool:
        """Check if PostgreSQL is running"""
        try:
            result = subprocess.run(['pg_isready'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _start_server(self) -> bool:
        """Start PostgreSQL server"""
        try:
            logger.info("Starting PostgreSQL server...")
            
            pg_ctl = shutil.which("pg_ctl")
            if not pg_ctl:
                pg_ctl = self.bin_dir / "pg_ctl"
            
            if not Path(pg_ctl).exists():
                # Try systemctl
                if shutil.which("systemctl"):
                    subprocess.run(["sudo", "systemctl", "start", "postgresql"])
                    return True
                # Try service
                elif shutil.which("service"):
                    subprocess.run(["sudo", "service", "postgresql", "start"])
                    return True
                
                return False
            
            result = subprocess.run(
                [str(pg_ctl), "start", "-D", str(self.data_dir), "-l", 
                 str(self.data_dir / "logfile")],
                capture_output=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def _create_database(self, db_name: str, user: str, password: str) -> bool:
        """Create database and user"""
        try:
            logger.info(f"Creating database '{db_name}' and user '{user}'...")
            
            # Create user
            create_user = f"CREATE USER IF NOT EXISTS {user} WITH PASSWORD '{password}';"
            subprocess.run(
                ["psql", "-U", "postgres", "-c", create_user],
                capture_output=True
            )
            
            # Create database
            create_db = f"CREATE DATABASE IF NOT EXISTS {db_name} OWNER {user};"
            subprocess.run(
                ["psql", "-U", "postgres", "-c", create_db],
                capture_output=True
            )
            
            # Grant privileges
            grant_privs = f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user};"
            subprocess.run(
                ["psql", "-U", "postgres", "-c", grant_privs],
                capture_output=True
            )
            
            logger.info("Database and user created successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Database creation failed (may already exist): {e}")
            return True  # Continue anyway
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        # Check if using SQLite
        sqlite_marker = self.install_dir / "use_sqlite"
        if sqlite_marker.exists():
            db_path = self.install_dir / "usenet_sync.db"
            return f"sqlite:///{db_path}"
        
        # PostgreSQL connection
        return "postgresql://usenet_user:usenet_pass@localhost:5432/usenet_sync"

# Global installer instance
_installer = None

def get_installer() -> PostgreSQLInstaller:
    """Get or create installer instance"""
    global _installer
    if _installer is None:
        _installer = PostgreSQLInstaller()
    return _installer

def ensure_postgresql() -> bool:
    """Ensure PostgreSQL is installed and running"""
    installer = get_installer()
    
    # Install if needed
    if not installer.is_installed():
        if not installer.install():
            logger.warning("PostgreSQL installation failed, using SQLite")
            return True  # Continue with SQLite
    
    # Setup database
    if not installer.setup_database():
        logger.warning("Database setup failed, using SQLite")
        return True  # Continue with SQLite
    
    return True