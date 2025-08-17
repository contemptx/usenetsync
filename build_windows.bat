@echo off
REM UsenetSync Windows Build Script
REM Builds the complete installer package

echo ========================================
echo UsenetSync Windows Build Script
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Create build directory
echo Creating build directories...
if not exist "build" mkdir build
if not exist "dist" mkdir dist
if not exist "assets" mkdir assets

REM Build Python application with PyInstaller
echo.
echo Building Python application...
pip install pyinstaller
pyinstaller --onefile ^
    --name usenet-sync ^
    --icon assets\icon.ico ^
    --add-data "usenet_sync_config.template.json;." ^
    --add-data "src;src" ^
    --hidden-import click ^
    --hidden-import cryptography ^
    --hidden-import colorama ^
    --hidden-import psutil ^
    --hidden-import tabulate ^
    --hidden-import tqdm ^
    --hidden-import sqlalchemy ^
    --hidden-import requests ^
    --hidden-import urllib3 ^
    --hidden-import prometheus_client ^
    --hidden-import dateutil ^
    --hidden-import yaml ^
    --hidden-import dotenv ^
    --hidden-import watchdog ^
    --hidden-import pynntp ^
    --hidden-import psycopg2 ^
    main.py

REM Download NSIS if not installed
echo.
echo Checking NSIS installation...
if not exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo Downloading NSIS...
    powershell -Command "Invoke-WebRequest -Uri 'https://prdownloads.sourceforge.net/nsis/nsis-3.09-setup.exe' -OutFile 'nsis-setup.exe'"
    echo Please install NSIS and run this script again
    start nsis-setup.exe
    exit /b 1
)

REM Create assets if they don't exist
echo.
echo Creating installer assets...
if not exist "assets\icon.ico" (
    echo Creating placeholder icon...
    REM In production, would use actual icon
    copy NUL assets\icon.ico
)

if not exist "LICENSE.txt" (
    echo Creating LICENSE file...
    echo MIT License > LICENSE.txt
    echo. >> LICENSE.txt
    echo Copyright (c) 2024 UsenetSync >> LICENSE.txt
)

REM Build installer
echo.
echo Building installer...
"C:\Program Files (x86)\NSIS\makensis.exe" windows_installer.nsi

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo Installer: UsenetSync-Setup.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    exit /b 1
)

pause