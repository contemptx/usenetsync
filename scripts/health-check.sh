#!/bin/bash
# Health check script for UsenetSync

echo "UsenetSync Health Check"
echo "======================"

# Check if UsenetSync is installed
if ! command -v usenetsync &> /dev/null; then
    echo "ERROR: UsenetSync not found in PATH"
    exit 1
fi

# Check configuration
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found"
    echo "INFO: Copy .env.example to .env and configure"
fi

# Check directories
for dir in data logs temp; do
    if [ ! -d "$dir" ]; then
        echo "WARNING: Directory $dir missing"
        mkdir -p "$dir"
        echo "INFO: Created $dir"
    fi
done

# Run health check
echo "Running system health check..."
python production_monitoring_system.py health

echo "Health check completed"
