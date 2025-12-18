#!/bin/bash
set -e

echo "Waiting for primary database to be ready..."
until pg_isready -h postgres-primary -p 5432 -U cgraph; do
    echo "Primary database not ready yet..."
    sleep 5
done

echo "Primary is ready. Setting up replica..."

# Remove any existing data
rm -rf /var/lib/postgresql/data/*

# Create base backup
echo "Creating base backup from primary..."
PGPASSWORD=replication123! pg_basebackup \
    -h postgres-primary \
    -p 5432 \
    -U replicator \
    -D /var/lib/postgresql/data \
    -v \
    -P \
    -R \
    -X stream \
    -C \
    -S replica_slot

# Create recovery.conf
cat > /var/lib/postgresql/data/standby.signal << 'SIGNAL'
standby_mode = 'on'
primary_conninfo = 'host=postgres-primary port=5432 user=replicator password=replication123! application_name=replica1'
primary_slot_name = 'replica_slot'
SIGNAL

echo "Starting replica..."
exec docker-entrypoint.sh postgres
