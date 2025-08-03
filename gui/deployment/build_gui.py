"""
GUI Build and Distribution Script
Creates standalone executable for Windows
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

class GUIBuilder:
    """Build standalone GUI application"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.gui_dir = self.project_root / "gui"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        
    def build_executable(self):
        """Build standalone executable using PyInstaller"""
        print("Building UsenetSync GUI executable...")
        
        # Ensure PyInstaller is installed
        self.ensure_pyinstaller()
        
        # Create spec file
        spec_file = self.create_spec_file()
        
        # Build executable
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm", 
            str(spec_file)
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        if result.returncode != 0:
            raise RuntimeError("PyInstaller build failed")
        
        # Post-build processing
        self.post_build_processing()
        
        print("✓ Build completed successfully!")
        print(f"Executable location: {self.dist_dir / 'UsenetSync'}")
    
    def ensure_pyinstaller(self):
        """Ensure PyInstaller is installed"""
        try:
            import PyInstaller
        except ImportError:
            print("Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    def create_spec_file(self):
        """Create PyInstaller spec file"""
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Project paths
project_root = Path(r'{self.project_root}')
gui_dir = project_root / 'gui'
src_dir = project_root / 'src'

# Data files to include
datas = [
    (str(gui_dir / 'resources'), 'resources'),
    (str(project_root / 'usenet_sync_config.json.example'), '.'),
]

# Hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'sqlite3',
    'json',
    'threading',
    'queue',
    'pathlib',
    'datetime',
    'time',
    'os',
    'sys',
    'logging',
    'traceback',
    'subprocess',
    'webbrowser',
]

block_cipher = None

a = Analysis(
    [str(gui_dir / 'main_application.py')],
    pathex=[str(project_root), str(src_dir), str(gui_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UsenetSync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windows app, not console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(gui_dir / 'resources' / 'icons' / 'usenetsync.ico') if (gui_dir / 'resources' / 'icons' / 'usenetsync.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UsenetSync',
)
"""
        
        spec_file = self.project_root / "UsenetSync.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        return spec_file
    
    def post_build_processing(self):
        """Post-build processing"""
        exe_dir = self.dist_dir / "UsenetSync"
        
        # Copy additional files
        additional_files = [
            ("README.md", "README.txt"),
            ("LICENSE", "LICENSE.txt"),
            ("usenet_sync_config.json.example", "usenet_sync_config.json.example"),
        ]
        
        for src_name, dst_name in additional_files:
            src_file = self.project_root / src_name
            if src_file.exists():
                shutil.copy2(src_file, exe_dir / dst_name)
        
        # Create directories
        dirs_to_create = ["data", "logs", "temp"]
        for dir_name in dirs_to_create:
            (exe_dir / dir_name).mkdir(exist_ok=True)
        
        # Create batch launcher
        launcher_content = """@echo off
echo Starting UsenetSync...
cd /d "%~dp0"
UsenetSync.exe
if errorlevel 1 (
    echo.
    echo UsenetSync encountered an error.
    echo Check the logs directory for more information.
    pause
)
"""
        
        with open(exe_dir / "Launch_UsenetSync.bat", 'w') as f:
            f.write(launcher_content)
        
        print(f"✓ Executable created in: {exe_dir}")
    
    def create_installer(self):
        """Create Windows installer using NSIS"""
        print("Creating Windows installer...")
        
        # Check if NSIS is available
        nsis_path = self.find_nsis()
        if not nsis_path:
            print("NSIS not found. Skipping installer creation.")
            print("Download NSIS from: https://nsis.sourceforge.io/")
            return
        
        # Create installer script
        installer_script = self.create_nsis_script()
        
        # Compile installer
        cmd = [str(nsis_path), str(installer_script)]
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ Installer created successfully!")
        else:
            print("✗ Installer creation failed")
    
    def find_nsis(self):
        """Find NSIS installation"""
        possible_paths = [
            Path("C:/Program Files (x86)/NSIS/makensis.exe"),
            Path("C:/Program Files/NSIS/makensis.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def create_nsis_script(self):
        """Create NSIS installer script"""
        version = "2.0.0"  # TODO: Get from version file
        
        script_content = f'''
!define APPNAME "UsenetSync"
!define COMPANYNAME "UsenetSync Project"
!define DESCRIPTION "Secure Usenet File Synchronization"
!define VERSIONMAJOR 2
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define VERSION "{version}"

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${{APPNAME}}"
Name "${{APPNAME}}"
Icon "{self.gui_dir}\\resources\\icons\\usenetsync.ico"
OutFile "{self.dist_dir}\\UsenetSync_Setup.exe"

!include LogicLib.nsh

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    
    # Copy files
    File /r "{self.dist_dir}\\UsenetSync\\*"
    
    # Create shortcuts
    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\UsenetSync.exe"
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\UsenetSync.exe"
    
    # Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}} - ${{DESCRIPTION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayVersion" "${{VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    
    # Uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    # Remove files
    RMDir /r "$INSTDIR"
    
    # Remove shortcuts
    Delete "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk"
    RMDir "$SMPROGRAMS\\${{APPNAME}}"
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
SectionEnd
'''
        
        script_file = self.project_root / "installer.nsi"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        return script_file
    
    def create_portable_zip(self):
        """Create portable ZIP distribution"""
        print("Creating portable ZIP distribution...")
        
        exe_dir = self.dist_dir / "UsenetSync"
        zip_file = self.dist_dir / "UsenetSync_Portable.zip"
        
        if not exe_dir.exists():
            print("Build executable first!")
            return
        
        # Create ZIP
        shutil.make_archive(
            str(zip_file.with_suffix('')),
            'zip',
            str(exe_dir.parent),
            str(exe_dir.name)
        )
        
        print(f"✓ Portable ZIP created: {zip_file}")
    
    def clean_build(self):
        """Clean build artifacts"""
        print("Cleaning build artifacts...")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        
        # Remove spec file
        spec_file = self.project_root / "UsenetSync.spec"
        if spec_file.exists():
            spec_file.unlink()
        
        print("✓ Build artifacts cleaned")

def main():
    """Main build script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build UsenetSync GUI")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--exe", action="store_true", help="Build executable")
    parser.add_argument("--installer", action="store_true", help="Create installer")
    parser.add_argument("--portable", action="store_true", help="Create portable ZIP")
    parser.add_argument("--all", action="store_true", help="Build everything")
    
    args = parser.parse_args()
    
    builder = GUIBuilder()
    
    if args.clean:
        builder.clean_build()
    
    if args.exe or args.all:
        builder.build_executable()
    
    if args.installer or args.all:
        builder.create_installer()
    
    if args.portable or args.all:
        builder.create_portable_zip()
    
    if not any([args.clean, args.exe, args.installer, args.portable, args.all]):
        print("No action specified. Use --help for options.")

if __name__ == "__main__":
    main()