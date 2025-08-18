#!/bin/bash

echo "============================================================"
echo "UsenetSync PostgreSQL Database Setup"
echo "============================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 first"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip3 install psycopg2-binary

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Attempting to install..."
    
    # Detect OS and install PostgreSQL
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib
            sudo systemctl start postgresql
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS
            sudo yum install -y postgresql-server postgresql-contrib
            sudo postgresql-setup initdb
            sudo systemctl start postgresql
        else
            echo "Please install PostgreSQL manually"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install postgresql
            brew services start postgresql
        else
            echo "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    fi
fi

# Run the setup script
echo
echo "Running database setup..."
python3 setup_database.py

if [ $? -ne 0 ]; then
    echo
    echo "Database setup failed!"
    echo "Please check the error messages above"
    exit 1
fi

echo
echo "Database setup completed successfully!"