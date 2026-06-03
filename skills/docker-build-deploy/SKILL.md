---
name: docker-build-deploy
description: Use when user wants to containerize a project, set up Docker CI/CD with GitHub Actions, push images to a container registry, or deploy containers to a remote server
---

# Docker Build & Deploy

Generate complete Docker CI/CD GitHub Actions workflows: build, push to GHCR, and deploy via SSH.

## When to Use

- User wants to containerize a project
- User needs GitHub Actions to build Docker images
- User mentions Docker, GHCR, container deployment, CI/CD

## Core Pattern

### Step 1: Collect info

Ask for: `port` (default 3000), `env_file` (optional), project type.

Auto-detect: `package.json` → Node.js, `go.mod` → Go, `requirements.txt` → Python.

### Step 2: Generate Dockerfile

Multi-stage build, non-root user, health check:

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
RUN addgroup -g 1001 -S app && adduser -S app -u 1001 -G app
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
USER app
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Step 3: Generate workflow

**build-and-push job**: Login GHCR → Buildx → Push (latest + sha) → GHA cache

**deploy job** (main only): SSH → Pull → Stop old → Start new → Prune

## Quick Reference

```bash
/docker-build-deploy
/docker-build-deploy --port 8080 --env-file /opt/app/.env
```

Required GitHub Secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PASSWORD`

## Full Version

For complete templates: [wu529778790/shenzjd-skills](https://github.com/wu529778790/shenzjd-skills/tree/main/docker-build-deploy)

Install with: `npx skills add wu529778790/shenzjd-skills -s docker-build-deploy`
