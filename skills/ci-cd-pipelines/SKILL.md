---
name: ci-cd-pipelines
description: CI/CD pipeline patterns for GitHub Actions, GitLab CI, testing strategies, and deployment automation
---

# CI/CD Pipelines

## GitHub Actions Workflow

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

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
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/test
      - uses: codecov/codecov-action@v4

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy.sh
```

Use `concurrency` to cancel stale runs. Use `needs` to define job dependencies.

## GitLab CI Pipeline

```yaml
stages:
  - validate
  - test
  - build
  - deploy

variables:
  NODE_IMAGE: node:22-alpine

lint:
  stage: validate
  image: $NODE_IMAGE
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths: [node_modules/]
  script:
    - npm ci
    - npm run lint
    - npm run typecheck

test:
  stage: test
  image: $NODE_IMAGE
  services:
    - postgres:16
  variables:
    POSTGRES_DB: test
    DATABASE_URL: postgres://runner:@postgres:5432/test
  script:
    - npm ci
    - npm test -- --coverage
  coverage: '/Statements\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      junit: coverage/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura.xml

build:
  stage: build
  image: docker:24
  services: [docker:24-dind]
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:
  stage: deploy
  environment:
    name: production
    url: https://app.example.com
  script:
    - ./deploy.sh $CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

## Reusable GitHub Action

```yaml
# .github/actions/setup/action.yml
name: Setup
description: Install dependencies and cache
inputs:
  node-version:
    default: "22"
runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm
    - run: npm ci
      shell: bash
```

```yaml
# Usage in workflow
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/setup
  - run: npm test
```

## Matrix Strategy

```yaml
test:
  strategy:
    fail-fast: false
    matrix:
      node: [20, 22]
      os: [ubuntu-latest, macos-latest]
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node }}
    - run: npm ci && npm test
```

## Anti-Patterns

- Not caching dependencies (npm, pip, cargo) between runs
- Running all jobs sequentially when lint and test can parallelize
- Storing secrets in workflow files instead of repository/environment secrets
- Missing `concurrency` groups causing redundant CI runs on rapid pushes
- Not using `fail-fast: false` in matrix builds (one failure cancels others)
- Deploying without an approval gate or environment protection rule

## Checklist

- [ ] Dependencies cached between CI runs
- [ ] Concurrency groups cancel stale pipeline runs
- [ ] Lint, typecheck, and test run as separate parallelizable jobs
- [ ] Database services use health checks before tests start
- [ ] Coverage reports uploaded and tracked
- [ ] Deploy job requires approval for production
- [ ] Reusable actions/templates extract common setup steps
- [ ] Secrets stored in CI platform, never in code
