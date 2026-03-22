Optimize an existing Dockerfile for smaller images, faster builds, and better security.

## Steps

1. Read the existing Dockerfile and analyze each instruction.
2. Check for size optimization opportunities:
   - Use Alpine or distroless base images where possible.
   - Combine RUN commands to reduce layers.
   - Remove package manager caches in the same layer as installs.
   - Use multi-stage builds to exclude build tools from the final image.
   - Copy only necessary files, not the entire context.
3. Check for build cache optimization:
   - Order instructions from least to most frequently changing.
   - Copy dependency files before source code.
   - Use `--mount=type=cache` for package manager caches.
4. Check for security best practices:
   - Use specific version tags for base images.
   - Run as non-root user: `USER <non-root>`.
   - Set `HEALTHCHECK` instruction.
   - Do not store secrets in environment variables or build args.
   - Minimize installed packages to reduce attack surface.
5. Apply optimizations and compare before/after image sizes.
6. Verify the optimized image still runs correctly.

## Format

```
Dockerfile Optimization: <path>

Before: <size>MB, <layers> layers
After: <size>MB, <layers> layers
Reduction: <percent>%

Changes:
  1. Switched base from node:20 to node:20-alpine (-600MB)
  2. Combined 5 RUN commands into 2 (-3 layers)
  3. Added multi-stage build, excluded devDependencies (-200MB)
  4. Added non-root USER instruction (security)

Verification: container starts and passes health check
```

## Rules

- Always test the optimized image before recommending changes.
- Do not sacrifice build reliability for marginal size gains.
- Preserve build cache efficiency; do not combine steps that change independently.
- Keep security fixes separate from optimization changes for clear review.
- Document why each base image was chosen.
