# /deploy-pilot:dockerfile

Generate an optimized multi-stage Dockerfile for the current project.

## Process

1. Detect the project type and runtime:
   - Check for `package.json` (Node.js), `requirements.txt`/`pyproject.toml` (Python), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml`/`build.gradle` (Java)
   - Identify the framework (Next.js, FastAPI, Gin, Actix, Spring Boot, etc.)
   - Read the existing entrypoint script or start command

2. Select the appropriate base image:
   - Use official slim/alpine variants for smaller image sizes
   - Pin to a specific version tag, never use `latest`
   - For Node.js: `node:22-alpine` for runtime, `node:22` for build
   - For Python: `python:3.12-slim` for runtime
   - For Go: `golang:1.23-alpine` for build, `gcr.io/distroless/static-debian12` for runtime
   - For Rust: `rust:1.82-slim` for build, `debian:bookworm-slim` for runtime

3. Structure the Dockerfile with these stages:

### Stage 1: Dependencies
- Copy only dependency manifests (package.json, go.sum, Cargo.lock, etc.)
- Install dependencies in a cached layer
- This stage changes only when dependencies change, maximizing cache hits

### Stage 2: Build
- Copy source code
- Run the build command (compile, transpile, bundle)
- Run tests if a `--with-tests` flag is specified
- Prune dev dependencies after build

### Stage 3: Runtime
- Start from a minimal base image
- Copy only the built artifacts and production dependencies
- Set a non-root user for security
- Configure health check with appropriate endpoint or command
- Set resource limits via labels where applicable
- Define the entrypoint and default command

4. Apply these optimizations:
   - Order COPY instructions from least to most frequently changed
   - Use `.dockerignore` patterns: suggest creating one if missing
   - Set `NODE_ENV=production` or equivalent environment variables
   - Use `COPY --from=build` to minimize final image layers
   - Add `LABEL` instructions for maintainer, version, and description
   - Set `EXPOSE` for the application port
   - Use `tini` or `dumb-init` as PID 1 for proper signal handling in Node.js

5. Generate a companion `.dockerignore` if one does not exist, including:
   - `.git`, `node_modules`, `__pycache__`, `.env`, `*.log`
   - Build output directories, test fixtures, documentation

## Output

Write the Dockerfile to the project root. If a Dockerfile already exists, present a diff and ask before overwriting. Include inline annotations explaining each optimization decision.

## Rules

- Never hardcode secrets or credentials in the Dockerfile
- Always run as non-root in the final stage
- Keep the final image under 200MB when possible
- Support both amd64 and arm64 architectures (avoid platform-specific binaries)
- Test the Dockerfile with `docker build --target runtime .` if Docker is available
