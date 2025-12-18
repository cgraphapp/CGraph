#!/bin/bash
sudo -u postgres psql << 'PSQL'
CREATE ROLE cgraph_admin WITH LOGIN PASSWORD '1994Lks!Oliver2017.';
ALTER ROLE cgraph_admin WITH SUPERUSER CREATEROLE CREATEDB REPLICATION;

CREATE DATABASE cgraph_dev OWNER cgraph_admin;
CREATE DATABASE cgraph_test OWNER cgraph_admin;
CREATE DATABASE cgraph_prod OWNER cgraph_admin;

GRANT ALL PRIVILEGES ON DATABASE cgraph_dev TO cgraph_admin;
GRANT ALL PRIVILEGES ON DATABASE cgraph_test TO cgraph_admin;
GRANT ALL PRIVILEGES ON DATABASE cgraph_prod TO cgraph_admin;

-- List databases
\l

-- Exit psql
\q
PSQL
