@echo off
echo ============================================================
echo UsenetSync Setup for Windows
echo ============================================================
echo.

echo Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install with system pip, trying user install...
    python -m pip install --user -r requirements.txt
)

echo.
echo Verifying pynntp installation...
python -c "from nntp import NNTPClient; print('pynntp verified successfully')"
if errorlevel 1 (
    echo pynntp not found, installing...
    python -m pip install --user pynntp
    python -c "from nntp import NNTPClient; print('pynntp installed and verified')"
)

echo.
echo ============================================================
echo Setup complete! You can now run: npm run tauri dev
echo ============================================================
pause