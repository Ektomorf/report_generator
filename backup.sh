#!/bin/bash
# Automated backup script for Test Results Archive System

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATABASE_FILE="${DATABASE_FILE:-./test_results.db}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_PREFIX="test_results_backup"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${BACKUP_PREFIX}_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

echo "======================================"
echo "Test Results Archive - Backup"
echo "======================================"
echo "Timestamp: $(date)"
echo "Backup file: $BACKUP_FILE"
echo ""

# Check if database exists
if [ ! -f "$DATABASE_FILE" ]; then
    echo "Warning: Database file not found: $DATABASE_FILE"
    echo "Skipping database backup."
    DATABASE_EXISTS=false
else
    DATABASE_EXISTS=true
fi

# Create backup
echo "Creating backup..."

if [ "$DATABASE_EXISTS" = true ]; then
    # Backup with database
    tar -czf "$BACKUP_FILE" \
        --exclude='*.log' \
        --exclude='backups' \
        --exclude='output' \
        --exclude='__pycache__' \
        --exclude='.git' \
        "$DATABASE_FILE" \
        docker-compose.yml \
        nginx/ \
        schema.sql 2>/dev/null || echo "Some files may be missing"
else
    # Backup without database
    tar -czf "$BACKUP_FILE" \
        --exclude='*.log' \
        --exclude='backups' \
        --exclude='output' \
        --exclude='__pycache__' \
        --exclude='.git' \
        docker-compose.yml \
        nginx/ \
        schema.sql 2>/dev/null || echo "Some files may be missing"
fi

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "Error: Backup failed!"
    exit 1
fi

# Create a "latest" symlink
LATEST_LINK="${BACKUP_DIR}/${BACKUP_PREFIX}_latest.tar.gz"
rm -f "$LATEST_LINK"
ln -s "$(basename "$BACKUP_FILE")" "$LATEST_LINK"
echo "Latest backup linked to: $LATEST_LINK"

# Clean up old backups
echo ""
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING_BACKUPS=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -type f | wc -l)
echo "Remaining backups: $REMAINING_BACKUPS"

# List recent backups
echo ""
echo "Recent backups:"
ls -lht "$BACKUP_DIR"/${BACKUP_PREFIX}_*.tar.gz | head -n 5

echo ""
echo "Backup complete!"
