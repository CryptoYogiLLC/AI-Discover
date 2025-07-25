# AI-Discover: Automated Application Discovery System

An intelligent, automated application discovery and assessment platform that leverages AI agents to analyze applications and provide 6R cloud migration recommendations.

## 🚀 Features

- **Automated Discovery**: Platform-agnostic data collection from AWS, Azure, GCP, and on-premises environments
- **AI-Powered Analysis**: CrewAI agents for intelligent gap analysis and recommendations
- **Adaptive Workflows**: Smart (automated) and Traditional (manual) data collection paths
- **6R Recommendations**: Comprehensive cloud migration strategy assessment
- **Enterprise Ready**: SOC2/GDPR compliant with full audit trails
- **Containerized Deployment**: Docker-based architecture for flexible deployment

## 📁 Project Structure

```
ai-discover/
├── backend/            # Python/FastAPI backend with CrewAI agents
├── frontend/           # Next.js frontend application
├── shared/             # Shared types and schemas
├── infrastructure/     # Docker, Kubernetes, and IaC configurations
├── docs/               # Documentation
└── scripts/            # Development and deployment scripts
```

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **AI Framework**: CrewAI
- **Database**: PostgreSQL with SQLAlchemy
- **Caching**: Redis
- **Task Queue**: Celery

### Frontend
- **Framework**: Next.js 14+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **API Client**: React Query

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Security**: HashiCorp Vault
- **Monitoring**: OpenTelemetry

## 🚦 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/[your-org]/ai-discover.git
cd ai-discover
```

2. Set up development environment:
```bash
./scripts/setup-dev.sh
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🤖 AI Development Team

This project is developed using an AI-powered development approach with Claude Code agents assigned to different roles:

- **Architect Agent**: System design and architecture decisions
- **Backend Developer Agent**: Python/FastAPI implementation
- **Frontend Developer Agent**: Next.js/React implementation
- **DevOps Engineer Agent**: CI/CD and infrastructure
- **Security Engineer Agent**: Security scanning and compliance
- **QA/Tester Agent**: Test implementation and quality assurance
- **Documentation Agent**: Technical documentation

See [CLAUDE.md](./CLAUDE.md) for detailed agent instructions.

## 🔒 Security

This project implements comprehensive security measures:

- **SAST**: Semgrep, Bandit
- **Dependency Scanning**: Snyk, npm audit, pip-audit
- **Container Scanning**: Trivy, Grype
- **Secret Scanning**: GitLeaks
- **DAST**: OWASP ZAP (staging)

All code must pass security scans before merging.

## 📖 Documentation

- [Architecture Overview](./docs/architecture/README.md)
- [API Documentation](./docs/api/README.md)
- [Development Guide](./docs/development/README.md)
- [Deployment Guide](./docs/deployment/README.md)

## 🤝 Contributing

Please read our [Contributing Guide](./CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- Built with CrewAI for intelligent automation
- Inspired by cloud migration best practices
- Developed using AI-powered development methodology