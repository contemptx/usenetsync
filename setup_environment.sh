#!/bin/bash

# UsenetSync Environment Setup Script

echo "============================================================"
echo "USENETSYNC ENVIRONMENT SETUP"
echo "============================================================"
echo ""

# Check if credentials are already set
if [ -n "$NNTP_USERNAME" ] && [ -n "$NNTP_PASSWORD" ]; then
    echo "✓ NNTP credentials already set in environment"
    echo "  Username: ${NNTP_USERNAME:0:3}..."
else
    echo "Please enter your NNTP credentials:"
    echo ""
    
    # Get username
    read -p "NNTP Username: " username
    export NNTP_USERNAME="$username"
    
    # Get password (hidden input)
    read -s -p "NNTP Password: " password
    echo ""
    export NNTP_PASSWORD="$password"
    
    echo ""
    echo "✓ Credentials set for this session"
fi

# Optional: Set other environment variables
echo ""
echo "Optional configuration (press Enter to use defaults):"
read -p "NNTP Server [news.newshosting.com]: " server
if [ -n "$server" ]; then
    export NNTP_SERVER="$server"
fi

read -p "NNTP Port [563]: " port
if [ -n "$port" ]; then
    export NNTP_PORT="$port"
fi

read -p "Use SSL? (yes/no) [yes]: " use_ssl
if [ "$use_ssl" = "no" ]; then
    export NNTP_SSL="false"
else
    export NNTP_SSL="true"
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p data logs temp tests/logs

# Install Python dependencies
echo ""
echo "Checking Python dependencies..."
python3 -c "import cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing missing dependencies..."
    pip3 install --break-system-packages -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi

# Display summary
echo ""
echo "============================================================"
echo "ENVIRONMENT READY"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  NNTP Server: ${NNTP_SERVER:-news.newshosting.com}"
echo "  NNTP Port: ${NNTP_PORT:-563}"
echo "  NNTP SSL: ${NNTP_SSL:-true}"
echo "  Username: ${NNTP_USERNAME:0:3}..."
echo ""
echo "To make these settings permanent, add to your ~/.bashrc:"
echo ""
echo "  export NNTP_USERNAME='$NNTP_USERNAME'"
echo "  export NNTP_PASSWORD='your_password'"
if [ -n "$NNTP_SERVER" ]; then
    echo "  export NNTP_SERVER='$NNTP_SERVER'"
fi
if [ -n "$NNTP_PORT" ]; then
    echo "  export NNTP_PORT='$NNTP_PORT'"
fi
echo ""
echo "You can now run:"
echo "  python3 test_basic.py    # Basic tests"
echo "  python3 run_tests.py     # Full E2E tests"
echo ""