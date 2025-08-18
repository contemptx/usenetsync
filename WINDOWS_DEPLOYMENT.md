# 🚀 UsenetSync Windows Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Building from Source](#building-from-source)
4. [Creating Windows Installer](#creating-windows-installer)
5. [Installation](#installation)
6. [Running UsenetSync](#running-usenetsync)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for Usenet access

### Required Software for Building
1. **Node.js** (v18 or later)
   - Download: https://nodejs.org/
   - Verify: `node --version`

2. **Rust** (latest stable)
   - Download: https://rustup.rs/
   - Run: `rustup default stable`
   - Add MSVC build tools during installation

3. **Git**
   - Download: https://git-scm.com/download/win
   - Verify: `git --version`

4. **Visual Studio Build Tools 2022**
   - Download: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
   - Install "Desktop development with C++" workload

5. **Python 3.11+** (for backend)
   - Download: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   - Verify: `python --version`

6. **PostgreSQL 15+** (optional, auto-installed by installer)
   - Download: https://www.postgresql.org/download/windows/
   - Default port: 5432

---

## Development Setup

### 1. Clone Repository
```powershell
# Open PowerShell or Command Prompt
git clone https://github.com/contemptx/usenetsync.git
cd usenetsync
```

### 2. Install Frontend Dependencies
```powershell
cd usenet-sync-app
npm install
```

### 3. Install Python Dependencies
```powershell
# From project root
pip install -r requirements.txt
```

### 4. Install Rust Dependencies
```powershell
cd usenet-sync-app/src-tauri
cargo build
```

---

## Building from Source

### Quick Build (Development)
```powershell
# From usenet-sync-app directory
npm run tauri dev
```
This launches the app in development mode with hot-reload.

### Production Build
```powershell
# From usenet-sync-app directory

# Step 1: Build frontend
npm run build

# Step 2: Build Tauri app
npm run tauri build
```

The built executable will be in:
- `usenet-sync-app/src-tauri/target/release/UsenetSync.exe`

### Build Installers
```powershell
# Builds both MSI and NSIS installers
npm run tauri build -- --bundles msi,nsis
```

Output locations:
- MSI: `usenet-sync-app/src-tauri/target/release/bundle/msi/`
- NSIS: `usenet-sync-app/src-tauri/target/release/bundle/nsis/`

---

## Creating Windows Installer

### Using Pre-built Installer (Recommended)
1. Download latest release from GitHub Releases
2. Choose either:
   - `UsenetSync-1.0.0-x64.msi` (MSI installer)
   - `UsenetSync-1.0.0-Setup.exe` (NSIS installer)

### Building Installer from Source

#### MSI Installer (Windows Installer)
```powershell
# Requires WiX Toolset v3
# Download: https://wixtoolset.org/releases/

cd usenet-sync-app
npm run tauri build -- --bundles msi
```

#### NSIS Installer (Nullsoft)
```powershell
# Requires NSIS
# Download: https://nsis.sourceforge.io/Download

cd usenet-sync-app
npm run tauri build -- --bundles nsis
```

---

## Installation

### Method 1: Using Installer (Recommended)

1. **Run the installer** as Administrator
   - Right-click → "Run as administrator"

2. **Follow installation wizard**:
   - Accept license agreement
   - Choose installation directory (default: `C:\Program Files\UsenetSync`)
   - Select components:
     - ✅ UsenetSync Core (required)
     - ✅ PostgreSQL (required, skipped if already installed)
     - ✅ Python Runtime (required)
     - ☐ Desktop Shortcut (optional)
     - ☐ Start Menu Shortcuts (optional)

3. **Wait for installation** to complete
   - PostgreSQL setup (if needed)
   - Python dependencies installation
   - TurboActivate license system setup

4. **Launch UsenetSync**
   - Check "Launch UsenetSync" on final screen
   - Or use desktop/start menu shortcut

### Method 2: Manual Installation

1. **Create installation directory**:
```powershell
mkdir "C:\Program Files\UsenetSync"
```

2. **Copy files**:
```powershell
# Copy executable
copy usenet-sync-app\src-tauri\target\release\UsenetSync.exe "C:\Program Files\UsenetSync\"

# Copy Python backend
xcopy /E /I src "C:\Program Files\UsenetSync\backend"

# Copy TurboActivate files
mkdir "C:\Program Files\UsenetSync\turboactivate"
copy usenet-sync-app\src-tauri\turboactivate\*.* "C:\Program Files\UsenetSync\turboactivate\"
```

3. **Install PostgreSQL** (if not installed):
```powershell
# Download PostgreSQL installer
# Run with these parameters:
postgresql-15.5-1-windows-x64.exe --mode unattended --superpassword postgres --servicename PostgreSQL
```

4. **Setup database**:
```powershell
psql -U postgres -c "CREATE DATABASE usenet_sync;"
psql -U postgres -c "CREATE USER usenet_user WITH PASSWORD 'usenet_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE usenet_sync TO usenet_user;"
```

5. **Install Python dependencies**:
```powershell
cd "C:\Program Files\UsenetSync\backend"
pip install -r requirements.txt
```

6. **Create desktop shortcut** (optional):
   - Right-click on desktop → New → Shortcut
   - Location: `C:\Program Files\UsenetSync\UsenetSync.exe`
   - Name: UsenetSync

---

## Running UsenetSync

### First Launch

1. **Start the application**:
   - Double-click UsenetSync desktop icon
   - Or run from Start Menu
   - Or execute: `"C:\Program Files\UsenetSync\UsenetSync.exe"`

2. **License Activation**:
   - Enter your license key when prompted
   - Or start 30-day trial
   - Hardware ID is automatically generated

3. **Initial Configuration**:
   - Add Usenet server credentials
   - Configure bandwidth limits (optional)
   - Set download directory

### Command Line Usage

```powershell
# Run with custom config
UsenetSync.exe --config "C:\Users\%USERNAME%\AppData\Roaming\UsenetSync\config.json"

# Run in debug mode
UsenetSync.exe --debug

# Check version
UsenetSync.exe --version
```

### Python CLI Direct Access

```powershell
# Navigate to backend directory
cd "C:\Program Files\UsenetSync\backend"

# Create share
python src\cli.py create-share --files file1.txt file2.pdf --type public

# Download share
python src\cli.py download-share --share-id SHARE123 --destination C:\Downloads

# List shares
python src\cli.py list-shares

# Test server connection
python src\cli.py test-connection --server news.example.com --port 563 --ssl
```

---

## Configuration

### Configuration File Location
```
C:\Users\%USERNAME%\AppData\Roaming\UsenetSync\config.json
```

### Database Location
```
C:\ProgramData\UsenetSync\database\
```

### Logs Location
```
C:\Users\%USERNAME%\AppData\Roaming\UsenetSync\logs\
```

### Sample Configuration
```json
{
  "servers": [
    {
      "hostname": "news.example.com",
      "port": 563,
      "username": "your_username",
      "password": "your_password",
      "ssl": true,
      "maxConnections": 10
    }
  ],
  "bandwidth": {
    "uploadLimit": 0,
    "downloadLimit": 0,
    "enabled": false
  },
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM"
  },
  "paths": {
    "downloads": "C:\\Users\\%USERNAME%\\Downloads\\UsenetSync",
    "temp": "C:\\Users\\%USERNAME%\\AppData\\Local\\Temp\\UsenetSync"
  }
}
```

### Environment Variables
```powershell
# Set custom config path
setx USENETSYNC_CONFIG "D:\MyConfig\usenet.json"

# Set custom data directory
setx USENETSYNC_DATA "D:\UsenetData"

# Enable debug logging
setx USENETSYNC_DEBUG "1"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Won't Start
```powershell
# Check if port 5432 (PostgreSQL) is available
netstat -an | findstr :5432

# Check if PostgreSQL service is running
sc query PostgreSQL

# Start PostgreSQL if stopped
net start PostgreSQL

# Check Windows Event Viewer for errors
eventvwr.msc
```

#### 2. Database Connection Failed
```powershell
# Test PostgreSQL connection
psql -U postgres -d usenet_sync -c "SELECT version();"

# Reset database
psql -U postgres -c "DROP DATABASE IF EXISTS usenet_sync;"
psql -U postgres -c "CREATE DATABASE usenet_sync;"

# Check PostgreSQL logs
type "C:\Program Files\PostgreSQL\15\data\log\postgresql-*.log"
```

#### 3. License Activation Issues
```powershell
# Clear license cache
del "C:\ProgramData\UsenetSync\license.dat"

# Run as administrator for first activation
runas /user:Administrator "C:\Program Files\UsenetSync\UsenetSync.exe"

# Check hardware ID
"C:\Program Files\UsenetSync\UsenetSync.exe" --hardware-id
```

#### 4. Python Backend Errors
```powershell
# Reinstall Python dependencies
cd "C:\Program Files\UsenetSync\backend"
pip install --upgrade -r requirements.txt

# Test Python backend directly
python src\cli.py --help

# Check Python version
python --version  # Should be 3.11 or higher
```

#### 5. Permission Errors
```powershell
# Grant full permissions to UsenetSync directories
icacls "C:\Program Files\UsenetSync" /grant %USERNAME%:F /T
icacls "C:\ProgramData\UsenetSync" /grant %USERNAME%:F /T
icacls "%APPDATA%\UsenetSync" /grant %USERNAME%:F /T
```

#### 6. Firewall/Antivirus Issues
- Add UsenetSync.exe to Windows Defender exclusions
- Add firewall rules for:
  - UsenetSync.exe (outbound)
  - PostgreSQL port 5432 (local only)
  - Usenet server ports (typically 119 or 563)

```powershell
# Add firewall rule
netsh advfirewall firewall add rule name="UsenetSync" dir=out action=allow program="C:\Program Files\UsenetSync\UsenetSync.exe"
```

#### 7. WebView2 Runtime Missing
```powershell
# Download and install WebView2 Runtime
# https://developer.microsoft.com/en-us/microsoft-edge/webview2/

# Or use the bootstrapper (included in NSIS installer)
WebView2Bootstrapper.exe /silent /install
```

### Debug Mode
```powershell
# Run with verbose logging
set RUST_LOG=debug
set USENETSYNC_DEBUG=1
"C:\Program Files\UsenetSync\UsenetSync.exe"

# Check debug logs
type "%APPDATA%\UsenetSync\logs\debug.log"
```

### Clean Reinstall
```powershell
# 1. Uninstall via Control Panel or
"C:\Program Files\UsenetSync\Uninstall.exe"

# 2. Remove leftover files
rmdir /S /Q "C:\Program Files\UsenetSync"
rmdir /S /Q "%APPDATA%\UsenetSync"
rmdir /S /Q "C:\ProgramData\UsenetSync"

# 3. Remove registry entries
reg delete "HKLM\SOFTWARE\UsenetSync" /f
reg delete "HKCU\SOFTWARE\UsenetSync" /f

# 4. Reinstall fresh
```

---

## Performance Optimization

### Windows-Specific Optimizations

1. **Disable Windows Defender scanning for UsenetSync folders**:
```powershell
Add-MpPreference -ExclusionPath "C:\Program Files\UsenetSync"
Add-MpPreference -ExclusionPath "%APPDATA%\UsenetSync"
Add-MpPreference -ExclusionProcess "UsenetSync.exe"
```

2. **Increase TCP connection limit**:
```powershell
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global chimney=enabled
```

3. **Optimize PostgreSQL for Windows**:
Edit `C:\Program Files\PostgreSQL\15\data\postgresql.conf`:
```conf
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
effective_cache_size = 1GB
```

4. **Set process priority**:
```powershell
# Set high priority
wmic process where name="UsenetSync.exe" CALL setpriority "high priority"
```

---

## Security Considerations

### Best Practices

1. **Run with standard user privileges** (after initial setup)
2. **Keep PostgreSQL password secure**
3. **Enable Windows Firewall**
4. **Use encrypted connections (SSL) for Usenet servers**
5. **Regular backups of configuration and database**

### Backup Script
```powershell
# Create backup script: backup_usenetsync.ps1
$date = Get-Date -Format "yyyy-MM-dd"
$backupDir = "C:\Backups\UsenetSync\$date"

New-Item -ItemType Directory -Force -Path $backupDir

# Backup config
Copy-Item "$env:APPDATA\UsenetSync\*" -Destination "$backupDir\config" -Recurse

# Backup database
pg_dump -U postgres usenet_sync > "$backupDir\database.sql"

# Compress backup
Compress-Archive -Path $backupDir -DestinationPath "C:\Backups\UsenetSync_$date.zip"
```

---

## Support

### Getting Help
- **GitHub Issues**: https://github.com/contemptx/usenetsync/issues
- **Documentation**: https://github.com/contemptx/usenetsync/wiki
- **Logs**: Check `%APPDATA%\UsenetSync\logs\` for detailed error information

### Reporting Issues
When reporting issues, please include:
1. UsenetSync version (`UsenetSync.exe --version`)
2. Windows version (`winver`)
3. Error messages from logs
4. Steps to reproduce the issue

---

## Quick Start Commands

```powershell
# Clone and build
git clone https://github.com/contemptx/usenetsync.git
cd usenetsync\usenet-sync-app
npm install
npm run tauri build

# Install
cd src-tauri\target\release\bundle\nsis
.\UsenetSync-1.0.0-Setup.exe

# Run
"C:\Program Files\UsenetSync\UsenetSync.exe"
```

---

**Congratulations! UsenetSync is now installed and ready to use on Windows!** 🎉