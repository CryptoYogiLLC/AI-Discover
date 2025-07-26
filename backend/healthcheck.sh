#!/bin/sh
# Health check script for backend
# Note: Backend runs on port 8000 internally (mapped to 8800 externally)

curl -f http://localhost:8000/health || exit 1
