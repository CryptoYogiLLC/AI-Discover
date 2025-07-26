#!/bin/bash
set -e

echo "🧪 Running all tests for AI-Discover..."

# Backend tests
echo "🐍 Running backend tests..."
cd backend
if [ -d venv ]; then
    source venv/bin/activate
fi
pytest -v --cov=app --cov-report=term-missing --cov-report=html
cd ..

# Frontend tests
echo "⚛️  Running frontend tests..."
cd frontend
npm test
cd ..

# Security tests
echo "🔒 Running security scans..."

# Python security
echo "  - Running Bandit..."
bandit -r backend/app

echo "  - Running pip-audit..."
cd backend
pip-audit
cd ..

# JavaScript security
echo "  - Running npm audit..."
cd frontend
npm audit --production
cd ..

# Docker security
echo "  - Running Trivy..."
trivy fs .

# Linting
echo "🧹 Running linters..."

# Python linting
echo "  - Running Black..."
black --check backend/

echo "  - Running Ruff..."
ruff check backend/

echo "  - Running MyPy..."
mypy backend/

# JavaScript linting
echo "  - Running ESLint..."
cd frontend
npm run lint
cd ..

echo "✅ All tests passed!"
