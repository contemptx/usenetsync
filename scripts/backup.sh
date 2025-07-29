#!/bin/bash
# Backup script for UsenetSync data

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."

# Backup database
if [ -f "data/usenetsync.db" ]; then
    cp "data/usenetsync.db" "$BACKUP_DIR/"
    echo "Database backed up"
fi

# Backup configuration
if [ -f ".env" ]; then
    cp ".env" "$BACKUP_DIR/"
    echo "Configuration backed up"
fi

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

echo "Backup completed: $BACKUP_DIR"
