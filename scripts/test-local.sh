#!/bin/bash
# Run tests locally before pushing

echo "🧪 Running local tests..."

# Backend checks
echo ""
echo "=== BACKEND CHECKS ==="
cd backend

echo "▶️  Black formatting check..."
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "pip install black && black --check ."

echo "▶️  Ruff linting..."
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "pip install ruff && ruff check ."

echo "▶️  MyPy type checking..."
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "pip install mypy types-passlib types-python-jose types-redis && mypy app/ --ignore-missing-imports"

cd ..

# Frontend checks
echo ""
echo "=== FRONTEND CHECKS ==="
cd frontend

echo "▶️  ESLint..."
npm run lint || yarn lint

echo "▶️  Prettier check..."
npm run prettier:check || yarn prettier:check

cd ..

echo ""
echo "✅ All local tests complete!"
