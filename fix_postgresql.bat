@echo off
echo ========================================
echo PostgreSQL Fix Tool for UsenetSync
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires Administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Checking PostgreSQL installation...
echo.

REM Check for portable PostgreSQL
set PORTABLE_PG=%LOCALAPPDATA%\UsenetSync\postgresql
if exist "%PORTABLE_PG%\bin\psql.exe" (
    echo Found portable PostgreSQL at %PORTABLE_PG%
    set PSQL="%PORTABLE_PG%\bin\psql.exe"
    set PG_CTL="%PORTABLE_PG%\bin\pg_ctl.exe"
    set DATA_DIR=%LOCALAPPDATA%\UsenetSync\pgdata
    goto :fix_database
)

REM Check for system PostgreSQL
set SYSTEM_PG=C:\Program Files\PostgreSQL\14
if exist "%SYSTEM_PG%\bin\psql.exe" (
    echo Found system PostgreSQL at %SYSTEM_PG%
    set PSQL="%SYSTEM_PG%\bin\psql.exe"
    goto :fix_database
)

echo PostgreSQL not found!
echo Please install PostgreSQL first using the Settings page.
pause
exit /b 1

:fix_database
echo.
echo Creating UsenetSync database and user...
echo.

REM Create a temporary SQL file
set TEMP_SQL=%TEMP%\usenetsync_setup.sql
echo CREATE USER usenet WITH PASSWORD 'usenetsync'; > "%TEMP_SQL%"
echo CREATE DATABASE usenet OWNER usenet; >> "%TEMP_SQL%"
echo GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet; >> "%TEMP_SQL%"

REM Try to execute as postgres user (no password)
echo Attempting to connect as postgres user...
%PSQL% -U postgres -h localhost -f "%TEMP_SQL%" 2>nul
if %errorLevel% equ 0 (
    echo Success! Database and user created.
    goto :test_connection
)

REM Try with default password
echo Trying with default postgres password...
set PGPASSWORD=postgres
%PSQL% -U postgres -h localhost -f "%TEMP_SQL%" 2>nul
if %errorLevel% equ 0 (
    echo Success! Database and user created.
    goto :test_connection
)

REM Try with no host (local connection)
echo Trying local connection...
%PSQL% -U postgres -f "%TEMP_SQL%" 2>nul
if %errorLevel% equ 0 (
    echo Success! Database and user created.
    goto :test_connection
)

echo.
echo Could not create database automatically.
echo.
echo Please run these commands manually:
echo 1. Open Command Prompt as Administrator
echo 2. Run: %PSQL% -U postgres
echo 3. Enter these commands:
echo    CREATE USER usenet WITH PASSWORD 'usenetsync';
echo    CREATE DATABASE usenet OWNER usenet;
echo    GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;
echo    \q
echo.
pause
exit /b 1

:test_connection
echo.
echo Testing connection...
set PGPASSWORD=usenetsync
echo SELECT version(); | %PSQL% -U usenet -h localhost -d usenet >nul 2>&1
if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! PostgreSQL is configured!
    echo ========================================
    echo.
    echo Connection details:
    echo   Host: localhost
    echo   Port: 5432
    echo   Database: usenet
    echo   User: usenet
    echo   Password: usenetsync
    echo.
    echo You can now use PostgreSQL in UsenetSync!
) else (
    echo.
    echo Connection test failed.
    echo Please check the PostgreSQL service is running.
)

REM Clean up
del "%TEMP_SQL%" 2>nul

echo.
pause