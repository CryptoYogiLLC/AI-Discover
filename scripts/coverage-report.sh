#!/bin/bash
# Generate coverage reports for both backend and frontend

set -e

echo "========================================="
echo "AI-Discover Coverage Report"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend coverage
echo -e "\n${YELLOW}Running Backend Tests with Coverage...${NC}"
cd backend
if pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=json --cov-fail-under=80; then
    echo -e "${GREEN}✓ Backend tests passed with coverage >= 80%${NC}"
    
    # Extract coverage percentage
    if [ -f coverage.json ]; then
        BACKEND_COV=$(python -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}%\")")
        echo -e "Backend Coverage: ${GREEN}${BACKEND_COV}${NC}"
    fi
else
    echo -e "${RED}✗ Backend tests failed or coverage < 80%${NC}"
    exit 1
fi
cd ..

# Frontend coverage
echo -e "\n${YELLOW}Running Frontend Tests with Coverage...${NC}"
cd frontend
if npm run test:ci; then
    echo -e "${GREEN}✓ Frontend tests passed with coverage >= 80%${NC}"
    
    # Extract coverage percentage
    if [ -f coverage/coverage-summary.json ]; then
        FRONTEND_COV=$(node -e "const data=require('./coverage/coverage-summary.json'); console.log(data.total.lines.pct + '%')")
        echo -e "Frontend Coverage: ${GREEN}${FRONTEND_COV}${NC}"
    fi
else
    echo -e "${RED}✗ Frontend tests failed or coverage < 80%${NC}"
    exit 1
fi
cd ..

# Combined report
echo -e "\n========================================="
echo -e "${GREEN}Coverage Report Summary:${NC}"
echo -e "Backend:  ${BACKEND_COV:-N/A}"
echo -e "Frontend: ${FRONTEND_COV:-N/A}"
echo -e "========================================="

# Open coverage reports if running locally
if [ -z "$CI" ]; then
    echo -e "\n${YELLOW}Opening coverage reports in browser...${NC}"
    
    # Check OS and open accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open backend/htmlcov/index.html 2>/dev/null || true
        open frontend/coverage/lcov-report/index.html 2>/dev/null || true
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open backend/htmlcov/index.html 2>/dev/null || true
        xdg-open frontend/coverage/lcov-report/index.html 2>/dev/null || true
    fi
fi

echo -e "\n${GREEN}✓ All coverage checks passed!${NC}"