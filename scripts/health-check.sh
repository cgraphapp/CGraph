#!/bin/bash
# Script: scripts/health-check.sh

set -e

API_URL="https://cgraph.org"
SERVICES=()
FAILED=0

echo "🏥 CGRAPH Health Check - $(date)"
echo "=================================================="

# Check Nginx
echo -n "🌐 Nginx... "
if docker ps | grep -q cgraph-nginx; then
  echo "✓ Running"
else
  echo "✗ Not running"
  FAILED=$((FAILED + 1))
fi

# Check Backend API
echo -n "🚀 Backend API... "
if curl -s -f "$API_URL/api/v1/health" > /dev/null 2>&1; then
  echo "✓ Responding"
else
  echo "✗ Not responding"
  FAILED=$((FAILED + 1))
fi

# Check Database
echo -n "🗄️  PostgreSQL... "
if docker exec cgraph-db-primary psql -U cgraph -d cgraph -c "SELECT 1" > /dev/null 2>&1; then
  echo "✓ Connected"
else
  echo "✗ Connection failed"
  FAILED=$((FAILED + 1))
fi

# Check Redis
echo -n "⚡ Redis... "
if docker exec cgraph-redis redis-cli ping > /dev/null 2>&1; then
  echo "✓ Responding"
else
  echo "✗ Not responding"
  FAILED=$((FAILED + 1))
fi

# Check Frontend
echo -n "⚛️  Frontend... "
if curl -s -f "$API_URL/" > /dev/null 2>&1; then
  echo "✓ Responding"
else
  echo "✗ Not responding"
  FAILED=$((FAILED + 1))
fi

# Check SSL Certificate
echo -n "🔒 SSL Certificate... "
EXPIRY=$(echo | openssl s_client -servername cgraph.org -connect cgraph.org:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)
if [ -n "$EXPIRY" ]; then
  echo "✓ Valid until $EXPIRY"
else
  echo "✗ Certificate issue"
  FAILED=$((FAILED + 1))
fi

# Disk Space
echo -n "💾 Disk Space... "
USAGE=$(df /opt/cgraph | tail -1 | awk '{print $5}')
if [ "${USAGE%\%}" -lt 80 ]; then
  echo "✓ $USAGE used"
else
  echo "⚠️  $USAGE used"
fi

# Memory Usage
echo -n "🧠 Memory... "
MEMORY=$(free | grep Mem | awk '{printf "%.0f%%", $3/$2 * 100}')
echo "✓ $MEMORY used"

echo "=================================================="
if [ $FAILED -eq 0 ]; then
  echo "✅ All systems operational"
  exit 0
else
  echo "❌ $FAILED service(s) failed"
  exit 1
fi
