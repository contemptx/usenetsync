@echo off
echo GitHub Repository Status
echo =======================
"C:\Program Files\Git\bin\git.exe" status
echo.
"C:\Program Files\Git\bin\git.exe" log --oneline -5
pause
