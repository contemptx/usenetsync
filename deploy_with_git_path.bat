@echo off
REM Deploy to GitHub using full Git path

echo ========================================
echo   Deploying to GitHub
echo ========================================
echo.

set GIT_PATH=C:\Program Files\Git\bin\git.exe

if not exist "%GIT_PATH%" (
    echo ERROR: Git not found at expected location
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Using Git at: %GIT_PATH%
echo.

echo Initializing repository...
"%GIT_PATH%" init

echo.
echo Configuring Git...
"%GIT_PATH%" config user.name "contemptx"
"%GIT_PATH%" config user.email "contemptx@me.com"

echo.
echo Adding files...
"%GIT_PATH%" add .

echo.
echo Creating commit...
"%GIT_PATH%" commit -m "Initial commit - Complete UsenetSync repository with all modules"

echo.
echo Adding remote repository...
"%GIT_PATH%" remote add origin https://github.com/contemptx/usenetsync.git

echo.
echo Current status:
"%GIT_PATH%" status

echo.
echo ========================================
echo Ready to push to GitHub!
echo.
echo When you run the next command, you'll need:
echo   Username: contemptx
echo   Password: Your GitHub Personal Access Token
echo   (NOT your GitHub password!)
echo.
echo To create a token:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token (classic)"
echo   3. Give it a name
echo   4. Select scope: "repo" (full control)
echo   5. Generate and copy the token
echo ========================================
echo.
echo Press any key to push to GitHub...
pause >nul

echo.
echo Pushing to GitHub...
"%GIT_PATH%" push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Push failed. Common issues:
    echo.
    echo 1. Authentication failed:
    echo    - Make sure to use a Personal Access Token
    echo    - NOT your GitHub password
    echo.
    echo 2. Repository doesn't exist:
    echo    - Create it at https://github.com/new
    echo    - Name: usenetsync
    echo    - Don't initialize with any files
    echo.
    echo 3. Branch name is 'master' not 'main':
    echo    Try: "%GIT_PATH%" push -u origin master
    echo ========================================
) else (
    echo.
    echo ========================================
    echo SUCCESS! Your code is now on GitHub!
    echo.
    echo Repository: https://github.com/contemptx/usenetsync
    echo ========================================
)

pause
