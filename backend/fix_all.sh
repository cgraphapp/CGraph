#!/bin/bash
set -e

echo "🔧 COMPLETE DATABASE MIGRATION FIX 🔧"
echo "====================================="

# 1. FIX POSTGRESQL
echo ""
echo "1. FIXING POSTGRESQL..."
echo "----------------------"
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not installed. Installing..."
    sudo apt update
    sudo apt install postgresql postgresql-contrib -y
fi

if ! sudo systemctl is-active postgresql > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL not running. Starting..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "✅ PostgreSQL is running"

# 2. CREATE DATABASE
echo ""
echo "2. CREATING DATABASE..."
echo "----------------------"
sudo -u postgres psql -c "CREATE USER cgraph_admin WITH PASSWORD '1994Lks!Oliver2017.';" 2>/dev/null || echo "⚠️ User already exists"
sudo -u postgres psql -c "ALTER USER cgraph_admin WITH SUPERUSER CREATEROLE CREATEDB REPLICATION;" 2>/dev/null || echo "⚠️ User privileges updated"
sudo -u postgres psql -c "CREATE DATABASE cgraph_dev OWNER cgraph_admin;" 2>/dev/null || echo "⚠️ Database already exists"

# 3. TEST CONNECTION
echo ""
echo "3. TESTING CONNECTION..."
echo "----------------------"
if psql "postgresql://cgraph_admin:1994Lks\!Oliver2017.@localhost/cgraph_dev" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed!"
    echo "   Please check PostgreSQL logs: sudo tail -f /var/log/postgresql/postgresql-*.log"
    exit 1
fi

# 4. CLEAN UP ALEMBIC
echo ""
echo "4. SETTING UP ALEMBIC..."
echo "----------------------"
echo "Cleaning up old alembic..."
rm -rf alembic alembic.ini 2>/dev/null || true

echo "Initializing alembic..."
alembic init alembic

echo "Updating database URL..."
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = postgresql://cgraph_admin:1994Lks\!Oliver2017.@localhost/cgraph_dev|" alembic.ini

# 5. CREATE MIGRATION
echo ""
echo "5. CREATING MIGRATION..."
echo "----------------------"
alembic revision --autogenerate -m "Initial schema"

# 6. APPLY MIGRATION
echo ""
echo "6. APPLYING MIGRATION..."
echo "----------------------"
alembic upgrade head

echo ""
echo "====================================="
echo "✅ MIGRATION COMPLETE!"
echo "====================================="
echo ""
echo "Database: cgraph_dev"
echo "User: cgraph_admin"
echo "Connection: postgresql://cgraph_admin:********@localhost/cgraph_dev"
echo ""
echo "To verify:"
echo "  alembic current"
echo "  psql 'postgresql://cgraph_admin:1994Lks!Oliver2017.@localhost/cgraph_dev' -c '\dt'"
