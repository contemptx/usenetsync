#!/bin/bash
#
# Quick Deployment Script for UsenetSync
# Deploys using Docker Compose for easy setup
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "================================================"
echo "   UsenetSync Quick Deployment with Docker"
echo "================================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Get NNTP credentials
echo "Please enter your NNTP credentials:"
read -p "NNTP Username: " NNTP_USER
read -sp "NNTP Password: " NNTP_PASSWORD
echo ""

# Create .env file
cat > .env <<EOF
NNTP_USER=${NNTP_USER}
NNTP_PASSWORD=${NNTP_PASSWORD}
EOF

# Create config directory
mkdir -p config

# Create default configuration
cat > config/usenetsync.conf <<EOF
[database]
type = postgresql
host = postgres
port = 5432
database = usenetsync
user = usenetsync
password = usenetsync123

[nntp]
host = news.newshosting.com
port = 563
username = ${NNTP_USER}
password = ${NNTP_PASSWORD}
use_ssl = true
max_connections = 10

[storage]
data_dir = /data
temp_dir = /tmp
segment_size = 786432

[monitoring]
enable = true
prometheus_port = 9090
EOF

# Create Prometheus configuration
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'usenetsync'
    static_configs:
      - targets: ['usenetsync:9090']
EOF

# Build and start services
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

echo -e "${GREEN}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${GREEN}Waiting for services to be ready...${NC}"
sleep 10

# Check service status
echo ""
echo -e "${GREEN}Service Status:${NC}"
docker-compose ps

echo ""
echo "================================================"
echo "   Deployment Complete!"
echo "================================================"
echo ""
echo "Services:"
echo "  - Application: http://localhost:8000"
echo "  - Prometheus: http://localhost:9091"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "Commands:"
echo "  View logs: docker-compose logs -f usenetsync"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update: git pull && docker-compose build && docker-compose up -d"
echo ""
echo "Your NNTP credentials have been saved to .env"
echo "Configuration is in config/usenetsync.conf"
echo ""