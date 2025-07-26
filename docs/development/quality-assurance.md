# Quality Assurance Overview

This document summarizes the quality assurance measures implemented in the AI-Discover project.

## Testing Framework

### Backend (Python/FastAPI)

- **Framework**: pytest with async support
- **Coverage Tool**: pytest-cov
- **Minimum Coverage**: 80% (enforced in CI/CD)
- **Test Structure**:
  - `backend/tests/unit/` - Unit tests
  - `backend/tests/integration/` - Integration tests
  - `backend/tests/fixtures/` - Test fixtures
  - `backend/tests/utils/` - Test utilities

### Frontend (Next.js/React)

- **Framework**: Jest with React Testing Library
- **Coverage Tool**: Jest built-in coverage
- **Minimum Coverage**: 80% (enforced in CI/CD)
- **Test Structure**:
  - Component tests in `__tests__` directories
  - Test utilities in `src/test-utils/`

## Code Quality Gates

### CI/CD Pipeline Checks

1. **Linting**

   - Python: Black (formatting), Ruff (linting), mypy (type checking)
   - JavaScript/TypeScript: ESLint, TypeScript compiler

2. **Testing**

   - All tests must pass
   - Coverage must be ≥ 80% for all metrics

3. **Security Scanning**

   - Bandit (Python security)
   - pip-audit (Python dependencies)
   - npm audit (JavaScript dependencies)
   - Trivy (container scanning)
   - GitLeaks (secret scanning)
   - OWASP Dependency Check

4. **Quality Gates Job**
   - Validates coverage thresholds
   - Aggregates results from all checks
   - Blocks deployment on failure

### Pre-commit Hooks

Local checks before committing:

- Code formatting (Black, Prettier)
- Linting (Ruff, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning (detect-secrets, gitleaks)
- File validation (YAML, JSON, Markdown)
- Large file prevention
- Test execution (on push)

## Running Quality Checks

### Quick Commands

```bash
# Run all backend tests with coverage
cd backend && pytest --cov=app --cov-fail-under=80

# Run all frontend tests with coverage
cd frontend && npm run test:ci

# Run full coverage report
./scripts/coverage-report.sh

# Run pre-commit on all files
pre-commit run --all-files

# Run security scans
cd backend && bandit -r app
cd frontend && npm audit
```

### IDE Integration

Configure your IDE to run these tools automatically:

- Format on save (Black/Prettier)
- Lint on save (Ruff/ESLint)
- Type check in real-time (mypy/TypeScript)

## Coverage Reports

### Viewing Coverage

**Backend HTML Report**: `backend/htmlcov/index.html`
**Frontend HTML Report**: `frontend/coverage/lcov-report/index.html`

### Coverage Metrics

We track four coverage metrics:

- **Lines**: Percentage of code lines executed
- **Branches**: Percentage of decision branches taken
- **Functions**: Percentage of functions called
- **Statements**: Percentage of statements executed

All must be ≥ 80% for the build to pass.

## Best Practices

1. **Write Tests First** (TDD)

   - Write failing test
   - Implement feature
   - Refactor

2. **Test Pyramid**

   - Many unit tests (fast, isolated)
   - Some integration tests (component interaction)
   - Few E2E tests (complete workflows)

3. **Mock External Dependencies**

   - Use provided mocks for Redis, OpenAI, Celery
   - Keep tests deterministic and fast

4. **Continuous Improvement**
   - Monitor coverage trends
   - Add tests for bug fixes
   - Refactor complex code for testability

## Troubleshooting

### Common Issues

1. **Coverage Below Threshold**

   - Identify uncovered code: Check HTML reports
   - Add missing tests
   - Consider if code is actually needed

2. **Flaky Tests**

   - Remove time dependencies
   - Mock external services properly
   - Ensure proper async handling

3. **Slow Tests**
   - Use unit tests over integration where possible
   - Mock heavy operations
   - Parallelize test execution

## Resources

- [Testing Guide](./testing-guide.md) - Detailed testing instructions
- [Pre-commit Setup](./pre-commit-setup.md) - Local quality checks
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)

## Metrics and Monitoring

Track these metrics over time:

- Coverage percentage trends
- Test execution time
- Number of tests
- Failed build frequency
- Security vulnerability count

## Future Enhancements

Planned improvements:

- [ ] E2E testing with Playwright
- [ ] Performance testing
- [ ] Mutation testing
- [ ] Visual regression testing
- [ ] API contract testing
