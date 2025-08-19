#!/bin/bash
# Unified UsenetSync Installation Script

set -e

echo "================================"
echo "Unified UsenetSync Installer"
echo "================================"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Python version: $PYTHON_VERSION ✓"

# Create installation directory
INSTALL_DIR="$HOME/.usenetsync"
mkdir -p "$INSTALL_DIR"
echo "Installation directory: $INSTALL_DIR"

# Copy source files
echo "Copying files..."
cp -r src "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Create virtual environment
echo "Creating virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create configuration
echo "Creating configuration..."
cat > "$INSTALL_DIR/config.json" << EOF
{
    "database_type": "sqlite",
    "database_path": "$INSTALL_DIR/data/unified.db",
    "system_data_directory": "$INSTALL_DIR/data",
    "cache_directory": "$INSTALL_DIR/cache",
    "log_directory": "$INSTALL_DIR/logs",
    "api_host": "127.0.0.1",
    "api_port": 8000
}
EOF

# Create directories
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/cache"
mkdir -p "$INSTALL_DIR/logs"

# Create launcher script
echo "Creating launcher..."
cat > "$INSTALL_DIR/usenetsync" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/src"
python -m unified.main "$@"
EOF

chmod +x "$INSTALL_DIR/usenetsync"

# Create systemd service (Linux only)
if [ "$OS" == "linux" ]; then
    echo "Creating systemd service..."
    sudo tee /etc/systemd/system/usenetsync.service > /dev/null << EOF
[Unit]
Description=Unified UsenetSync Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/usenetsync
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "Service created. Run 'sudo systemctl start usenetsync' to start"
fi

# Create desktop shortcut
if [ "$OS" == "linux" ]; then
    cat > "$HOME/.local/share/applications/usenetsync.desktop" << EOF
[Desktop Entry]
Name=UsenetSync
Comment=Unified UsenetSync Application
Exec=$INSTALL_DIR/usenetsync
Icon=$INSTALL_DIR/icon.png
Terminal=false
Type=Application
Categories=Network;FileTransfer;
EOF
fi

echo ""
echo "================================"
echo "Installation Complete!"
echo "================================"
echo ""
echo "To run UsenetSync:"
echo "  $INSTALL_DIR/usenetsync"
echo ""
echo "To start as service (Linux):"
echo "  sudo systemctl start usenetsync"
echo "  sudo systemctl enable usenetsync  # Auto-start on boot"
echo ""
echo "API will be available at:"
echo "  http://localhost:8000"
echo ""