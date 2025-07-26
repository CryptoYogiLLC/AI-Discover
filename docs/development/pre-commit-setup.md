# Pre-commit Setup Guide

This guide will help you set up pre-commit hooks for the AI-Discover project to ensure code quality and consistency before committing changes.

## Overview

Pre-commit hooks run automatically before each commit to check your code for:
- Code formatting (Black for Python, Prettier for JS/TS)
- Linting issues (Ruff for Python, ESLint for JS/TS)
- Type checking (mypy for Python, TypeScript)
- Security vulnerabilities
- Large files and merge conflicts
- Test failures

## Installation

### 1. Install pre-commit

```bash
# Using pip (recommended for this project)
pip install pre-commit

# Or using homebrew on macOS
brew install pre-commit

# Verify installation
pre-commit --version
```

### 2. Install the git hook scripts

From the project root directory:

```bash
pre-commit install
```

This will install the pre-commit script in `.git/hooks/pre-commit`.

### 3. (Optional) Install commit-msg hooks

If you want to enforce conventional commit messages:

```bash
pre-commit install --hook-type commit-msg
```

## Usage

### Automatic Runs

Once installed, pre-commit will run automatically when you try to commit:

```bash
git add .
git commit -m "feat: add new feature"
# Pre-commit hooks will run here
```

### Manual Runs

Run all hooks on all files:

```bash
pre-commit run --all-files
```

Run a specific hook:

```bash
# Run only Black formatter
pre-commit run black --all-files

# Run only ESLint
pre-commit run eslint --all-files
```

Run on specific files:

```bash
pre-commit run --files backend/app/main.py frontend/src/app/page.tsx
```

### Skipping Hooks

If you need to bypass pre-commit hooks (not recommended):

```bash
git commit --no-verify -m "emergency fix"
```

## Hooks Configuration

Our pre-commit configuration includes:

### Python Hooks
- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **mypy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **pytest-check**: Runs unit tests on push

### JavaScript/TypeScript Hooks
- **ESLint**: Linting for JS/TS files
- **Prettier**: Code formatting
- **jest-check**: Runs tests on push

### General Hooks
- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML files
- **check-json**: Validates JSON files
- **check-added-large-files**: Prevents large files (>1MB)
- **detect-private-key**: Prevents committing private keys
- **gitleaks**: Scans for secrets

### Docker & Config Hooks
- **hadolint**: Dockerfile linting
- **yamllint**: YAML linting
- **markdownlint**: Markdown linting

## Troubleshooting

### Hook Failures

If a hook fails:

1. **Read the error message** - It usually tells you exactly what's wrong
2. **Fix the issue** - Make the necessary changes
3. **Stage the fixes** - `git add <fixed-files>`
4. **Commit again** - The hooks will run again

### Common Issues

#### Python Import Errors

If mypy fails with import errors:

```bash
cd backend
pip install -e .
```

#### ESLint Configuration Not Found

If ESLint can't find the config:

```bash
cd frontend
npm install
```

#### Slow Hook Performance

Some hooks can be slow on large codebases. You can:

1. Run on changed files only (default behavior)
2. Skip specific hooks temporarily:
   ```bash
   SKIP=mypy,eslint git commit -m "message"
   ```

### Updating Hooks

To update to the latest hook versions:

```bash
pre-commit autoupdate
```

Then commit the changes to `.pre-commit-config.yaml`.

## Best Practices

1. **Don't skip hooks** - They're there to maintain code quality
2. **Fix issues immediately** - Don't let them accumulate
3. **Run before pushing** - Use `pre-commit run --all-files` before pushing to catch any issues
4. **Keep hooks updated** - Run `pre-commit autoupdate` periodically
5. **Configure your IDE** - Many IDEs can run these tools automatically

## IDE Integration

### VS Code

Install these extensions:
- Python: Black Formatter
- ESLint
- Prettier
- mypy (Pylance includes this)

### PyCharm

- Enable Black: Settings → Tools → Black
- Enable Ruff: Settings → Tools → External Tools → Add Ruff
- Enable ESLint: Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint

## CI/CD Integration

The same checks run in CI/CD, so fixing pre-commit issues locally saves CI time and prevents failed builds.

## Additional Resources

- [pre-commit documentation](https://pre-commit.com/)
- [Black documentation](https://black.readthedocs.io/)
- [Ruff documentation](https://beta.ruff.rs/docs/)
- [ESLint documentation](https://eslint.org/)
- [Prettier documentation](https://prettier.io/)