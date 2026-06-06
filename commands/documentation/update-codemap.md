Update the project codemap to reflect the current state of the codebase.

## Steps

### 1. Scan Project Structure
- Run `find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/__pycache__/*'` to get the file tree.
- Identify the top-level directories and their purposes.
- Note the primary language(s) and framework(s) from config files (package.json, pyproject.toml, go.mod, Cargo.toml).

### 2. Identify Key Modules
For each major directory:
- **Purpose**: What this module is responsible for.
- **Entry point**: The main file that exports or bootstraps the module.
- **Key files**: The 3-5 most important files and what they contain.
- **Dependencies**: Which other modules this one depends on.

### 3. Map Data Flow
- Trace the request lifecycle: entry point -> routing -> business logic -> data access -> response.
- Identify shared state: databases, caches, message queues, shared config.
- Note async boundaries: background jobs, event handlers, webhooks.

### 4. Document Key Patterns
- Architecture pattern (MVC, layered, hexagonal, microservices).
- State management approach.
- Error handling strategy.
- Testing strategy and test location conventions.

### 5. Output Format
```markdown
# Project Codemap

## Structure
src/
  api/        - REST API handlers and middleware
  services/   - Business logic layer
  models/     - Database models and schemas
  utils/      - Shared utilities

## Key Files
- src/api/server.ts    - Express app setup, middleware chain
- src/services/auth.ts - Authentication and JWT handling
- src/models/user.ts   - User model with validation

## Data Flow
Request -> Middleware (auth, validation) -> Handler -> Service -> Repository -> Database

## Patterns
- Dependency injection via constructor parameters
- Repository pattern for data access
- Result type for error handling (no thrown exceptions in services)
```

## Rules

- Keep the codemap concise. It should fit in one screen for small projects, two for large ones.
- Focus on orientation, not exhaustive listing. A new developer should understand the project structure in 2 minutes.
- Update the codemap in CLAUDE.md or a dedicated CODEMAP.md at the project root.
- Include the build and test commands.
