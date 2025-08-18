# UsenetSync Setup Instructions

## Prerequisites
- Node.js 18+ and npm
- Python 3.8+ (Python 3.11+ recommended)
- Rust (for Tauri)
- Git

## Initial Setup

### 1. Clone the Repository
```bash
git clone https://github.com/contemptx/usenetsync.git
cd usenetsync
```

### 2. Install Node.js Dependencies
```bash
cd usenet-sync-app
npm install
```

### 3. Install Python Dependencies (CRITICAL)

The Python backend requires several dependencies, most importantly `pynntp` for Usenet server connections.

#### Windows:
```cmd
# Run from the project root directory
setup.bat
```

#### Linux/Mac:
```bash
# Run from the project root directory
./setup.sh
```

#### Manual Installation:
If the setup scripts don't work, install manually:
```bash
pip install -r requirements.txt
# or
pip install --user -r requirements.txt
```

**IMPORTANT**: Make sure `pynntp` is installed:
```bash
pip install pynntp
# Test it:
python3 -c "from nntp import NNTPClient; print('pynntp is working')"
```

## Running the Application

### Development Mode
```bash
cd usenet-sync-app
npm run tauri dev
```

### Build for Production
```bash
cd usenet-sync-app
npm run tauri build
```

## Troubleshooting

### Python Module Not Found Errors
If you see errors like `ModuleNotFoundError: No module named 'upload'`:
1. Make sure you're in the correct directory
2. Run the setup script again
3. Verify Python can find the modules:
   ```bash
   cd src
   python3 -c "import upload.enhanced_upload; print('Modules OK')"
   ```

### NNTP Connection Issues
If Usenet server connections fail:
1. Verify `pynntp` is installed: `pip list | grep pynntp`
2. Test the import: `python3 -c "from nntp import NNTPClient"`
3. Check your server credentials and network connection

### Important Note About NNTP
- **DO NOT** use `nntplib` - it's discontinued in Python 3.11+
- **USE** `pynntp` package which provides the `nntp` module
- Install: `pip install pynntp`
- Import: `from nntp import NNTPClient` (NOT `from pynntp`)

## Platform-Specific Notes

### Windows
- Use `python` instead of `python3`
- Run `setup.bat` for automatic setup
- May need to run as Administrator

### Linux
- May need `--break-system-packages` flag for pip on newer distributions
- Use `./setup.sh` for automatic setup

### macOS
- Ensure you have Xcode Command Line Tools installed
- Use `./setup.sh` for automatic setup