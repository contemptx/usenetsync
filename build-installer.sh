#!/bin/bash

echo "============================================================"
echo "Building UsenetSync Installer with Python Backend"
echo "============================================================"
echo

# Step 1: Install Python dependencies
echo "Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt pyinstaller || {
    echo "Failed to install dependencies"
    exit 1
}

# Step 2: Build Python backend executable
echo
echo "Step 2: Building Python backend executable..."
cd src
python3 -m PyInstaller \
    --clean \
    --onefile \
    --name usenetsync-backend \
    --distpath ../usenet-sync-app/src-tauri/resources \
    cli.py || {
    echo "Failed to build Python backend"
    exit 1
}
cd ..

# Step 3: Build Tauri application
echo
echo "Step 3: Building Tauri application..."
cd usenet-sync-app
npm install
TAURI_CONFIG=tauri.conf.prod.json npm run tauri build -- --config tauri.conf.prod.json || {
    echo "Failed to build Tauri application"
    exit 1
}
cd ..

echo
echo "============================================================"
echo "Build complete! Application bundle located in:"
echo "usenet-sync-app/src-tauri/target/release/bundle/"
echo "============================================================"