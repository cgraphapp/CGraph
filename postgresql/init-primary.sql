-- Create replication user
CREATE USER replicator WITH REPLICATION PASSWORD 'replication123!';

-- Create replication slot
SELECT pg_create_physical_replication_slot('replica_slot', true);

-- Grant permissions
GRANT CONNECT ON DATABASE cgraph TO replicator;

-- Create test table
CREATE TABLE IF NOT EXISTS test_replication (
    id SERIAL PRIMARY KEY,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_replication (message) VALUES ('Primary database initialized');
