@echo off
REM Push to GitHub with proper branch and authentication

echo ========================================
echo   Pushing to GitHub (Master Branch)
echo ========================================
echo.

set GIT_PATH=C:\Program Files\Git\bin\git.exe

echo Current branch status:
"%GIT_PATH%" branch
echo.

echo Checking remote:
"%GIT_PATH%" remote -v
echo.

REM Clear any stored credentials to force a prompt
echo Clearing stored credentials...
"%GIT_PATH%" config --unset credential.helper

echo ========================================
echo IMPORTANT: Authentication Setup
echo.
echo GitHub no longer accepts passwords!
echo You MUST use a Personal Access Token.
echo.
echo 1. Go to: https://github.com/settings/tokens
echo 2. Generate new token (classic)
echo 3. Select "repo" scope
echo 4. Copy the token
echo.
echo When prompted:
echo   Username: contemptx
echo   Password: [PASTE YOUR TOKEN]
echo ========================================
echo.
pause

echo.
echo Pushing to master branch...
"%GIT_PATH%" push -u origin master

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! Your code is now on GitHub!
    echo.
    echo Repository: https://github.com/contemptx/usenetsync
    echo Branch: master
    echo.
    echo Next steps:
    echo 1. Visit your repository
    echo 2. Add a description
    echo 3. Configure settings
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Push failed. Let's try with explicit URL...
    echo ========================================
    echo.
    
    echo Setting remote URL with username...
    "%GIT_PATH%" remote set-url origin https://contemptx@github.com/contemptx/usenetsync.git
    
    echo.
    echo Trying push again...
    "%GIT_PATH%" push -u origin master
    
    if %errorlevel% neq 0 (
        echo.
        echo ========================================
        echo Still failing. Manual steps:
        echo.
        echo 1. Make sure repository exists at:
        echo    https://github.com/contemptx/usenetsync
        echo.
        echo 2. Try this command manually:
        echo    git push https://contemptx:[YOUR-TOKEN]@github.com/contemptx/usenetsync.git master
        echo    (Replace [YOUR-TOKEN] with your actual token)
        echo ========================================
    )
)

pause
