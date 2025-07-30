@echo off
REM UsenetSync GUI Launcher for Windows
REM Simple production launcher

title UsenetSync GUI - Production

REM Set UTF-8 code page
chcp 65001 >nul

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo.
echo =========================================
echo    UsenetSync GUI - Production Launch
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Launch using the correct script name
if exist "run_gui.py" (
    python run_gui.py
) else if exist "production_launcher.py" (
    python production_launcher.py
) else (
    echo ERROR: No launcher script found
    echo.
    echo Make sure one of these files exists:
    echo - run_gui.py
    echo - production_launcher.py
    pause
    exit /b 1
)

REM Check exit code
if errorlevel 1 (
    echo.
    echo =========================================
    echo   Application Error
    echo =========================================
    echo.
    echo Check the error message above.
    echo Common solutions:
    echo - Configure NNTP server settings in usenet_sync_config.json
    echo - Ensure all Python dependencies are installed
    echo - Check that all files are present
    echo.
    pause
)

exit /b 0
