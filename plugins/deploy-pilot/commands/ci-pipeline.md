# /deploy-pilot:ci-pipeline

Generate a GitHub Actions CI/CD workflow tailored to the current project.

## Process

1. Analyze the project to determine the pipeline requirements:
   - Detect language and package manager from manifest files
   - Check for existing test commands in package.json scripts, Makefile, or pyproject.toml
   - Identify linting tools already configured (ESLint, Prettier, Ruff, golangci-lint, Clippy)
   - Look for existing Docker configuration
   - Check for deployment targets (Vercel, AWS, GCP, Kubernetes manifests)

2. Generate the workflow file at `.github/workflows/ci.yml` with these jobs:

### Lint Job
- Install dependencies with caching (npm ci, pip install, go mod download)
- Run the project's configured linter
- Run format checking (prettier --check, ruff format --check, gofmt)
- Run type checking if applicable (tsc --noEmit, mypy, pyright)
- Fail fast: this job should complete in under 2 minutes

### Test Job
- Run the full test suite with coverage reporting
- Upload coverage artifacts for later reference
- For Node.js: use matrix strategy for Node 20 and 22
- For Python: use matrix strategy for Python 3.11 and 3.12
- Set timeout to prevent hung tests from blocking the pipeline
- Run tests in parallel if the framework supports it (pytest -n auto, vitest)

### Build Job
- Depends on lint and test passing
- Build the application artifacts
- For Docker projects: build the image and optionally push to registry
- For libraries: build the package and verify it can be published (dry-run)
- Cache build outputs between runs

### Deploy Job (optional, triggered on main branch only)
- Depends on build passing
- Deploy to the detected target environment
- Use environment protection rules and manual approval for production
- Include rollback instructions in job comments

3. Configure these workflow settings:
   - Trigger on push to main and pull requests
   - Cancel in-progress runs when new commits are pushed to the same PR
   - Set appropriate permissions (contents: read, packages: write if publishing)
   - Use `actions/checkout@v4`, `actions/setup-node@v4`, or equivalent
   - Cache dependency directories (node_modules, .pip-cache, ~/go/pkg/mod)

4. Add status badge markdown for the README.

## Output

Write the workflow to `.github/workflows/ci.yml`. If a workflow already exists, present a diff of the changes. Include comments in the YAML explaining non-obvious configuration choices.

## Rules

- Pin all action versions to full SHA hashes, not just major versions, for supply chain security
- Never store secrets directly in the workflow file; reference GitHub Secrets
- Keep the total pipeline under 10 minutes for a fast feedback loop
- Use `concurrency` groups to prevent redundant runs
- Set explicit timeouts on every job to prevent runaway costs
- Make the pipeline work for forks (no secrets required for lint and test)
