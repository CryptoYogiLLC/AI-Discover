#!/bin/bash
set -e

echo "🚀 Setting up AI-Discover development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not installed."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 18+ is required but not installed."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    exit 1
fi

echo "✅ All prerequisites met!"

# Create virtual environment for backend
echo "🐍 Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pip-tools

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f requirements.in ]; then
    pip-compile requirements.in
    pip-compile requirements-dev.in
    pip-compile requirements-test.in
fi

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
fi

cd ..

# Install Node dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Application
ENVIRONMENT=development
DEBUG=true

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_discover

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# AI/ML
OPENAI_API_KEY=your-openai-api-key

# Cloud Providers (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
GCP_PROJECT_ID=
GCP_SERVICE_ACCOUNT_KEY=
EOF
    echo "⚠️  Please update .env with your actual credentials!"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p uploads

# Initialize database
echo "🗄️  Starting database services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
cd backend
if [ -f alembic.ini ]; then
    alembic upgrade head
fi
cd ..

echo "✅ Development environment setup complete!"
echo ""
echo "To start the application, run:"
echo "  docker-compose up"
echo ""
echo "Or to run services individually:"
echo "  Backend: cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Happy coding! 🎉"