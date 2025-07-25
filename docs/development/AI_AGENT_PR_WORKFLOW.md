# AI Agent Workflow for Pull Request Management

## Overview

This document describes how to use Claude Code agents to manage pull requests, especially Dependabot updates, in the AI-Discover project.

## Agent Roles and Responsibilities

### 1. 🔒 Security Engineer Agent

**When to invoke**: For all dependency updates, especially security-related ones

```bash
# Review security implications of dependency updates
/security-review

# The agent will:
# - Check CVE databases for known vulnerabilities
# - Review changelog for security fixes
# - Assess risk level of updates
# - Recommend merge priority
```

**Example workflow**:

```bash
# 1. Start security review for a PR
gh pr view 1 --repo CryptoYogiLLC/AI-Discover

# 2. Invoke Security Agent
/security-review PR#1

# 3. Agent analyzes and provides report
# 4. Based on report, approve or request changes
```

### 2. 🔧 DevOps Engineer Agent

**When to invoke**: For GitHub Actions, Docker, and infrastructure updates

```bash
# Review infrastructure changes
/devops-review

# The agent will:
# - Test CI/CD pipeline compatibility
# - Verify Docker builds
# - Check for breaking changes in workflows
# - Update configurations if needed
```

### 3. 👨‍💻 Backend Developer Agent

**When to invoke**: For Python dependency updates

```bash
# Review backend dependency updates
/backend-review

# The agent will:
# - Check for API breaking changes
# - Run backend tests
# - Update code for deprecations
# - Verify database migrations
```

### 4. 👩‍💻 Frontend Developer Agent

**When to invoke**: For JavaScript/Node.js updates

```bash
# Review frontend dependency updates
/frontend-review

# The agent will:
# - Check for React/Next.js breaking changes
# - Run frontend tests
# - Update components if needed
# - Verify build success
```

## Practical Workflow for Current PRs

### Step 1: Initial Triage

```bash
# Run the PR management script
./scripts/manage-dependabot-prs.sh

# Choose option 1 to categorize PRs
```

### Step 2: Handle by Priority

#### Priority 1: Security Updates (Critical)

```bash
# For each security PR:
gh pr checkout <PR_NUMBER>

# Invoke Security Agent
/security-review

# If approved by agent:
gh pr review <PR_NUMBER> --approve
gh pr merge <PR_NUMBER> --merge
```

#### Priority 2: Major Version Updates (High Risk)

```bash
# For major updates (e.g., Next.js 14 → 15):
gh pr checkout <PR_NUMBER>

# Invoke appropriate agent based on component
/frontend-review  # For frontend updates
/backend-review   # For backend updates

# Agent will:
# 1. Check breaking changes
# 2. Update code if needed
# 3. Run comprehensive tests
# 4. Provide migration guide

# If changes needed:
git add -A
git commit -m "fix: update code for <dependency> v<version>"
git push
```

#### Priority 3: Minor/Patch Updates (Low Risk)

```bash
# Batch approve safe updates
./scripts/manage-dependabot-prs.sh
# Choose option 3
```

## Automated Workflow

The repository includes automated workflows for:

1. **Auto-approval**: Patch and minor updates for dev dependencies
2. **Auto-merge**: After tests pass and approval
3. **Labeling**: Automatic categorization of updates

## AI Agent Commands Reference

### Quick Commands for Common Tasks

```bash
# Security audit all PRs
/security-audit --all-prs

# Batch update frontend dependencies
/frontend-batch-update

# Review and fix breaking changes
/breaking-changes-fix PR#<number>

# Generate compatibility report
/compatibility-report
```

### Agent Collaboration

For complex updates requiring multiple agents:

```bash
# 1. Architect reviews impact
/architect-review PR#<number>

# 2. Relevant developer implements fixes
/backend-fix PR#<number>  # or frontend-fix

# 3. Security validates changes
/security-validate

# 4. DevOps ensures CI/CD works
/devops-validate
```

## Best Practices

1. **Always start with security**: Review security implications first
2. **Test locally**: Check out PR branches and test locally
3. **Incremental updates**: Handle major versions separately
4. **Document changes**: Update CHANGELOG for significant updates
5. **Monitor CI/CD**: Ensure all checks pass before merging

## Handling the Current 13 PRs

Here's the recommended approach:

### 1. Quick Wins (5 minutes)

```bash
# Auto-approve GitHub Actions updates (low risk)
gh pr review 3 4 5 6 7 --approve

# These are infrastructure updates that rarely break
```

### 2. Frontend Updates (30 minutes)

```bash
# Check out the Next.js major update
gh pr checkout 9

# Invoke Frontend Agent to handle breaking changes
/frontend-review

# The agent will update code and test
# Then merge if successful
```

### 3. Docker Updates (15 minutes)

```bash
# Python 3.11 → 3.13 and Node 18 → 24
gh pr checkout 8
/devops-review

gh pr checkout 2
/devops-review
```

### 4. Development Dependencies (10 minutes)

```bash
# These are safe to batch approve
./scripts/manage-dependabot-prs.sh
# Option 3: Batch approve patch updates
```

## Monitoring and Reporting

After handling PRs:

```bash
# Generate summary report
./scripts/manage-dependabot-prs.sh
# Option 5: Generate report

# Check deployment status
gh workflow view "CI/CD Pipeline"

# Monitor for new PRs
gh pr list --author "app/dependabot"
```

## Troubleshooting

### If Tests Fail

```bash
# Check specific test failure
gh pr checks <PR_NUMBER>

# Invoke appropriate agent to fix
/<agent>-fix PR#<number>
```

### If Merge Conflicts

```bash
# Check out PR
gh pr checkout <PR_NUMBER>

# Rebase with main
git rebase origin/main

# Resolve conflicts with agent help
/resolve-conflicts

# Push changes
git push --force-with-lease
```

Remember: The AI agents are here to help automate the tedious parts while ensuring quality and security!
