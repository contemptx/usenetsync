#!/bin/bash
#
# Automated Deployment Script for Unified UsenetSync System
# Handles installation, configuration, and deployment
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/usenetsync"
DATA_DIR="/var/lib/usenetsync"
LOG_DIR="/var/log/usenetsync"
CONFIG_DIR="/etc/usenetsync"
SERVICE_USER="usenetsync"
PYTHON_VERSION="3.11"

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        print_error "Python ${PYTHON_VERSION} is not installed"
        exit 1
    fi
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL is not installed. Installing..."
        apt-get update
        apt-get install -y postgresql postgresql-contrib
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        apt-get install -y git
    fi
    
    print_status "Dependencies checked"
}

create_user() {
    print_status "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --home-dir "$DATA_DIR" --shell /bin/false "$SERVICE_USER"
        print_status "User $SERVICE_USER created"
    else
        print_status "User $SERVICE_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    
    print_status "Directories created"
}

setup_database() {
    print_status "Setting up PostgreSQL database..."
    
    # Check if database exists
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw usenetsync; then
        print_status "Database already exists"
    else
        # Create database and user
        sudo -u postgres psql <<EOF
CREATE DATABASE usenetsync;
CREATE USER usenetsync WITH PASSWORD 'usenetsync123';
GRANT ALL PRIVILEGES ON DATABASE usenetsync TO usenetsync;
ALTER DATABASE usenetsync OWNER TO usenetsync;
EOF
        print_status "Database created"
    fi
}

install_application() {
    print_status "Installing UsenetSync application..."
    
    # Clone or update repository
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_status "Updating existing installation..."
        cd "$INSTALL_DIR"
        git pull
    else
        print_status "Cloning repository..."
        git clone https://github.com/contemptx/usenetsync.git "$INSTALL_DIR"
    fi
    
    # Create virtual environment
    print_status "Creating Python virtual environment..."
    cd "$INSTALL_DIR"
    python${PYTHON_VERSION} -m venv venv
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    print_status "Application installed"
}

create_configuration() {
    print_status "Creating configuration..."
    
    cat > "$CONFIG_DIR/usenetsync.conf" <<EOF
# UsenetSync Configuration
[database]
type = postgresql
host = localhost
port = 5432
database = usenetsync
user = usenetsync
password = usenetsync123

[nntp]
host = news.newshosting.com
port = 563
username = YOUR_USERNAME
password = YOUR_PASSWORD
use_ssl = true
max_connections = 10

[storage]
data_dir = ${DATA_DIR}
temp_dir = /tmp/usenetsync
segment_size = 786432  # 768KB

[security]
enable_encryption = true
user_id_file = ${DATA_DIR}/user_id
keys_dir = ${DATA_DIR}/keys

[monitoring]
enable = true
prometheus_port = 9090
log_level = INFO
log_file = ${LOG_DIR}/usenetsync.log

[performance]
max_parallel_indexing = 4
max_parallel_uploads = 8
memory_limit_mb = 2048
EOF
    
    chmod 600 "$CONFIG_DIR/usenetsync.conf"
    chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/usenetsync.conf"
    
    print_status "Configuration created at $CONFIG_DIR/usenetsync.conf"
    print_warning "Please update NNTP credentials in the configuration file"
}

create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat > /etc/systemd/system/usenetsync.service <<EOF
[Unit]
Description=UsenetSync Unified System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/src/unified/main.py --config ${CONFIG_DIR}/usenetsync.conf
Restart=on-failure
RestartSec=10
StandardOutput=append:${LOG_DIR}/usenetsync.log
StandardError=append:${LOG_DIR}/usenetsync.error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR}

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    print_status "Systemd service created"
}

setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create Prometheus configuration
    cat > "$CONFIG_DIR/prometheus.yml" <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'usenetsync'
    static_configs:
      - targets: ['localhost:9090']
EOF
    
    # Create monitoring dashboard script
    cat > "$INSTALL_DIR/monitor.sh" <<EOF
#!/bin/bash
source ${INSTALL_DIR}/venv/bin/activate
python ${INSTALL_DIR}/src/unified/monitoring_dashboard.py
EOF
    
    chmod +x "$INSTALL_DIR/monitor.sh"
    
    print_status "Monitoring configured"
}

run_migration() {
    print_status "Running database migration..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Check if old databases exist
    if [ -f "$DATA_DIR/old_indexing.db" ] || [ -f "$DATA_DIR/old_upload.db" ]; then
        print_status "Found old databases. Running migration..."
        python -m src.unified.migration_system \
            --old-indexing "$DATA_DIR/old_indexing.db" \
            --old-upload "$DATA_DIR/old_upload.db" \
            --target postgresql \
            --backup-dir "$DATA_DIR/backup"
    else
        print_status "No old databases found. Skipping migration."
    fi
    
    # Initialize database schema
    python -c "
from src.unified.database_schema import UnifiedDatabaseSchema
schema = UnifiedDatabaseSchema('postgresql', 
    host='localhost',
    database='usenetsync',
    user='usenetsync',
    password='usenetsync123'
)
schema.create_schema()
print('Database schema initialized')
"
    
    print_status "Migration complete"
}

run_tests() {
    print_status "Running system tests..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Run basic connectivity test
    python -c "
from src.unified.unified_system import UnifiedSystem
system = UnifiedSystem('postgresql',
    host='localhost',
    database='usenetsync',
    user='usenetsync',
    password='usenetsync123'
)
print('✓ Database connection successful')
"
    
    # Test indexing
    TEST_DIR=$(mktemp -d)
    echo "Test file" > "$TEST_DIR/test.txt"
    
    python -c "
from src.unified.unified_system import UnifiedSystem
system = UnifiedSystem('postgresql',
    host='localhost',
    database='usenetsync',
    user='usenetsync',
    password='usenetsync123'
)
stats = system.indexer.index_folder('$TEST_DIR')
print(f'✓ Indexing test successful: {stats[\"files_indexed\"]} files')
"
    
    rm -rf "$TEST_DIR"
    
    print_status "Tests passed"
}

start_service() {
    print_status "Starting UsenetSync service..."
    
    systemctl enable usenetsync.service
    systemctl start usenetsync.service
    
    sleep 2
    
    if systemctl is-active --quiet usenetsync.service; then
        print_status "Service started successfully"
    else
        print_error "Service failed to start. Check logs at $LOG_DIR/usenetsync.error.log"
        exit 1
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "   UsenetSync Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo "Data directory: $DATA_DIR"
    echo "Log directory: $LOG_DIR"
    echo "Configuration: $CONFIG_DIR/usenetsync.conf"
    echo ""
    echo "Service status:"
    systemctl status usenetsync.service --no-pager | head -n 3
    echo ""
    echo "Next steps:"
    echo "1. Update NNTP credentials in $CONFIG_DIR/usenetsync.conf"
    echo "2. Restart service: systemctl restart usenetsync"
    echo "3. View logs: tail -f $LOG_DIR/usenetsync.log"
    echo "4. Monitor system: $INSTALL_DIR/monitor.sh"
    echo ""
    echo "Prometheus metrics available at: http://localhost:9090/metrics"
    echo ""
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "   UsenetSync Unified System Deployment"
    echo "=========================================="
    echo ""
    
    check_root
    check_dependencies
    create_user
    create_directories
    setup_database
    install_application
    create_configuration
    create_systemd_service
    setup_monitoring
    run_migration
    run_tests
    start_service
    print_summary
}

# Run main function
main "$@"