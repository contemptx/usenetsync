#!/usr/bin/env python3
"""
GUI Development Environment Setup
Sets up complete development environment for UsenetSync GUI
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GUIDevSetup:
    """Setup GUI development environment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.gui_dir = self.project_root / "gui"
        self.resources_dir = self.gui_dir / "resources"
        
    def setup(self):
        """Complete setup process"""
        logger.info("Starting GUI development environment setup...")
        
        self.create_directories()
        self.install_dependencies()
        self.create_resource_files()
        self.create_launcher_scripts()
        self.validate_setup()
        
        logger.info("GUI development environment ready!")
        
    def create_directories(self):
        """Create required directory structure"""
        directories = [
            self.gui_dir,
            self.gui_dir / "components",
            self.gui_dir / "dialogs",
            self.gui_dir / "widgets",
            self.gui_dir / "themes",
            self.resources_dir,
            self.resources_dir / "icons",
            self.resources_dir / "images",
            self.gui_dir / "tests",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def install_dependencies(self):
        """Install GUI dependencies"""
        requirements_file = self.project_root / "requirements-gui.txt"
        
        if requirements_file.exists():
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            subprocess.run(cmd, check=True)
            logger.info("GUI dependencies installed")
        else:
            logger.warning("requirements-gui.txt not found")
    
    def create_resource_files(self):
        """Create resource files and icons"""
        # Create application icon (simple text-based for now)
        icon_content = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVFiFrZdPaBNBFMafSWM1/mvatGmTmkStVq2KeCgIXhQPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODBgwcPHjx48ODh
"""
        icon_file = self.resources_dir / "icons" / "usenetsync.ico"
        # Note: In production, use proper ICO files
        
        # Create themes configuration
        themes_config = self.gui_dir / "themes" / "themes.json"
        themes_config.write_text("""{
    "default": {
        "style": "clam",
        "colors": {
            "primary": "#0078D4",
            "secondary": "#666666",
            "success": "#0F7B0F",
            "warning": "#FF8C00",
            "error": "#D13438",
            "background": "#FFFFFF",
            "surface": "#F3F2F1"
        }
    },
    "dark": {
        "style": "equilux",
        "colors": {
            "primary": "#0078D4",
            "secondary": "#CCCCCC",
            "success": "#0F7B0F",
            "warning": "#FF8C00",
            "error": "#D13438",
            "background": "#202020",
            "surface": "#2D2D2D"
        }
    }
}""")
    
    def create_launcher_scripts(self):
        """Create launcher scripts"""
        # Windows launcher
        launcher_bat = self.project_root / "launch_gui.bat"
        launcher_bat.write_text("""@echo off
echo Starting UsenetSync GUI...
cd /d "%~dp0"
python gui/main_application.py
if errorlevel 1 (
    echo.
    echo Error starting GUI. Press any key to exit.
    pause >nul
)
""")
        
        # Cross-platform Python launcher
        launcher_py = self.project_root / "launch_gui.py"
        launcher_py.write_text("""#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set working directory
os.chdir(project_root)

try:
    from gui.main_application import MainApplication
    app = MainApplication()
    app.run()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please run: pip install -r requirements-gui.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)
""")
    
    def validate_setup(self):
        """Validate setup is complete"""
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")
        
        # Check tkinter availability
        try:
            import tkinter
            logger.info("✓ tkinter available")
        except ImportError:
            raise RuntimeError("tkinter not available")

if __name__ == "__main__":
    setup = GUIDevSetup()
    setup.setup()