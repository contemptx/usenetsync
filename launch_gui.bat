@echo off
title UsenetSync GUI
echo Starting UsenetSync GUI...
cd /d "%~dp0"

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking tkinter availability...
python -c "import tkinter; print('tkinter OK')" 2>nul
if errorlevel 1 (
    echo Error: tkinter not available
    echo Please reinstall Python with tkinter support
    pause
    exit /b 1
)

echo Launching UsenetSync GUI...
if exist "gui\main_application.py" (
    python gui\main_application.py
) else (
    echo Error: GUI files not found
    echo Please run the setup script first
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo GUI encountered an error. Check logs for details.
    pause
)
