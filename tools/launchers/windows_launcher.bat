@echo off
REM UsenetSync GUI Launcher for Windows
REM Production-ready launcher with complete validation

title UsenetSync GUI - Production

REM Set UTF-8 code page to handle international characters
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

REM Display Python version
echo Python version:
python --version
echo.

REM Run production setup and validation
echo Running production validation...
echo.

python setup_production_gui.py --validate-only
if errorlevel 1 (
    echo.
    echo =========================================
    echo   VALIDATION FAILED
    echo =========================================
    echo.
    echo The system validation failed. Please check the errors above.
    echo Common issues:
    echo - Missing backend files
    echo - Configuration not set up
    echo - Required Python modules missing
    echo - Database connection issues
    echo.
    echo Fix the issues and try again.
    pause
    exit /b 1
)

echo.
echo =========================================
echo   VALIDATION PASSED - Starting GUI
echo =========================================
echo.

REM Launch the production GUI
python setup_production_gui.py

REM Check if the GUI exited with an error
if errorlevel 1 (
    echo.
    echo =========================================
    echo   GUI exited with an error
    echo =========================================
    echo.
    echo Check the console output above for error details.
    echo.
    echo Common solutions:
    echo - Check NNTP server configuration
    echo - Verify all dependencies are installed
    echo - Check log files in the logs directory
    echo - Ensure database is accessible
    echo.
    pause
) else (
    echo.
    echo GUI closed normally.
)

REM Keep window open if run directly (not from command line)
if "%1"=="" pause

exit /b 0
