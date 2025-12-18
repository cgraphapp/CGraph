# Incident: Database Connection Pool Exhausted

## Detection
- Alert: `RDSConnectionPoolExhausted` (connections > 80 of max)
- Symptom: API responses with "too many connections" errors
- Timeline: Usually happens during traffic spike

## Diagnosis

### Step 1: Verify the issue
\`\`\`bash
kubectl exec -it cgraph-backend-0 -- python -c "
from sqlalchemy import text
from app.database import engine
conn = engine.connect()
result = conn.execute(text('SHOW max_connections'))
print('Max connections:', result.fetchone())
"
\`\`\`

### Step 2: Check query status
\`\`\`sql
-- Connect directly to RDS
SELECT pid, user, query_start, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start DESC;
\`\`\`

### Step 3: Identify long-running queries
\`\`\`sql
SELECT pid, user, query_start, now() - query_start as duration, query
FROM pg_stat_activity
WHERE now() - query_start > interval '5 minutes'
ORDER BY duration DESC;
\`\`\`

## Resolution

### Option 1: Terminate long-running queries
\`\`\`sql
-- Kill specific query
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid <> pg_backend_pid()
  AND query ~ 'EXPENSIVE_QUERY'
  AND query_start < now() - interval '30 minutes';
\`\`\`

### Option 2: Scale up application instances
\`\`\`bash
# Increase replicas (reduces queries per instance)
kubectl scale deployment cgraph-backend --replicas=5 -n cgraph

# Monitor
kubectl top nodes
kubectl top pods -n cgraph
\`\`\`

### Option 3: Increase RDS pool size
\`\`\`bash
# Update RDS max_connections parameter group
# This requires RDS restart (5-10 min downtime)
aws rds modify-db-parameter-group \
  --db-parameter-group-name cgraph-params \
  --parameters "ParameterName=max_connections,ParameterValue=200,ApplyMethod=immediate"
\`\`\`

## Prevention

1. Implement connection pooling on app side (PgBouncer)
2. Set query timeouts: `statement_timeout = '5min'`
3. Monitor slow queries regularly
4. Use read replicas for read-heavy queries
5. Add alerts at 60% and 80% utilization

## Post-Incident

- [ ] Root cause analysis
- [ ] Update alerting thresholds
- [ ] Document learnings
- [ ] Update runbooks