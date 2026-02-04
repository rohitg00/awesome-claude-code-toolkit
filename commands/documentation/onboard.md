Generate an onboarding guide for new developers joining the project.

## Steps

1. Scan the project root for configuration files to determine the tech stack:
   - `package.json`, `tsconfig.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`.
   - `.env.example` for required environment variables.
   - `docker-compose.yml` for service dependencies.
2. Read existing documentation (`README.md`, `CONTRIBUTING.md`, `docs/`).
3. Map the project structure: key directories and their purposes.
4. Identify setup prerequisites:
   - Runtime versions (Node, Python, Go, Rust).
   - Required CLI tools (docker, kubectl, terraform).
   - Database and service dependencies.
5. Document the development workflow:
   - How to install dependencies.
   - How to run the project locally.
   - How to run tests.
   - How to create a branch and submit a PR.
6. List key architectural concepts a new developer needs to understand.
7. Write the guide to `docs/onboarding.md` or the specified location.

## Format

```markdown
# Developer Onboarding Guide

## Prerequisites
- [ ] Install <tool> v<version>

## Setup
1. Clone the repository
2. Install dependencies: `<command>`
3. Configure environment: `cp .env.example .env`
4. Start services: `<command>`

## Project Structure
- `src/` - Application source code
- `tests/` - Test suite

## Development Workflow
<step-by-step instructions>

## Key Concepts
<architectural overview for newcomers>
```

## Rules

- Write for someone with general programming experience but no project knowledge.
- Include exact commands, not vague instructions like "install dependencies".
- Test every setup command to verify it works.
- Link to existing documentation rather than duplicating it.
- Include common troubleshooting steps at the end.
