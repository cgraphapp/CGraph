#!/bin/bash
# Script: scripts/backup.sh
# Complete backup of code, database, and configuration
# Run daily via cron

set -e

BACKUP_DIR="/opt/cgraph/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="cgraph-backup-$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Create backup directory
mkdir -p $BACKUP_DIR

echo "📦 Starting backup: $BACKUP_NAME"

# 1. Backup PostgreSQL Database
echo "📊 Backing up PostgreSQL..."
mkdir -p $BACKUP_PATH/database
docker exec cgraph-db-primary pg_dump \
  -U cgraph \
  -d cgraph \
  --format=custom \
  --compress=9 \
  --verbose \
  > $BACKUP_PATH/database/cgraph.dump.gz

SIZE=$(du -h $BACKUP_PATH/database/cgraph.dump.gz | cut -f1)
echo "✓ Database backup: $SIZE"

# 2. Backup Redis Cache
echo "💾 Backing up Redis..."
mkdir -p $BACKUP_PATH/redis
docker exec cgraph-redis redis-cli --rdb /data/dump.rdb
docker cp cgraph-redis:/data/dump.rdb $BACKUP_PATH/redis/

SIZE=$(du -h $BACKUP_PATH/redis/dump.rdb | cut -f1)
echo "✓ Redis backup: $SIZE"

# 3. Backup Code and Config
echo "📝 Backing up code..."
mkdir -p $BACKUP_PATH/code
cp -r /opt/cgraph/backend $BACKUP_PATH/code/ --exclude node_modules --exclude __pycache__ --exclude .venv
cp -r /opt/cgraph/frontend $BACKUP_PATH/code/ --exclude node_modules --exclude dist --exclude build
cp -r /opt/cgraph/mobile $BACKUP_PATH/code/ --exclude node_modules --exclude dist --exclude .expo
cp -r /opt/cgraph/nginx $BACKUP_PATH/code/

SIZE=$(du -sh $BACKUP_PATH/code | cut -f1)
echo "✓ Code backup: $SIZE"

# 4. Backup Environment Files
echo "🔐 Backing up environment config..."
mkdir -p $BACKUP_PATH/config
cp /opt/cgraph/backend/.env $BACKUP_PATH/config/ 2>/dev/null || true
cp /opt/cgraph/frontend/.env.production $BACKUP_PATH/config/ 2>/dev/null || true
cp /opt/cgraph/mobile/.env $BACKUP_PATH/config/ 2>/dev/null || true

# 5. Create Backup Manifest
cat > $BACKUP_PATH/MANIFEST.json << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$(date -Iseconds)",
  "components": {
    "database": "$(ls -lh $BACKUP_PATH/database/cgraph.dump.gz | awk '{print $5}')",
    "redis": "$(ls -lh $BACKUP_PATH/redis/dump.rdb | awk '{print $5}')",
    "code": "$(du -sh $BACKUP_PATH/code | cut -f1)"
  },
  "md5_checksums": {
    "database": "$(md5sum $BACKUP_PATH/database/cgraph.dump.gz | awk '{print $1}')",
    "redis": "$(md5sum $BACKUP_PATH/redis/dump.rdb | awk '{print $1}')"
  }
}
EOF

# 6. Create tar archive for easy transfer
echo "📦 Creating archive..."
tar -czf $BACKUP_PATH.tar.gz -C $BACKUP_DIR $BACKUP_NAME
rm -rf $BACKUP_PATH

TOTAL_SIZE=$(du -h $BACKUP_PATH.tar.gz | cut -f1)
echo "✓ Archive created: $TOTAL_SIZE"

# 7. Upload to remote storage (optional - S3, Backblaze, etc.)
# If you have S3 credentials:
# aws s3 cp $BACKUP_PATH.tar.gz s3://your-backup-bucket/cgraph/

# 8. Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "cgraph-backup-*.tar.gz" -mtime +30 -delete

# 9. Update backup registry
cat >> $BACKUP_DIR/BACKUP_REGISTRY.md << EOF
- **$TIMESTAMP** - Size: $TOTAL_SIZE - Status: ✓ Complete
EOF

echo "✅ Backup complete: $BACKUP_PATH.tar.gz"
echo "📋 Backup registry updated"
