Generate a CI pipeline configuration for GitHub Actions.

## Steps

### 1. Detect Project Requirements
- Identify language, package manager, and test framework from config files.
- Determine required services (database, Redis, etc.) from the project setup.
- Check for existing CI configuration to update rather than replace.

### 2. Pipeline Stages

#### Lint
- Run linter: ESLint, Ruff, golangci-lint, clippy.
- Run formatter check: Prettier, Black, gofmt, rustfmt.
- Run type checker: tsc --noEmit, mypy, go vet.

#### Test
- Run unit tests with coverage reporting.
- Run integration tests with required services.
- Upload coverage reports as artifacts.
- Fail if coverage drops below threshold.

#### Build
- Build the application.
- Build Docker image if applicable.
- Upload build artifacts.

#### Deploy (on main branch only)
- Deploy to staging environment.
- Run smoke tests against staging.
- Deploy to production (manual approval gate).

### 3. Generate Workflow File
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
```

### 4. Add Caching
- Cache package manager dependencies (npm, pip, go modules).
- Cache build outputs where possible.
- Use `hashFiles` for cache keys based on lock files.

## Rules

- Use specific action versions (v4, not latest) for reproducibility.
- Cache aggressively: dependencies, build outputs, Docker layers.
- Run lint before tests (fail fast on style issues).
- Use matrix builds for multiple language versions only if the project supports them.
- Keep secrets in GitHub repository settings, never in workflow files.
- Add timeout limits to prevent hung jobs: `timeout-minutes: 15`.
- Use `concurrency` to cancel superseded runs on the same branch.
