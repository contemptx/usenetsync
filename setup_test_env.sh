#!/bin/bash

echo "🔧 Setting up E2E test environment..."

# Set up PostgreSQL if not running
if ! pg_isready -q; then
    echo "Starting PostgreSQL..."
    sudo service postgresql start
    sleep 2
fi

# Create test database
sudo -u postgres psql << SQL
CREATE DATABASE IF NOT EXISTS usenet_sync;
CREATE USER IF NOT EXISTS usenet_user WITH PASSWORD 'usenet_pass';
GRANT ALL PRIVILEGES ON DATABASE usenet_sync TO usenet_user;
SQL

# Set environment variables for testing
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=usenet_sync
export DB_USER=postgres
export DB_PASSWORD=postgres

# For Usenet testing (use demo/test server if available)
export NNTP_HOST=${NNTP_HOST:-"news.usenetserver.com"}
export NNTP_PORT=${NNTP_PORT:-563}
export NNTP_USER=${NNTP_USER:-"demo"}
export NNTP_PASS=${NNTP_PASS:-"demo"}

echo "✅ Environment ready"
