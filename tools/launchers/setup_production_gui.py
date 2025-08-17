#!/usr/bin/env python3
"""
Production Setup Script for UsenetSync GUI
Validates all components and dependencies before running
"""

import sys
import os
import subprocess
import importlib
import sqlite3
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ProductionSetup:
    """Production setup and validation for UsenetSync GUI"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.errors = []
        self.warnings = []
        
    def validate_python_version(self):
        """Validate Python version"""
        logger.info("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
            
        logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
        
    def validate_required_modules(self):
        """Validate all required Python modules"""
        logger.info("Checking required Python modules...")
        
        required_modules = [
            ('tkinter', 'GUI framework'),
            ('sqlite3', 'Database support'),
            ('threading', 'Threading support'),
            ('ssl', 'SSL/TLS support'),
            ('hashlib', 'Cryptographic hashing'),
            ('json', 'JSON support'),
            ('pathlib', 'Path handling'),
            ('logging', 'Logging support')
        ]
        
        optional_modules = [
            ('psutil', 'System monitoring'),
            ('cryptography', 'Advanced cryptography')
        ]
        
        success = True
        
        for module_name, description in required_modules:
            try:
                importlib.import_module(module_name)
                logger.info(f"✓ {module_name} - {description}")
            except ImportError:
                self.errors.append(f"Required module missing: {module_name} ({description})")
                success = False
                
        for module_name, description in optional_modules:
            try:
                importlib.import_module(module_name)
                logger.info(f"✓ {module_name} - {description}")
            except ImportError:
                self.warnings.append(f"Optional module missing: {module_name} ({description})")
                
        return success
        
    def validate_backend_files(self):
        """Validate all required backend files are present"""
        logger.info("Checking backend files...")
        
        required_files = [
            'main.py',
            'enhanced_database_manager.py',
            'production_db_wrapper.py',
            'enhanced_security_system.py',
            'production_nntp_client.py',
            'segment_packing_system.py',
            'enhanced_upload_system.py',
            'versioned_core_index_system.py',
            'simplified_binary_index.py',
            'enhanced_download_system.py',
            'publishing_system.py',
            'user_management.py',
            'configuration_manager.py',
            'monitoring_system.py',
            'segment_retrieval_system.py',
            'upload_queue_manager.py'
        ]
        
        success = True
        
        for filename in required_files:
            filepath = self.script_dir / filename
            if filepath.exists():
                logger.info(f"✓ {filename}")
            else:
                self.errors.append(f"Required backend file missing: {filename}")
                success = False
                
        return success
        
    def validate_gui_files(self):
        """Validate all required GUI files are present"""
        logger.info("Checking GUI files...")
        
        required_gui_files = [
            'usenetsync_gui_main.py',
            'usenetsync_gui_user.py',
            'usenetsync_gui_folder.py',
            'usenetsync_gui_download.py'
        ]
        
        success = True
        
        for filename in required_gui_files:
            filepath = self.script_dir / filename
            if filepath.exists():
                logger.info(f"✓ {filename}")
            else:
                self.errors.append(f"Required GUI file missing: {filename}")
                success = False
                
        return success
        
    def validate_configuration(self):
        """Validate configuration file"""
        logger.info("Checking configuration...")
        
        config_file = self.script_dir / 'usenet_sync_config.json'
        
        if not config_file.exists():
            # Try to create from example
            example_file = self.script_dir / 'usenet_sync_config.json.example'
            if example_file.exists():
                logger.info("Creating configuration from example...")
                import shutil
                shutil.copy(example_file, config_file)
            else:
                self.errors.append("Configuration file missing: usenet_sync_config.json")
                return False
        
        try:
            with open(config_file) as f:
                config = json.load(f)
                
            # Validate structure
            if 'servers' not in config:
                self.errors.append("Configuration missing 'servers' section")
                return False
                
            if not config['servers']:
                self.warnings.append("No NNTP servers configured")
            else:
                for i, server in enumerate(config['servers']):
                    required_fields = ['hostname', 'port', 'username', 'password']
                    for field in required_fields:
                        if field not in server or not server[field]:
                            self.warnings.append(f"Server {i+1} missing {field}")
                            
            logger.info("✓ Configuration file valid")
            return True
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Configuration file invalid JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Configuration error: {e}")
            return False
            
    def create_directories(self):
        """Create required directories"""
        logger.info("Creating directories...")
        
        directories = [
            'data',
            'temp',
            'logs',
            'downloads'
        ]
        
        for dirname in directories:
            dirpath = self.script_dir / dirname
            try:
                dirpath.mkdir(exist_ok=True)
                logger.info(f"✓ {dirname}/")
            except Exception as e:
                self.errors.append(f"Failed to create directory {dirname}: {e}")
                return False
                
        return True
        
    def test_database_connection(self):
        """Test database connection"""
        logger.info("Testing database connection...")
        
        try:
            db_path = self.script_dir / 'data' / 'usenetsync.db'
            
            # Test basic SQLite connection
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")
            conn.close()
            
            logger.info("✓ Database connection successful")
            return True
            
        except Exception as e:
            self.errors.append(f"Database connection failed: {e}")
            return False
            
    def test_backend_import(self):
        """Test backend imports"""
        logger.info("Testing backend imports...")
        
        try:
            # Add current directory to path
            sys.path.insert(0, str(self.script_dir))
            
            # Test main backend import
            from main import UsenetSync
            logger.info("✓ Backend imports successful")
            return True
            
        except ImportError as e:
            self.errors.append(f"Backend import failed: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Backend initialization error: {e}")
            return False
            
    def test_gui_import(self):
        """Test GUI imports"""
        logger.info("Testing GUI imports...")
        
        try:
            # Test GUI imports
            import usenetsync_gui_main
            import usenetsync_gui_user
            import usenetsync_gui_folder
            import usenetsync_gui_download
            
            logger.info("✓ GUI imports successful")
            return True
            
        except ImportError as e:
            self.errors.append(f"GUI import failed: {e}")
            return False
        except Exception as e:
            self.errors.append(f"GUI initialization error: {e}")
            return False
            
    def run_validation(self):
        """Run complete validation"""
        logger.info("=" * 50)
        logger.info("UsenetSync Production Setup Validation")
        logger.info("=" * 50)
        
        validations = [
            self.validate_python_version,
            self.validate_required_modules,
            self.validate_backend_files,
            self.validate_gui_files,
            self.validate_configuration,
            self.create_directories,
            self.test_database_connection,
            self.test_backend_import,
            self.test_gui_import
        ]
        
        success = True
        
        for validation in validations:
            try:
                if not validation():
                    success = False
            except Exception as e:
                self.errors.append(f"Validation error in {validation.__name__}: {e}")
                success = False
        
        # Report results
        logger.info("=" * 50)
        logger.info("Validation Results")
        logger.info("=" * 50)
        
        if self.warnings:
            logger.warning("Warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
            logger.warning("")
        
        if self.errors:
            logger.error("Errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
            logger.error("")
            
            logger.error("❌ Validation FAILED")
            logger.error("Please fix the errors above before running the GUI")
            return False
        else:
            if self.warnings:
                logger.warning("✓ Validation PASSED with warnings")
                logger.warning("The GUI should work but some features may be limited")
            else:
                logger.info("✅ Validation PASSED")
                logger.info("All systems ready for production use")
            return True
            
    def launch_gui(self):
        """Launch the GUI application"""
        if not self.run_validation():
            return False
            
        logger.info("=" * 50)
        logger.info("Launching UsenetSync GUI...")
        logger.info("=" * 50)
        
        try:
            # Import and run GUI
            from usenetsync_gui_main import main
            main()
            return True
            
        except KeyboardInterrupt:
            logger.info("GUI closed by user")
            return True
        except Exception as e:
            logger.error(f"GUI failed to start: {e}")
            return False


def main():
    """Main entry point"""
    setup = ProductionSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--validate-only':
        # Just run validation
        success = setup.run_validation()
        sys.exit(0 if success else 1)
    else:
        # Run validation and launch GUI
        if setup.launch_gui():
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
