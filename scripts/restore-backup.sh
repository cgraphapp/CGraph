#!/bin/bash
# Script: scripts/restore-backup.sh

set -e

BACKUP_FILE="${1:?Usage: restore-backup.sh /path/to/backup.tar.gz}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "⚠️  WARNING: This will overwrite current database and code"
read -p "Type YES to continue: " confirm
[ "$confirm" = "YES" ] || exit 1

BACKUP_DIR="/tmp/cgraph-restore"
mkdir -p $BACKUP_DIR

echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE" -C $BACKUP_DIR

BACKUP_NAME=$(basename $BACKUP_FILE .tar.gz)
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Verify manifest
if [ ! -f "$BACKUP_PATH/MANIFEST.json" ]; then
  echo "❌ Invalid backup: missing MANIFEST.json"
  exit 1
fi

echo "📊 Restoring database..."
dropdb cgraph 2>/dev/null || true
createdb cgraph

pg_restore \
  -U cgraph \
  -d cgraph \
  -v \
  "$BACKUP_PATH/database/cgraph.dump.gz"

echo "✓ Database restored"

echo "💾 Restoring Redis cache..."
redis-cli FLUSHALL
redis-cli --pipe < "$BACKUP_PATH/redis/dump.rdb"

echo "✓ Redis restored"

echo "📝 Restoring code..."
cp -r "$BACKUP_PATH/code/"* /opt/cgraph/

echo "✓ Code restored"

echo "🔄 Restarting services..."
cd /opt/cgraph
docker-compose restart

echo "✅ Restore complete"
echo "⏰ Verify all services:"
docker ps | grep cgraph
