-- Enable replication for replicator user
ALTER USER replicator WITH REPLICATION;

-- Create replication slot if not exists
SELECT * FROM pg_create_physical_replication_slot('replica_slot', true);
