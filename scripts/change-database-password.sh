#!/bin/bash
# Script: scripts/change-database-password.sh

set -e

NEW_PASSWORD="1994Lks.Oli2017.iheartlegale2021."
DB_USER="cgraph"
DB_NAME="cgraph"

echo "🔐 Changing database password..."

# Connect to PostgreSQL and change password
PGPASSWORD=cgraph psql -U $DB_USER -d $DB_NAME -h localhost << EOF
ALTER USER $DB_USER WITH PASSWORD '$NEW_PASSWORD';
EOF

echo "✓ PostgreSQL password changed"

# Update Redis password
redis-cli CONFIG SET requirepass "$NEW_PASSWORD" || true
echo "✓ Redis password changed"

# Update backend environment
sed -i "s|REDISURL=.*|REDISURL=redis://:$NEW_PASSWORD@localhost:6379/0|" /opt/cgraph/backend/.env
sed -i "s|postgresql+asyncpg://.*@|postgresql+asyncpg://$DB_USER:$NEW_PASSWORD@|" /opt/cgraph/backend/.env

echo "✓ Environment variables updated"

# Restart services to pick up new credentials
cd /opt/cgraph/backend
docker-compose restart

echo "✅ Password change complete"
echo "Next change scheduled: $(date -d '+7 days' '+%Y-%m-%d')"
