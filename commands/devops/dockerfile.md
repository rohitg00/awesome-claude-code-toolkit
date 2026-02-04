Generate an optimized Dockerfile for the current project.

## Steps

### 1. Detect Project Type
- Read package.json, pyproject.toml, go.mod, Cargo.toml, or equivalent to determine the language and framework.
- Identify the build command and output directory.
- Identify runtime dependencies vs. build-only dependencies.

### 2. Choose Base Image
- **Node.js**: `node:22-alpine` for runtime, `node:22` for build if native modules are needed.
- **Python**: `python:3.12-slim` for runtime, full image for build if compilation is needed.
- **Go**: `golang:1.23-alpine` for build, `gcr.io/distroless/static-debian12` for runtime.
- **Rust**: `rust:1.82-slim` for build, `debian:bookworm-slim` or `scratch` for runtime.

### 3. Multi-Stage Build
```dockerfile
# Stage 1: Build
FROM <build-image> AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM <runtime-image>
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
USER node
CMD ["node", "dist/index.js"]
```

### 4. Optimization Checklist
- Copy dependency files first, then source code (layer caching).
- Use `.dockerignore` to exclude: `.git`, `node_modules`, `dist`, `.env`, tests, docs.
- Run as non-root user.
- Set `NODE_ENV=production` or equivalent.
- Add health check: `HEALTHCHECK CMD curl -f http://localhost:3000/health || exit 1`.
- Pin base image versions with digest for reproducibility.
- Minimize layers by combining related RUN commands.

### 5. Generate .dockerignore
Create or update `.dockerignore` with sensible defaults for the project type.

## Rules

- Always use multi-stage builds to minimize image size.
- Never copy `.env` files or secrets into the image.
- Run as a non-root user in the final stage.
- Include a HEALTHCHECK instruction.
- Keep the final image under 200MB for typical web applications.
- Test the built image locally with `docker build -t app . && docker run -p 3000:3000 app`.
