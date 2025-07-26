#!/bin/bash
# Developer setup script

echo "🚀 Setting up development environment..."

# Install pre-commit
echo "📦 Installing pre-commit..."
pip install pre-commit

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Run pre-commit on all files to check current state
echo "🔍 Running pre-commit checks on all files..."
pre-commit run --all-files || true

echo "✅ Development environment setup complete!"
echo ""
echo "Pre-commit hooks are now installed and will run automatically on git commit."
echo "You can also run checks manually with: pre-commit run --all-files"
