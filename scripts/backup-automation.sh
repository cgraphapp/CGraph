#!/bin/bash
# /scripts/backup-automation.sh
# Automated daily backups with retention

set -e

BACKUP_DIR="/backups"
S3_BUCKET="cgraph-backups"
RETENTION_DAYS=30
DB_NAME="cgraph"
DB_USER="postgres"

# Create backup
backup_database() {
    local BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    local BACKUP_FILE="$BACKUP_DIR/db_backup_$BACKUP_DATE.sql.gz"
    
    echo "Starting database backup..."
    
    pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_FILE"
    
    echo "Backup completed: $BACKUP_FILE"
    
    # Upload to S3
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/daily/"
    
    # Cleanup old local backups
    find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
}

# Setup cron job
setup_cron() {
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * /scripts/backup-automation.sh >> /var/log/backup.log 2>&1") | crontab -
}

backup_database