#!/bin/bash
set -e

echo "🔧 FIXING POSTGRESQL CONFIGURATION 🔧"

# Find PostgreSQL config directory
PG_CONF=$(find /etc/postgresql -name "postgresql.conf" | head -1)
PG_HBA=$(find /etc/postgresql -name "pg_hba.conf" | head -1)
PG_DIR=$(dirname "$PG_CONF")

echo "PostgreSQL config: $PG_CONF"
echo "PG_HBA config: $PG_HBA"

# Backup original configs
sudo cp "$PG_CONF" "${PG_CONF}.backup"
sudo cp "$PG_HBA" "${PG_HBA}.backup"

# Update postgresql.conf to listen on localhost
sudo sed -i "s/^#listen_addresses =.*/listen_addresses = 'localhost'/g" "$PG_CONF"
sudo sed -i "s/^listen_addresses =.*/listen_addresses = 'localhost'/g" "$PG_CONF"

# Ensure port is 5432
sudo sed -i "s/^#port =.*/port = 5432/g" "$PG_CONF"
sudo sed -i "s/^port =.*/port = 5432/g" "$PG_CONF"

# Update pg_hba.conf to allow password authentication
if ! sudo grep -q "host.*all.*all.*127.0.0.1/32.*md5" "$PG_HBA"; then
    echo "Adding localhost authentication rule..."
    sudo tee -a "$PG_HBA" << 'CONF'
# Allow local connections with password
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
CONF
fi

# Restart PostgreSQL
echo "Restarting PostgreSQL..."
sudo systemctl restart postgresql

# Wait for restart
sleep 2

# Test connection
echo "Testing connection..."
if psql "postgresql://cgraph_admin:1994Lks\!Oliver2017.@localhost/cgraph_dev" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ PostgreSQL connection successful!"
else
    echo "❌ Still failing. Trying alternative connection methods..."
    
    # Test with different connection methods
    echo "Testing as postgres user..."
    sudo -u postgres psql -c "SELECT 1;"
    
    echo "Testing local socket connection..."
    psql -U cgraph_admin -d cgraph_dev -h /var/run/postgresql -c "SELECT 1;" || true
    
    echo "Checking PostgreSQL logs..."
    sudo tail -20 /var/log/postgresql/postgresql-*.log
fi
