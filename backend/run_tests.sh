#!/bin/bash
# Script to run tests locally in Docker

echo "Running backend tests in Docker..."

# Build requirements files
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "\
  pip install pip-tools && \
  pip-compile requirements.in -o requirements.txt && \
  pip-compile requirements-test.in -o requirements-test.txt \
"

# Run MyPy
echo "Running MyPy..."
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "\
  pip install -r requirements.txt && \
  pip install mypy types-passlib types-python-jose types-redis && \
  python -m mypy app/ --ignore-missing-imports \
"

echo "Tests completed!"
