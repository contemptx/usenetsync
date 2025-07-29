@echo off
REM UsenetSync Installation Script for Windows

echo Installing UsenetSync...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install UsenetSync
python -m pip install --upgrade pip
pip install usenetsync

REM Setup configuration
mkdir data logs temp 2>nul
copy .env.example .env >nul

echo UsenetSync installed successfully!
echo Next steps:
echo    1. Edit .env with your NNTP server details
echo    2. Initialize: usenetsync init
echo    3. Start using: usenetsync index /path/to/folder

pause
