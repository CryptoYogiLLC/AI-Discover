# Contributing to AI-Discover

Thank you for your interest in contributing to AI-Discover! This document provides guidelines and instructions for contributing to the project.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone https://github.com/[your-username]/ai-discover.git
   cd ai-discover
   ```

3. Set up the development environment:

   ```bash
   ./scripts/setup-dev.sh
   ```

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

### 2. Make Your Changes

Follow these guidelines:

- Write clean, readable code
- Follow existing code patterns
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Commit Your Changes

We use conventional commits:

```bash
git commit -m "type(scope): description"
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/updates
- `chore`: Maintenance tasks

Examples:

```bash
git commit -m "feat(backend): add AWS adapter for EC2 discovery"
git commit -m "fix(frontend): resolve form validation issue"
git commit -m "docs: update API documentation"
```

### 4. Run Tests

Before pushing, ensure all tests pass:

```bash
./scripts/test-all.sh
```

### 5. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

1. Go to the GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template
5. Request reviews from appropriate team members

## 📋 Pull Request Guidelines

### PR Requirements

- [ ] All tests pass
- [ ] Code coverage maintained or improved
- [ ] Security scans pass
- [ ] Documentation updated
- [ ] PR template completed
- [ ] Appropriate reviewers assigned

### PR Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one approval required
3. **Security Review**: For security-sensitive changes
4. **Architecture Review**: For significant architectural changes

## 🏗️ Architecture Guidelines

### Backend (Python/FastAPI)

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all public functions
- Keep functions small and focused
- Use dependency injection
- Follow SOLID principles

Example:

```python
from typing import List, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse

async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user in the database.

    Args:
        user_data: User creation data
        db: Database session

    Returns:
        Created user data
    """
    # Implementation here
    pass
```

### Frontend (Next.js/React)

- Use functional components with hooks
- Implement proper TypeScript types
- Follow React best practices
- Keep components small and reusable
- Use proper state management (Zustand)

Example:

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  onClick,
  children
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-md font-medium',
        variants[variant],
        sizes[size]
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

## 🧪 Testing Guidelines

### Backend Testing

- Write unit tests for all business logic
- Include integration tests for API endpoints
- Use pytest fixtures for test data
- Aim for >80% code coverage

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "secure123"}  # pragma: allowlist secret
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### Frontend Testing

- Write unit tests for components
- Include integration tests for pages
- Use React Testing Library
- Test user interactions

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## 🔒 Security Guidelines

- Never commit secrets or credentials
- Validate all user input
- Use parameterized queries
- Implement proper authentication/authorization
- Follow OWASP best practices
- Report security issues privately

## 📚 Documentation

- Update README.md for significant changes
- Add/update API documentation
- Include code comments for complex logic
- Create architecture decision records (ADRs)
- Update user guides as needed

## 🐛 Reporting Issues

### Bug Reports

Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots if applicable

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality

## 💬 Getting Help

- Check existing documentation
- Search closed issues
- Ask in discussions
- Contact maintainers

## 🎉 Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in commits

Thank you for contributing to AI-Discover!
