Build a Docker image with best practices for caching, security, and size optimization.

## Steps

1. Read the existing Dockerfile or generate one if missing.
2. Analyze the build context:
   - Check `.dockerignore` exists and excludes unnecessary files.
   - Identify the base image and its size.
   - Map build stages and layer count.
3. Build the image with build arguments:
   - `docker build -t <name>:<tag> --build-arg VERSION=<ver> .`
   - Use BuildKit for improved caching: `DOCKER_BUILDKIT=1`.
   - Add `--platform linux/amd64,linux/arm64` for multi-arch if needed.
4. Verify the build:
   - Check final image size: `docker images <name>:<tag>`.
   - Run a quick smoke test: `docker run --rm <name>:<tag> <health-command>`.
   - Scan for vulnerabilities: `docker scout cves <name>:<tag>`.
5. Tag appropriately:
   - `<name>:latest` for development.
   - `<name>:<version>` for releases.
   - `<name>:<git-sha-short>` for CI builds.
6. Report build results and image details.

## Format

```
Docker Build: <name>:<tag>
Base: <base-image>
Size: <size>MB (layers: <N>)
Build time: <duration>

Vulnerabilities: <C>critical, <H>high, <M>medium
Smoke test: <pass/fail>

Push: docker push <registry>/<name>:<tag>
```

## Rules

- Always use specific base image tags, not `latest`.
- Include a `.dockerignore` to minimize build context.
- Run as non-root user in the final image.
- Use multi-stage builds to keep the final image minimal.
- Add health check instruction (`HEALTHCHECK`) for production images.
