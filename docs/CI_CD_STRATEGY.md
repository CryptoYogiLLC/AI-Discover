# CI/CD Strategy

## Overview

Our CI/CD pipeline uses a three-tier approach to provide fast feedback while maintaining code quality.

## Tiers

### 1. Local Checks (Pre-commit)
**When:** Before every commit
**Duration:** < 10 seconds
**Checks:**
- Code formatting (Black, Prettier)
- Linting (Ruff, ESLint)
- File hygiene (trailing spaces, file size)
- Secret detection

### 2. Quick CI
**When:** Every push to feature branches
**Duration:** < 1 minute
**Checks:**
- All formatting and linting
- Type checking (MyPy, TypeScript)
- Unit tests (if changed)

### 3. Full CI
**When:** 
- PRs to main/staging branches
- Daily scheduled runs
- Manual trigger
**Duration:** 5-10 minutes
**Checks:**
- Everything from Quick CI
- Integration tests
- Docker builds
- Security scanning
- Performance tests

## Special Cases

### Dependabot PRs
- Only run Quick CI initially
- Run Full CI only after approval
- Auto-merge if all checks pass

### Documentation Changes
- Skip CI with `[skip ci]` in commit message
- Only run markdown linting

### Hotfixes
- Can bypass certain checks with `[hotfix]` tag
- Still runs critical security checks

## Local Development

### Initial Setup
```bash
./scripts/setup-dev.sh
```

### Before Committing
Pre-commit hooks run automatically. To run manually:
```bash
pre-commit run --all-files
```

### Before Pushing
```bash
./scripts/test-local.sh
```

## Bypassing Checks

**Use sparingly and document why:**

```bash
# Skip pre-commit for emergency fix
git commit --no-verify -m "hotfix: critical production issue"

# Skip CI checks
git commit -m "docs: update changelog [skip ci]"
```

## Reducing CI Time

1. **Cache dependencies** - Already implemented
2. **Parallel jobs** - Run backend/frontend tests simultaneously
3. **Conditional checks** - Only test changed code
4. **Fail fast** - Stop on first failure in non-critical checks