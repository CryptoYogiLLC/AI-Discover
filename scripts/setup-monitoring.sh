#!/bin/bash

# AI-Discover Monitoring Setup Script
# This script sets up the monitoring stack for production deployment

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${GREEN}Setting up AI-Discover Monitoring Stack${NC}"

# Create necessary directories
echo "Creating monitoring directories..."
mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/json"
mkdir -p "$PROJECT_ROOT/monitoring/alerts"
mkdir -p "$PROJECT_ROOT/logs"

# Check if monitoring files exist
if [[ ! -f "$PROJECT_ROOT/monitoring/prometheus.yml" ]]; then
    echo -e "${YELLOW}Warning: prometheus.yml not found${NC}"
fi

if [[ ! -f "$PROJECT_ROOT/monitoring/grafana/provisioning/datasources/prometheus.yml" ]]; then
    echo -e "${YELLOW}Warning: Grafana datasources configuration not found${NC}"
fi

# Create curl format file for performance testing
cat > "$PROJECT_ROOT/curl-format.txt" << 'EOF'
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
EOF

echo "Created curl format file for performance testing"

# Create a simple load test script
cat > "$PROJECT_ROOT/scripts/load-test.sh" << 'EOF'
#!/bin/bash
# Simple load test script for AI-Discover

API_URL="${1:-http://localhost:8800}"
CONCURRENT="${2:-10}"
REQUESTS="${3:-100}"

echo "Load testing $API_URL with $CONCURRENT concurrent requests ($REQUESTS total)"

# Install Apache Bench if not present
if ! command -v ab &> /dev/null; then
    echo "Installing Apache Bench..."
    sudo apt-get update && sudo apt-get install -y apache2-utils
fi

# Run load test
ab -n $REQUESTS -c $CONCURRENT -H "Accept: application/json" "$API_URL/health"
EOF

chmod +x "$PROJECT_ROOT/scripts/load-test.sh"
echo "Created load test script"

# Create monitoring check script
cat > "$PROJECT_ROOT/scripts/check-monitoring.sh" << 'EOF'
#!/bin/bash
# Check monitoring services status

echo "Checking monitoring services..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✓ Prometheus is healthy"
else
    echo "✗ Prometheus is not responding"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✓ Grafana is healthy"
else
    echo "✗ Grafana is not responding"
fi

# Check if metrics are being scraped
TARGETS=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length' 2>/dev/null || echo "0")
echo "Active Prometheus targets: $TARGETS"

# Check for alerts
ALERTS=$(curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts | length' 2>/dev/null || echo "0")
echo "Active alerts: $ALERTS"
EOF

chmod +x "$PROJECT_ROOT/scripts/check-monitoring.sh"
echo "Created monitoring check script"

# Create alert test script
cat > "$PROJECT_ROOT/scripts/test-alerts.sh" << 'EOF'
#!/bin/bash
# Test alert configurations

echo "Testing alert configurations..."

# Check if alerting rules are valid
docker run --rm -v "$PWD/monitoring:/monitoring" prom/prometheus:latest promtool check rules /monitoring/alerts/*.yml

echo "Alert rules validated"
EOF

chmod +x "$PROJECT_ROOT/scripts/test-alerts.sh"
echo "Created alert test script"

echo -e "${GREEN}Monitoring setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Ensure monitoring services are included in docker-compose.prod.yml"
echo "2. Start monitoring stack: docker-compose -f docker-compose.prod.yml up -d prometheus grafana"
echo "3. Access Grafana at http://localhost:3000 (admin/GRAFANA_ADMIN_PASSWORD)"
echo "4. Run ./scripts/check-monitoring.sh to verify setup"
echo ""
echo "Monitoring endpoints:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo "- Metrics: http://localhost:8800/metrics"