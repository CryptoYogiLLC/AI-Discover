# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Commands

### Backend Development
```bash
# Start backend with hot reload
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run backend tests
cd backend && pytest -v

# Run specific test
cd backend && pytest -v tests/test_main.py::test_function_name

# Check test coverage
cd backend && pytest --cov=app --cov-report=html

# Linting and formatting
black backend/           # Format code
ruff check backend/      # Lint code
mypy backend/           # Type checking

# Database migrations
cd backend && alembic revision --autogenerate -m "description"
cd backend && alembic upgrade head
```

### Frontend Development
```bash
# Start frontend dev server
cd frontend && npm run dev

# Run frontend tests
cd frontend && npm test

# Run single test file
cd frontend && npm test -- src/app/__tests__/layout.test.tsx

# Type checking and linting
cd frontend && npm run type-check
cd frontend && npm run lint
cd frontend && npm run format:check

# Build production bundle
cd frontend && npm run build
```

### Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild containers
docker-compose build --no-cache

# Access services
# Frontend: http://localhost:3300
# Backend API: http://localhost:8800
# API Docs: http://localhost:8800/docs
# Flower (Celery): http://localhost:5555
```

### Security Scanning
```bash
# Python security
bandit -r backend/app
pip-audit

# JavaScript security
cd frontend && npm audit

# Container security
trivy fs .

# Secret scanning
gitleaks detect
```

## High-Level Architecture

### Monorepo Structure
This is a monorepo containing both backend (Python/FastAPI) and frontend (Next.js) applications that work together to provide an AI-powered application discovery platform.

### Backend Architecture (FastAPI + CrewAI)
- **API Layer** (`backend/app/api/v1/`): RESTful endpoints organized by domain
  - Auth endpoints handle JWT-based authentication
  - Discovery endpoints manage the AI discovery process
  - Collection flows handle adaptive data collection workflows
  
- **Core Services** (`backend/app/core/`):
  - Database connection pooling with SQLAlchemy async
  - Redis for caching and Celery task broker
  - Middleware for CORS, logging, and error handling
  
- **AI Integration**: CrewAI agents analyze applications and provide 6R migration recommendations
  - Discovery service orchestrates multiple AI agents
  - Adapters for AWS, Azure, and GCP platforms
  
- **Async Task Processing**: Celery workers handle long-running discovery tasks

### Frontend Architecture (Next.js + React)
- **App Router**: Uses Next.js 14+ app directory structure
- **State Management**: Zustand for global state
- **Data Fetching**: React Query (TanStack Query) for server state
- **Styling**: Tailwind CSS with component-level styles
- **Forms**: React Hook Form with Zod validation

### Key Architectural Patterns

1. **Adapter Pattern**: Cloud platform adapters (`backend/app/api/v1/endpoints/adapters.py`) provide unified interface for AWS/Azure/GCP

2. **Repository Pattern**: Database operations abstracted through SQLAlchemy models

3. **Service Layer**: Business logic separated from API endpoints in service modules

4. **Async-First**: Both FastAPI backend and Next.js frontend leverage async patterns

5. **Container-Based**: All services run in Docker containers for consistency

## Critical Integration Points

### API Communication
- Frontend expects backend at `NEXT_PUBLIC_API_URL` (default: http://localhost:8030)
- All API calls use JWT tokens stored in httpOnly cookies
- API responses follow consistent schema patterns defined in `backend/app/schemas/`

### Database Schema
- PostgreSQL with async SQLAlchemy ORM
- Models in `backend/app/models/` define schema
- Alembic manages migrations

### Task Queue
- Celery workers process discovery tasks asynchronously
- Redis serves as message broker
- Results stored in Redis with TTL

### Security Requirements
- All endpoints require authentication except `/api/v1/auth/*`
- Input validation on all user inputs
- CORS configured for frontend origin only
- Secrets managed via environment variables

## Development Workflow

1. **Feature Development**:
   - Create feature branch from `develop`
   - Implement with tests (maintain >80% coverage)
   - Run linting and security scans
   - Submit PR with all checks passing

2. **Testing Strategy**:
   - Unit tests alongside implementation
   - Integration tests in `docker-compose.test.yml`
   - E2E tests for critical user flows

3. **Pre-commit Checks**:
   - Black formatting (Python)
   - Ruff linting (Python)
   - ESLint (JavaScript)
   - Type checking (both)

## AI Agent Development

When implementing CrewAI agents:
1. Define agent in `backend/app/services/discovery.py`
2. Create specific task handlers
3. Implement platform-specific data collection
4. Return structured 6R recommendations

## Common Pitfalls to Avoid

1. **Don't forget async**: Backend uses async SQLAlchemy - use `async def` and `await`
2. **Environment variables**: Always check `.env.example` for required vars (OpenAI API key is required)
3. **CORS issues**: Frontend/backend on different ports - CORS must be configured
4. **Database connections**: Use dependency injection for DB sessions
5. **Task timeouts**: Long-running tasks must use Celery, not block API requests
6. **Python version**: Backend uses Python 3.13 - ensure Dockerfile paths match
7. **ESLint compatibility**: Use @typescript-eslint v8+ with ESLint v9
8. **Docker volumes**: Production containers don't need development volume mounts
9. **Celery Beat**: Use `/tmp/celerybeat-schedule` for schedule file to avoid permission issues
10. **Next.js config**: Remove deprecated `swcMinify` option in Next.js 15+

## Performance Considerations

- Use Redis caching for frequently accessed data
- Implement pagination for list endpoints
- Use React Query's caching on frontend
- Optimize Docker images with multi-stage builds
- Database queries should use eager loading to avoid N+1

## Port Configuration

The application uses non-standard ports to avoid conflicts:
- Frontend: 3300 (dev server)
- Backend: 8800 (API server)  
- PostgreSQL: 5442 (mapped from 5432)
- Redis: 6479 (mapped from 6379)
- Flower: 5555 (Celery monitoring)