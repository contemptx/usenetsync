@echo off
echo ============================================================
echo UsenetSync PostgreSQL Database Setup for Windows
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Install required Python packages
echo Installing required Python packages...
pip install psycopg2-binary

REM Run the setup script
echo.
echo Running database setup...
python setup_database.py

if errorlevel 1 (
    echo.
    echo Database setup failed!
    echo.
    echo If PostgreSQL is not installed:
    echo 1. Download from: https://www.postgresql.org/download/windows/
    echo 2. Run the installer
    echo 3. Remember the superuser password
    echo 4. Run this script again
    pause
    exit /b 1
)

echo.
echo Database setup completed successfully!
pause