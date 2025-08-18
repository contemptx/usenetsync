@echo off
echo ============================================================
echo Building UsenetSync Installer with Python Backend
echo ============================================================
echo.

REM Step 1: Install Python dependencies
echo Step 1: Installing Python dependencies...
pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Failed to install dependencies
    exit /b 1
)

REM Step 2: Build Python backend executable
echo.
echo Step 2: Building Python backend executable...
cd src
python -m PyInstaller --clean --onefile --name usenetsync-backend --distpath ../usenet-sync-app/src-tauri/resources cli.py
if errorlevel 1 (
    echo Failed to build Python backend
    exit /b 1
)
cd ..

REM Step 3: Build Tauri application
echo.
echo Step 3: Building Tauri application...
cd usenet-sync-app
call npm install
call npm run tauri build
if errorlevel 1 (
    echo Failed to build Tauri application
    exit /b 1
)
cd ..

echo.
echo ============================================================
echo Build complete! Installer located in:
echo usenet-sync-app\src-tauri\target\release\bundle\
echo ============================================================
pause