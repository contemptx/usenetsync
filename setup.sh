#!/bin/bash

echo "============================================================"
echo "UsenetSync Setup for Unix/Linux/Mac"
echo "============================================================"
echo

echo "Installing Python dependencies..."
if python3 -m pip install -r requirements.txt 2>/dev/null; then
    echo "✓ Dependencies installed successfully"
elif python3 -m pip install --user -r requirements.txt 2>/dev/null; then
    echo "✓ Dependencies installed successfully (user install)"
elif pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
    echo "✓ Dependencies installed successfully (system packages override)"
else
    echo "✗ Failed to install dependencies automatically"
    echo "Please install manually with:"
    echo "  pip3 install -r requirements.txt"
    exit 1
fi

echo
echo "Verifying pynntp installation..."
if python3 -c "from nntp import NNTPClient; print('✓ pynntp verified successfully')" 2>/dev/null; then
    echo "pynntp is working correctly"
else
    echo "pynntp not found, installing..."
    if python3 -m pip install --user pynntp 2>/dev/null || pip3 install --break-system-packages pynntp 2>/dev/null; then
        python3 -c "from nntp import NNTPClient; print('✓ pynntp installed and verified')"
    else
        echo "✗ Failed to install pynntp"
        echo "Please install manually with:"
        echo "  pip3 install pynntp"
        exit 1
    fi
fi

echo
echo "============================================================"
echo "✓ Setup complete! You can now run: npm run tauri dev"
echo "============================================================"