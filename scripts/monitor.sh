#!/bin/bash

# CGRAPH Monitoring Script

API_URL="http://localhost:8000"
ALERT_EMAIL="admin@yourdomain.com"

# Check backend health
check_backend() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
    if [ "$response" != "200" ]; then
        echo "❌ Backend unhealthy: HTTP $response"
        send_alert "Backend Health Check Failed"
        return 1
    fi
    echo "✅ Backend: OK"
    return 0
}

# Check database connection
check_database() {
    docker exec cgraph-postgres pg_isready -U postgres > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Database connection failed"
        send_alert "Database Connection Failed"
        return 1
    fi
    echo "✅ Database: OK"
    return 0
}

# Check Redis
check_redis() {
    docker exec cgraph-redis redis-cli ping > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Redis unhealthy"
        send_alert "Redis Connection Failed"
        return 1
    fi
    echo "✅ Redis: OK"
    return 0
}

# Check disk space
check_disk_space() {
    usage=$(df /opt/cgraph | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 80 ]; then
        echo "⚠️ Disk usage high: ${usage}%"
        send_alert "Disk Space Warning: ${usage}%"
        return 1
    fi
    echo "✅ Disk: ${usage}% used"
    return 0
}

# Check memory
check_memory() {
    free=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
    if [ "$free" -gt 85 ]; then
        echo "⚠️ Memory usage high: ${free}%"
        send_alert "Memory Warning: ${free}%"
        return 1
    fi
    echo "✅ Memory: ${free}% used"
    return 0
}

# Send alert email
send_alert() {
    message=$1
    echo "$message" | mail -s "[CGRAPH ALERT] $message" $ALERT_EMAIL
}

# Run all checks
echo "🔍 Running health checks at $(date)"
check_backend
check_database
check_redis
check_disk_space
check_memory
echo "✅ Health check completed"

