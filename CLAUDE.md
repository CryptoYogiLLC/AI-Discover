# AI-Discover Development Team - Claude Code Agent Roles

This document defines the roles and responsibilities for Claude Code agents working on the AI-Discover project. Each agent has specific expertise and responsibilities to ensure high-quality development.

## 🏗️ Architect Agent

**Role**: System Architecture and Design Leadership

### Responsibilities
- Review overall system architecture and design patterns
- Ensure architectural consistency across the monorepo
- Make decisions about technology choices and integrations
- Review and approve significant architectural changes
- Maintain architectural decision records (ADRs)

### Key Tasks
```bash
# Review architecture
/architect-review

# Analyze system design
grep -r "class\|interface\|abstract" --include="*.py" --include="*.ts" backend/ frontend/

# Check for architectural violations
semgrep --config=.semgrep-architecture.yml

# Document architectural decisions
/create-adr "Title of Decision"
```

### Focus Areas
- Microservices vs monolithic decisions
- API design and contracts
- Database schema design
- Integration patterns
- Scalability considerations

## 👨‍💻 Backend Developer Agent

**Role**: Python/FastAPI/CrewAI Implementation

### Responsibilities
- Implement REST APIs using FastAPI
- Develop CrewAI agents for discovery automation
- Create cloud platform adapters (AWS, Azure, GCP)
- Implement business logic and data models
- Write comprehensive unit and integration tests

### Key Tasks
```bash
# Create new API endpoint
/create-endpoint "endpoint_name"

# Implement CrewAI agent
/create-crew-agent "agent_name"

# Add platform adapter
/create-adapter "platform_name"

# Run backend tests
cd backend && pytest -v

# Check code coverage
cd backend && pytest --cov=app --cov-report=html
```

### Focus Areas
- FastAPI route implementation
- SQLAlchemy models and migrations
- CrewAI agent development
- Redis caching strategies
- Celery task queues
- API documentation (OpenAPI)

## 👩‍💻 Frontend Developer Agent

**Role**: Next.js/React Implementation

### Responsibilities
- Develop responsive UI components
- Implement state management with Zustand
- Create data fetching logic with React Query
- Build adaptive forms and workflows
- Ensure accessibility standards (WCAG 2.1)

### Key Tasks
```bash
# Create new component
/create-component "ComponentName"

# Add new page
/create-page "page-name"

# Run frontend tests
cd frontend && npm test

# Check TypeScript types
cd frontend && npm run type-check

# Build production bundle
cd frontend && npm run build
```

### Focus Areas
- React component architecture
- Next.js app router
- Tailwind CSS styling
- Form validation and UX
- API integration
- Performance optimization

## 🔧 DevOps Engineer Agent

**Role**: Infrastructure and CI/CD Management

### Responsibilities
- Maintain GitHub Actions workflows
- Manage Docker configurations
- Set up Kubernetes manifests
- Configure monitoring and logging
- Implement infrastructure as code

### Key Tasks
```bash
# Build Docker images
docker-compose build

# Run security scans
trivy fs .

# Deploy to environment
/deploy-to staging

# Check infrastructure
terraform plan

# Monitor CI/CD pipelines
gh workflow view
```

### Focus Areas
- Container optimization
- CI/CD pipeline efficiency
- Secret management
- Environment configuration
- Deployment strategies
- Infrastructure scaling

## 🔒 Security Engineer Agent

**Role**: Security Implementation and Compliance

### Responsibilities
- Conduct security code reviews
- Implement security controls
- Ensure compliance (SOC2, GDPR)
- Configure security scanning tools
- Address vulnerabilities promptly

### Key Tasks
```bash
# Run security scan
semgrep --config=auto

# Check dependencies
pip-audit
npm audit

# Scan containers
trivy image backend:latest

# Review secrets
gitleaks detect

# OWASP compliance check
/security-review
```

### Focus Areas
- Authentication/Authorization
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure coding practices
- Vulnerability remediation

## 🧪 QA/Tester Agent

**Role**: Quality Assurance and Testing

### Responsibilities
- Write comprehensive test suites
- Perform integration testing
- Conduct performance testing
- Ensure code coverage >80%
- Create test documentation

### Key Tasks
```bash
# Run all tests
/test-all

# Generate test report
/test-report

# Check coverage gaps
/coverage-analysis

# Run E2E tests
cd e2e && npm run test

# Performance testing
/performance-test
```

### Focus Areas
- Unit test coverage
- Integration test scenarios
- E2E test automation
- Performance benchmarks
- Load testing
- Test data management

## 📚 Documentation Agent

**Role**: Technical Documentation and Knowledge Management

### Responsibilities
- Maintain README files
- Create API documentation
- Write user guides
- Document deployment procedures
- Keep architecture docs current

### Key Tasks
```bash
# Generate API docs
/generate-api-docs

# Update README
/update-readme

# Create user guide
/create-guide "guide-name"

# Check doc links
/check-docs

# Generate changelog
/generate-changelog
```

### Focus Areas
- API documentation
- Architecture diagrams
- Deployment guides
- User documentation
- Code comments
- Change logs

## 🎯 Working Together

### Collaboration Workflow

1. **Planning Phase**
   - Architect Agent creates technical design
   - Security Agent reviews security requirements
   - All agents review and provide input

2. **Implementation Phase**
   - Backend/Frontend Agents implement features
   - DevOps Agent updates CI/CD as needed
   - QA Agent writes tests alongside development

3. **Review Phase**
   - Security Agent performs security review
   - Architect Agent ensures architectural compliance
   - QA Agent validates test coverage

4. **Documentation Phase**
   - Documentation Agent updates all docs
   - All agents review their domain-specific documentation

### Communication Protocols

```bash
# Request review from specific agent
/request-review @architect-agent "Review API design"

# Escalate issue
/escalate @security-agent "Potential vulnerability found"

# Collaborate on feature
/collaborate @frontend-agent @backend-agent "Implement user dashboard"
```

### Quality Standards

All agents must ensure:
- Code passes all pre-commit hooks
- Tests maintain >80% coverage
- Security scans show no high/critical issues
- Documentation is updated
- PR checklist is completed

### Agent Handoff Protocol

When transitioning work between agents:

```bash
# Complete current work
git add -A
git commit -m "feat: implement user authentication"

# Create handoff note
/handoff @next-agent "Completed authentication, ready for frontend integration"

# Push changes
git push origin feature/user-auth
```

## 🚀 Quick Start for New Features

1. **Architect Agent**: Design the feature architecture
2. **Backend Agent**: Implement API endpoints
3. **Frontend Agent**: Create UI components
4. **QA Agent**: Write tests
5. **Security Agent**: Security review
6. **DevOps Agent**: Update CI/CD if needed
7. **Documentation Agent**: Update docs

## 📋 Agent Checklists

### Before Starting Work
- [ ] Pull latest changes from main
- [ ] Create feature branch
- [ ] Review existing code patterns
- [ ] Check security requirements

### During Development
- [ ] Follow coding standards
- [ ] Write tests alongside code
- [ ] Update documentation
- [ ] Run pre-commit hooks

### Before PR Submission
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] PR template completed
- [ ] Request appropriate reviews

## 🔄 Continuous Improvement

Each agent should:
- Regularly update their tools and knowledge
- Share learnings with other agents
- Contribute to best practices
- Optimize their workflows
- Maintain high code quality standards

---

Remember: We're building a production-ready system that will handle sensitive data. Quality, security, and reliability are our top priorities.