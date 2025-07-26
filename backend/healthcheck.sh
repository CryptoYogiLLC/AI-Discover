#!/bin/sh
# Health check script for backend

curl -f http://localhost:8000/health || exit 1
