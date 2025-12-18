#!/bin/bash
set -e

echo "Starting replica setup..."

# Wait for primary to be ready
echo "Waiting for primary database to be ready..."
until pg_isready -h postgres-primary -p 5432 -U cgraph; do
  echo "Primary not ready yet, waiting..."
  sleep 5
done

echo "Primary is ready. Setting up replica..."

# Clean any existing data (optional, careful!)
if [ -f "/var/lib/postgresql/data/postmaster.pid" ]; then
  echo "Cleaning old data directory..."
  rm -rf /var/lib/postgresql/data/*
fi

# Create base backup
echo "Creating base backup from primary..."
PGPASSWORD=securepwd123! pg_basebackup \
  -h postgres-primary \
  -p 5432 \
  -D /var/lib/postgresql/data \
  -U cgraph \
  -v \
  -P \
  -R \
  -X stream \
  -C \
  -S replica_slot

echo "Replica setup complete!"
