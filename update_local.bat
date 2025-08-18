@echo off
echo Updating UsenetSync to latest version...
echo.

cd /d C:\git\usenetsync

echo Fetching latest changes from GitHub...
git fetch origin

echo.
echo Current branch:
git branch --show-current

echo.
echo Pulling latest changes...
git pull origin master

echo.
echo Latest commits:
git log --oneline -5

echo.
echo Update complete!
echo.
pause