#!/bin/bash

echo "Starting UsenetSync GUI..."
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ for your system"
    exit 1
fi

# Check if GUI dependencies are installed
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "Installing GUI dependencies..."
    python3 -m pip install -r requirements-gui.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install dependencies"
        exit 1
    fi
fi

# Launch GUI
python3 gui/main_application.py
