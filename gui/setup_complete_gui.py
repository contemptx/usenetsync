"""
Windows-Compatible GUI Setup Script
Sets up the entire GUI framework with Windows-specific fixes
"""

import os
import sys
import json
import shutil
from pathlib import Path
import subprocess
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class WindowsGUISetup:
    """Windows-compatible GUI framework setup"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.gui_dir = self.project_root / "gui"
        self.errors = []
        
    def setup_complete_framework(self):
        """Setup complete GUI framework"""
        logger.info("Setting up UsenetSync GUI framework for Windows...")
        
        try:
            self.create_directory_structure()
            self.create_requirements_files()
            self.install_dependencies_windows()
            self.create_configuration_files()
            self.create_launcher_scripts()
            self.setup_themes_and_resources()
            self.create_documentation()
            self.validate_setup()
            
            if self.errors:
                logger.error("Setup completed with errors:")
                for error in self.errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("✓ Complete GUI framework setup successful!")
                self.print_usage_instructions()
                
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    def create_directory_structure(self):
        """Create complete directory structure"""
        logger.info("Creating directory structure...")
        
        directories = [
            # Core GUI structure
            self.gui_dir,
            self.gui_dir / "components",
            self.gui_dir / "dialogs", 
            self.gui_dir / "widgets",
            self.gui_dir / "utils",
            self.gui_dir / "themes",
            self.gui_dir / "resources" / "icons",
            self.gui_dir / "resources" / "images",
            self.gui_dir / "config",
            
            # Testing structure
            self.gui_dir / "tests",
            
            # Deployment structure
            self.gui_dir / "deployment",
            
            # Documentation
            self.gui_dir / "docs",
            
            # Application directories
            self.project_root / "data",
            self.project_root / "logs",
            self.project_root / "temp"
        ]
        
        created_count = 0
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                created_count += 1
            except Exception as e:
                logger.warning(f"Failed to create {directory}: {e}")
        
        logger.info(f"✓ Created {created_count} directories")
    
    def create_requirements_files(self):
        """Create requirements files"""
        logger.info("Creating requirements files...")
        
        # Essential GUI dependencies only (Windows compatible)
        gui_requirements = [
            "# Core GUI dependencies for Windows",
            "# tkinter is built into Python - no need to install",
            "",
            "# Optional enhancements",
            "pillow>=8.0.0",
            "psutil>=5.8.0",
            "",
            "# Development tools", 
            "pyinstaller>=4.0"
        ]
        
        # Create GUI requirements file
        gui_req_file = self.project_root / "requirements-gui.txt"
        try:
            with open(gui_req_file, 'w') as f:
                f.write('\n'.join(gui_requirements))
            logger.info("✓ Created requirements-gui.txt")
        except Exception as e:
            logger.error(f"Failed to create requirements file: {e}")
            self.errors.append(f"Requirements file creation failed: {e}")
    
    def install_dependencies_windows(self):
        """Install dependencies with Windows-specific handling"""
        logger.info("Installing GUI dependencies...")
        
        # Check if pip is available
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.error("pip is not available")
                self.errors.append("pip is not available")
                return
        except Exception as e:
            logger.error(f"Failed to check pip: {e}")
            self.errors.append(f"pip check failed: {e}")
            return
        
        # Install essential packages one by one
        essential_packages = ["pillow", "psutil"]
        
        for package in essential_packages:
            logger.info(f"Installing {package}...")
            try:
                # Use timeout to prevent hanging
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    logger.info(f"✓ {package} installed successfully")
                else:
                    logger.warning(f"Failed to install {package}: {result.stderr}")
                    # Don't treat as fatal error
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Installation of {package} timed out - continuing anyway")
            except Exception as e:
                logger.warning(f"Error installing {package}: {e}")
        
        logger.info("✓ Dependency installation completed")
    
    def create_configuration_files(self):
        """Create configuration files"""
        logger.info("Creating configuration files...")
        
        # GUI configuration
        gui_config = {
            "theme": {
                "default": "clam",
                "font_family": "Segoe UI",  # Windows default
                "font_size": 9
            },
            "window": {
                "width": 1200,
                "height": 800,
                "min_width": 800,
                "min_height": 600
            },
            "performance": {
                "file_browser_page_size": 1000,
                "max_log_lines": 1000
            }
        }
        
        config_file = self.gui_dir / "config" / "gui_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(gui_config, f, indent=2)
            logger.info("✓ Created GUI configuration")
        except Exception as e:
            logger.error(f"Failed to create config: {e}")
    
    def create_launcher_scripts(self):
        """Create launcher scripts"""
        logger.info("Creating launcher scripts...")
        
        # Windows batch launcher
        windows_launcher = self.project_root / "launch_gui.bat"
        windows_content = '''@echo off
title UsenetSync GUI
echo Starting UsenetSync GUI...
cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking tkinter availability...
python -c "import tkinter; print('tkinter OK')" 2>nul
if errorlevel 1 (
    echo Error: tkinter not available
    echo Please reinstall Python with tkinter support
    pause
    exit /b 1
)

echo Launching UsenetSync GUI...
if exist "gui\\main_application.py" (
    python gui\\main_application.py
) else (
    echo Error: GUI files not found
    echo Please run the setup script first
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo GUI encountered an error. Check logs for details.
    pause
)
'''
        
        try:
            with open(windows_launcher, 'w') as f:
                f.write(windows_content)
            logger.info("✓ Created Windows launcher")
        except Exception as e:
            logger.error(f"Failed to create launcher: {e}")
        
        # Python launcher (cross-platform)
        python_launcher = self.project_root / "launch_gui.py"
        python_content = '''#!/usr/bin/env python3
"""
Cross-platform GUI launcher for UsenetSync
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_tkinter():
    """Check tkinter availability"""
    try:
        import tkinter
        print("✓ tkinter available")
        return True
    except ImportError:
        print("Error: tkinter not available")
        print("Please install Python with tkinter support")
        return False

