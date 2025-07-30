# UsenetSync GUI Setup Guide

## Overview

This guide will help you set up and run the UsenetSync GUI application on Windows. The GUI provides a complete interface for managing your Usenet file synchronization with full support for millions of files.

## Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
   - Verify installation: Open Command Prompt and run `python --version`

2. **Usenet Server Account**
   - You need access to an NNTP server (news server)
   - Most Usenet providers offer accounts with SSL support
   - Required information: hostname, port, username, password

### System Requirements

- **Operating System**: Windows 10/11 (64-bit recommended)
- **Memory**: 4GB RAM minimum, 8GB+ recommended for large file operations
- **Storage**: 2GB free space minimum for application and temporary files
- **Network**: Broadband internet connection for Usenet access

## Installation Steps

### Step 1: Download UsenetSync

1. Download all UsenetSync files to a folder (e.g., `C:\UsenetSync\`)
2. Ensure all these files are present:
   ```
   UsenetSync/
   ├── usenetsync_gui_main.py          # Main GUI application
   ├── usenetsync_gui_user.py          # User initialization dialog
   ├── usenetsync_gui_folder.py        # Folder details panel
   ├── usenetsync_gui_download.py      # Download dialog
   ├── main.py                         # Backend integration
   ├── launch_gui.bat                  # Windows launcher
   ├── usenet_sync_config.json         # Configuration file
   └── [other backend files...]
   ```

### Step 2: Install Python Dependencies

1. Open Command Prompt as Administrator
2. Navigate to the UsenetSync folder:
   ```cmd
   cd C:\UsenetSync
   ```
3. Install required packages:
   ```cmd
   pip install -r requirements.txt
   ```

### Step 3: Configure NNTP Server

1. Copy the example configuration:
   ```cmd
   copy usenet_sync_config.json.example usenet_sync_config.json
   ```

2. Edit `usenet_sync_config.json` with your NNTP server details:
   ```json
   {
     "servers": [
       {
         "name": "Primary Server",
         "hostname": "news.your-provider.com",
         "port": 563,
         "username": "your_username",
         "password": "your_password",
         "use_ssl": true,
         "max_connections": 4,
         "enabled": true,
         "priority": 1,
         "posting_group": "alt.binaries.test"
       }
     ],
     "storage": {
       "database_path": "data/usenetsync.db",
       "temp_directory": "temp",
       "log_directory": "logs"
     }
   }
   ```

### Step 4: Launch the GUI

**Option A: Double-click `launch_gui.bat`**
- This is the recommended method
- Automatically checks dependencies and sets up directories
- Provides helpful error messages

**Option B: Command Line**
```cmd
cd C:\UsenetSync
python usenetsync_gui_main.py
```

## First Time Setup

### 1. Initialize Your User Profile

When you first run the GUI:

1. Click "Initialize User" or press `Ctrl+I`
2. Enter a display name (optional but recommended)
3. Click "Initialize User Profile"
4. **IMPORTANT**: Your User ID will be generated and displayed
   - This ID is permanent and cannot be changed
   - Copy it to a safe place for reference
   - Your private keys remain on this system only

### 2. Index Your First Folder

1. Click "Index Folder" or press `Ctrl+F`
2. Select a folder containing files you want to share
3. Wait for indexing to complete
4. The folder will appear in the navigation tree

### 3. Test the Connection

1. Go to Tools → Connection Test
2. Verify your NNTP server connection works
3. Check Tools → System Status for overall health

## Using the GUI

### Main Interface Components

#### Navigation Tree (Left Panel)
- Shows all indexed folders
- ✓ = Ready for sharing
- ⚠ = Has issues (check segments tab)
- Right-click for context menu

#### Details Panel (Right Panel)
- **Overview**: Folder statistics and activity
- **Access Control**: Manage sharing permissions
- **Segments**: Upload status and management
- **Files**: Browse folder contents (supports millions of files)
- **Actions**: Folder operations and maintenance

### Key Operations

#### Sharing Files
1. Select folder in navigation tree
2. Go to Access Control tab
3. Choose share type:
   - **Public**: Anyone with link can download
   - **Private**: Only authorized User IDs
   - **Protected**: Password required
4. Click "Update Access Settings"
5. Click "Publish Share" to create access string

#### Downloading Shares
1. Click "Download" or press `Ctrl+D`
2. Paste the access string you received
3. Click "Verify Share"
4. Select files/folders to download
5. Choose download options
6. Click "Start Download"

#### Managing Large File Collections
- The GUI uses virtual scrolling for millions of files
- Use the search feature to find specific files
- Segment-level control for upload management
- Background operations don't block the interface

### Security Features

#### User ID Management
- **One-time generation**: Cannot be regenerated
- **No export capability**: Private keys stay secure
- **Permanent identity**: Used for all private shares

#### Access Control
- **Per-folder permissions**: Each folder has independent access
- **User authorization**: Add/remove users for private shares
- **Password protection**: Additional security layer

## Troubleshooting

### Common Issues

#### "Python not found" Error
**Solution**: Install Python and ensure it's added to PATH
1. Download Python from python.org
2. Run installer with "Add Python to PATH" checked
3. Restart Command Prompt and try again

#### "tkinter module not found"
**Solution**: Install complete Python or tkinter separately
```cmd
pip install tk
```

#### GUI Won't Start
**Checks**:
1. Verify all GUI files are present
2. Check Python version: `python --version`
3. Check dependencies: `pip list`
4. Look for error messages in console

#### NNTP Connection Failed
**Checks**:
1. Verify server hostname and port
2. Check username/password
3. Ensure SSL settings match server requirements
4. Test with Tools → Connection Test

#### Slow Performance with Large Folders
**Solutions**:
1. Index during off-peak hours
2. Use selective download for large shares
3. Increase memory if possible
4. Check segment upload status

### Error Messages

#### "Backend not initialized"
- Wait for initialization to complete
- Check NNTP configuration
- Verify database permissions

#### "User not initialized"
- Run user initialization first
- Check if user profile was created successfully

#### "Folder not found"
- Refresh folder tree (F5)
- Re-index folder if necessary
- Check original folder still exists

### Performance Tips

#### For Large File Collections
- Index folders during off-peak network hours
- Use segment-level upload control
- Enable "Skip existing" for resume capability
- Monitor memory usage during operations

#### Network Optimization
- Adjust max_connections based on server limits
- Use multiple servers for redundancy
- Monitor upload/download speeds

## Configuration Reference

### Server Configuration Options

```json
{
  "name": "Server Name",           // Display name
  "hostname": "news.server.com",   // NNTP server address
  "port": 563,                     // Port (563 for SSL, 119 for plain)
  "username": "your_user",         // Account username
  "password": "your_pass",         // Account password
  "use_ssl": true,                 // Enable SSL/TLS
  "max_connections": 4,            // Concurrent connections
  "enabled": true,                 // Enable this server
  "priority": 1,                   // Server priority (1 = highest)
  "posting_group": "alt.binaries.test"  // Newsgroup for posts
}
```

### Storage Configuration

```json
{
  "database_path": "data/usenetsync.db",  // SQLite database location
  "temp_directory": "temp",               // Temporary files
  "log_directory": "logs"                 // Application logs
}
```

## Advanced Features

### Multiple Server Support
- Configure multiple NNTP servers for redundancy
- Automatic failover and load balancing
- Priority-based server selection

### Segment Management
- View all segments with upload status
- Upload specific failed segments only
- Verify segment integrity
- Queue management for large uploads

### Virtual File Browser
- Handles millions of files efficiently
- Search and filter capabilities
- Lazy loading for responsive interface
- Checkbox selection for downloads

### Background Operations
- Non-blocking uploads and downloads
- Progress tracking and statistics
- Automatic retry logic
- Pause/resume capability

## Security Considerations

### Private Key Security
- Private keys never leave your system
- No export or backup capability by design
- Secure local storage only

### Network Security
- All connections use SSL/TLS when available
- End-to-end encryption for shared content
- Zero-knowledge architecture

### Access Control
- Folder-level permissions
- User-based authorization
- Password protection options
- Audit logging

## Support and Updates

### Getting Help
1. Check this documentation first
2. Look at log files in the `logs` directory
3. Use Tools → System Status for diagnostics
4. Check the UsenetSync community forums

### Keeping Updated
- Monitor for new releases
- Backup configuration before updates
- Test with small folders first

### Reporting Issues
When reporting problems, include:
- Python version (`python --version`)
- Error messages from console
- Log files from `logs` directory
- Steps to reproduce the issue

---

## Quick Reference

### Keyboard Shortcuts
- `Ctrl+I`: Initialize User
- `Ctrl+F`: Index Folder
- `Ctrl+P`: Publish Share
- `Ctrl+D`: Download Share
- `F5`: Refresh All
- `Space`: Toggle checkbox in trees
- `Ctrl+A`: Select all (in trees)
- `Ctrl+N`: Select none (in trees)

### Status Indicators
- ✓ - Successfully uploaded/verified
- ⚠ - Failed or missing segments
- 🔒 - Encrypted content
- 📁 - Folder with subfolders
- `[PUB]` - Public share
- `[PRV]` - Private share
- `[PWD]` - Password-protected

### File Size Limits
- No practical limit on number of files
- Individual file size limited by available memory
- Automatic segmentation for large files
- Virtual scrolling for responsive interface

---

*This GUI provides full access to UsenetSync's production-grade capabilities with a user-friendly interface designed for both casual users and power users managing millions of files.*
