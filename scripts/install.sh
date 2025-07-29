#!/bin/bash
# UsenetSync Installation Script

set -e

echo "Installing UsenetSync..."

# Check Python version
if ! python3 --version | grep -E "3\.(8|9|10|11)" > /dev/null; then
    echo "ERROR: Python 3.8+ required"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install UsenetSync
pip install --upgrade pip
pip install usenetsync

# Setup configuration
mkdir -p data logs temp
cp .env.example .env

echo "UsenetSync installed successfully!"
echo "Next steps:"
echo "   1. Edit .env with your NNTP server details"
echo "   2. Initialize: usenetsync init"
echo "   3. Start using: usenetsync index /path/to/folder"