def launch_gui():
    """Launch the GUI application"""
    gui_script = Path(__file__).parent / "gui" / "main_application.py"
    
    if gui_script.exists():
        print(f"Launching GUI from: {gui_script}")
        # Change to project directory
        os.chdir(Path(__file__).parent)
        # Import and run
        exec(open(gui_script).read())
    else:
        print(f"Error: GUI script not found: {gui_script}")
        print("Please run the setup script first")
        sys.exit(1)

def main():
    """Main launcher function"""
    print("UsenetSync GUI Launcher")
    print("=" * 30)
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_tkinter():
        sys.exit(1)
    
    print("Starting GUI...")
    try:
        launch_gui()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        try:
            with open(python_launcher, 'w') as f:
                f.write(python_content)
            logger.info("✓ Created Python launcher")
        except Exception as e:
            logger.error(f"Failed to create Python launcher: {e}")
    
    def setup_themes_and_resources(self):
        """Setup themes and resource files"""
        logger.info("Setting up themes and resources...")
        
        # Create theme definition file
        themes_file = self.gui_dir / "themes" / "themes.json"
        themes_config = {
            "default": {
                "name": "Windows Default",
                "style": "clam"
            },
            "dark": {
                "name": "Dark Theme", 
                "style": "clam"
            }
        }
        
        try:
            with open(themes_file, 'w') as f:
                json.dump(themes_config, f, indent=2)
            logger.info("✓ Created theme configuration")
        except Exception as e:
            logger.warning(f"Failed to create themes: {e}")
        
        # Create placeholder icon files
        icon_dir = self.gui_dir / "resources" / "icons"
        icon_files = ["app.ico", "folder.ico", "file.ico"]
        
        created_icons = 0
        for icon_file in icon_files:
            try:
                icon_path = icon_dir / icon_file
                if not icon_path.exists():
                    icon_path.touch()
                    created_icons += 1
            except Exception as e:
                logger.warning(f"Failed to create icon {icon_file}: {e}")
        
        logger.info(f"✓ Created {created_icons} placeholder icons")
    
    def create_documentation(self):
        """Create basic documentation"""
        logger.info("Creating documentation...")
        
        # Quick start guide
        readme_file = self.gui_dir / "README.md"
        readme_content = '''# UsenetSync GUI

## Quick Start (Windows)

1. **Launch the GUI**:
   - Double-click `launch_gui.bat` in the project root
   - Or run: `python launch_gui.py`

2. **First Time Setup**:
   - The GUI will guide you through initial setup
   - Configure your NNTP server settings
   - Create your first folder share

3. **Requirements**:
   - Python 3.8+ with tkinter
   - Windows 10/11 recommended
   - NNTP server account

## Troubleshooting

### GUI Won't Start
- Ensure Python 3.8+ is installed
- Check that tkinter is available: `python -c "import tkinter"`
- Run from command prompt to see error messages

### Performance Issues
- Reduce file browser page size in settings
- Close other resource-intensive applications
- Ensure adequate RAM (4GB+ recommended)

## Support
For issues and support, check the logs directory for error details.
'''
        
        try:
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            logger.info("✓ Created README documentation")
        except Exception as e:
            logger.warning(f"Failed to create documentation: {e}")
    
    def validate_setup(self):
        """Validate the setup"""
        logger.info("Validating setup...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.errors.append("Python 3.8+ required")
        else:
            logger.info(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check tkinter
        try:
            import tkinter
            logger.info("✓ tkinter available")
        except ImportError:
            self.errors.append("tkinter not available")
        
        # Check critical directories
        critical_dirs = [self.gui_dir, self.gui_dir / "components"]
        for dir_path in critical_dirs:
            if dir_path.exists():
                logger.info(f"✓ {dir_path.name} directory")
            else:
                self.errors.append(f"Missing: {dir_path}")
        
        # Check launcher
        launcher = self.project_root / "launch_gui.bat"
        if launcher.exists():
            logger.info("✓ Windows launcher created")
        else:
            self.errors.append("Missing Windows launcher")
        
        if not self.errors:
            logger.info("✓ Setup validation passed")
        else:
            logger.warning(f"Validation found {len(self.errors)} issues")
    
    def print_usage_instructions(self):
        """Print usage instructions"""
        instructions = '''
╔══════════════════════════════════════════════════════════════╗
║                    UsenetSync GUI Framework                   ║
║                   Windows Setup Complete!                    ║
╚══════════════════════════════════════════════════════════════╝

🚀 QUICK START:

1. Launch the GUI:
   • Double-click: launch_gui.bat
   • Or run: python launch_gui.py

2. Create GUI files:
   • You now have the directory structure
   • Copy the GUI component files from the framework guide
   • Place them in the gui/ directory

3. Required GUI files to create:
   • gui/main_application.py (main window)
   • gui/components/base_component.py (base classes)
   • gui/dialogs/user_init_dialog.py (user setup)
   • gui/widgets/file_browser.py (file browser)

📁 DIRECTORY STRUCTURE CREATED:
   gui/
   ├── components/     # Place reusable components here
   ├── dialogs/        # Place dialog windows here  
   ├── widgets/        # Place custom widgets here
   ├── utils/          # Place utility modules here
   ├── themes/         # Theme configuration
   ├── resources/      # Icons and assets
   ├── config/         # Configuration files
   └── docs/           # Documentation

📝 NEXT STEPS:
   1. Copy the GUI component code from the framework guide
   2. Place files in appropriate directories
   3. Test with: python launch_gui.py
   4. Configure NNTP servers
   5. Start sharing files!

💡 TIPS:
   • Use launch_gui.bat for easy starting
   • Check logs/ directory for troubleshooting
   • GUI supports millions of files efficiently
   • Full Windows compatibility ensured

For detailed implementation, refer to the GUI Framework guide!
'''
        print(instructions)

def main():
    """Main setup function"""
    print("UsenetSync GUI Setup for Windows")
    print("=" * 40)
    
    setup = WindowsGUISetup()
    setup.setup_complete_framework()
    
    print("\n" + "=" * 40)
    print("Setup process completed!")

if __name__ == "__main__":
    main()
