# Testing Guide

This guide covers testing practices and commands for the AI-Discover project.

## Quick Reference

### Backend Testing (Python/pytest)

```bash
# Run all tests
cd backend && pytest

# Run with coverage
cd backend && pytest --cov=app --cov-report=term-missing

# Run specific test file
cd backend && pytest tests/unit/test_auth.py

# Run specific test
cd backend && pytest tests/unit/test_auth.py::TestAuthEndpoints::test_login_valid_credentials

# Run tests by marker
cd backend && pytest -m unit       # Unit tests only
cd backend && pytest -m integration # Integration tests only
cd backend && pytest -m "not slow"  # Skip slow tests

# Run with verbose output
cd backend && pytest -v

# Run and stop on first failure
cd backend && pytest -x

# Run last failed tests
cd backend && pytest --lf
```

### Frontend Testing (TypeScript/Jest)

```bash
# Run all tests
cd frontend && npm test

# Run with coverage
cd frontend && npm run test:ci

# Run in watch mode
cd frontend && npm run test:watch

# Run specific test file
cd frontend && npm test -- Button.test.tsx

# Run tests matching pattern
cd frontend && npm test -- --testNamePattern="should handle click"

# Update snapshots
cd frontend && npm test -- -u

# Debug tests
cd frontend && npm test -- --detectOpenHandles
```

### Full Coverage Report

```bash
# Run coverage for both backend and frontend
./scripts/coverage-report.sh
```

## Writing Tests

### Backend Test Structure

```python
# tests/unit/test_feature.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.utils.test_helpers import TestHelpers


class TestFeature:
    """Test feature functionality."""

    @pytest.mark.asyncio
    async def test_feature_behavior(
        self,
        async_client: AsyncClient,
        test_user: User,
        mock_redis
    ):
        """Test specific behavior."""
        # Arrange
        data = {"key": "value"}

        # Act
        response = await async_client.post("/api/v1/feature", json=data)

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
```

### Frontend Test Structure

```typescript
// src/components/__tests__/Feature.test.tsx
import { render, screen, waitFor } from "@/test-utils";
import { Feature } from "@/components/Feature";
import { mockApiResponse } from "@/test-utils";

describe("Feature Component", () => {
  it("should render and handle user interaction", async () => {
    // Arrange
    const mockData = { id: 1, name: "Test" };
    jest.mocked(apiCall).mockResolvedValue(mockApiResponse(mockData));

    // Act
    const { user } = render(<Feature />);
    const button = screen.getByRole("button", { name: /submit/i });
    await user.click(button);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(mockData.name)).toBeInTheDocument();
    });
  });
});
```

## Test Categories

### Unit Tests

- Test individual functions/components in isolation
- Mock all external dependencies
- Should be fast and deterministic
- Aim for high coverage of business logic

### Integration Tests

- Test interaction between components
- Use real database (test database)
- Test API endpoints end-to-end
- May include external service mocks

### E2E Tests (Future)

- Test complete user workflows
- Run against deployed application
- Simulate real user behavior
- Slower but catch integration issues

## Test Fixtures

### Backend Fixtures (pytest)

Available fixtures in `conftest.py`:

- `async_client`: HTTP client for API testing
- `test_db`: Database session for test
- `test_user`: Regular user fixture
- `superuser`: Admin user fixture
- `authenticated_client`: Client with auth headers
- `mock_redis`: Mocked Redis client
- `mock_openai`: Mocked OpenAI client
- `mock_celery_task`: Mocked Celery tasks

### Frontend Test Utils

Available in `src/test-utils/`:

- `render`: Custom render with providers
- `generateMockUser`: Create test user data
- `generateMockDiscovery`: Create test discovery data
- `mockApiResponse`: Mock successful API response
- `mockApiError`: Mock API error response
- `fillForm`: Helper to fill form fields
- `waitForLoadingToFinish`: Wait for loading states

## Coverage Requirements

Both backend and frontend require **80% code coverage**:

- Lines: 80%
- Branches: 80%
- Functions: 80%
- Statements: 80%

### Viewing Coverage Reports

After running tests with coverage:

**Backend:**

- Terminal: Coverage shown in test output
- HTML: Open `backend/htmlcov/index.html`
- XML: `backend/coverage.xml` (for CI)

**Frontend:**

- Terminal: Coverage shown in test output
- HTML: Open `frontend/coverage/lcov-report/index.html`
- JSON: `frontend/coverage/coverage-summary.json`

## Testing Best Practices

### 1. Follow AAA Pattern

- **Arrange**: Set up test data and conditions
- **Act**: Execute the code being tested
- **Assert**: Verify the results

### 2. Keep Tests Independent

- Each test should be able to run in isolation
- Don't depend on test execution order
- Clean up after tests (handled by fixtures)

### 3. Use Descriptive Names

```python
# Good
async def test_user_can_login_with_valid_credentials():

# Bad
async def test_login():
```

### 4. Test One Thing

Each test should verify a single behavior or requirement.

### 5. Use Fixtures and Utilities

Don't repeat setup code - use the provided fixtures and utilities.

### 6. Mock External Dependencies

- Mock API calls to external services
- Mock time-dependent operations
- Mock file system operations

### 7. Test Edge Cases

- Empty inputs
- Invalid data
- Boundary conditions
- Error scenarios

## Debugging Tests

### Backend Debugging

```bash
# Run with pytest debugger
cd backend && pytest --pdb

# Run with more verbose output
cd backend && pytest -vv

# Show print statements
cd backend && pytest -s

# Run with logging
cd backend && pytest --log-cli-level=DEBUG
```

### Frontend Debugging

```bash
# Run with Node debugger
cd frontend && node --inspect-brk node_modules/.bin/jest --runInBand

# Run single test file in watch mode
cd frontend && npm test -- --watch Feature.test.tsx

# Show console output
cd frontend && npm test -- --verbose
```

## Continuous Integration

Tests run automatically on:

- Every push to `main` or `develop`
- Every pull request
- Manual workflow dispatch

Failed tests will:

- Block PR merging
- Prevent deployment
- Notify via GitHub Actions

## Troubleshooting

### Common Backend Issues

1. **Import errors**: Ensure you're in the backend directory and have activated the virtual environment
2. **Database errors**: Check if test database is running (PostgreSQL for integration tests)
3. **Async warnings**: Use `pytest.mark.asyncio` decorator for async tests

### Common Frontend Issues

1. **Module not found**: Run `npm install` in the frontend directory
2. **React act() warnings**: Wrap state updates in `waitFor`
3. **Transform errors**: Check Jest configuration matches project setup

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Jest documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Testing FastAPI applications](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Next.js applications](https://nextjs.org/docs/testing)
