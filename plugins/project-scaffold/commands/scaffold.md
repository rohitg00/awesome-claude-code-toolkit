Scaffold a new project with a complete, production-ready structure.

## Steps

1. Determine the project type from the argument:
   - `api` - REST/GraphQL API backend.
   - `web` - Frontend web application.
   - `cli` - Command-line tool.
   - `lib` - Reusable library/package.
   - `fullstack` - Full-stack application.
2. Select the tech stack based on preferences or defaults:
   - TypeScript: Express/Fastify, React/Next.js, Vitest.
   - Python: FastAPI/Django, pytest.
   - Go: Chi/Gin, standard testing.
   - Rust: Actix/Axum, cargo test.
3. Generate the project structure:
   - `src/` with entry point and initial modules.
   - `tests/` with test configuration and example tests.
   - Configuration files (tsconfig, eslint, prettier, etc.).
   - `Dockerfile` and `.dockerignore`.
   - CI/CD workflow (GitHub Actions).
   - `README.md` with setup instructions.
   - `.env.example` with documented variables.
   - `.gitignore` with comprehensive patterns.
4. Initialize package manager and install dependencies.
5. Initialize git repository with initial commit.
6. Verify the project builds and tests pass.

## Format

```
Project scaffolded: <name>
Type: <project-type>
Stack: <tech-stack>

Structure:
  src/          - Application source
  tests/        - Test suite
  .github/      - CI/CD workflows
  docker/       - Container configuration

Commands:
  dev:   <command>
  test:  <command>
  build: <command>
```

## Rules

- Every scaffold must include a working test and build pipeline from the start.
- Include health check endpoint for API projects.
- Add pre-commit hooks for linting and formatting.
- Use the latest stable versions of all dependencies.
- Generate a CLAUDE.md with project-specific memory from the start.
