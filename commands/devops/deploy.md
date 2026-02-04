Deploy the application to a target environment with pre/post checks.

## Steps

1. Determine the target environment from the argument (staging, production, preview).
2. Run pre-deployment checks:
   - All tests pass: run the test suite.
   - No uncommitted changes: `git status --porcelain`.
   - Branch is up to date: `git fetch && git status -uno`.
   - Build succeeds: run the build command.
   - No critical vulnerabilities: run dependency audit.
3. Detect the deployment method:
   - **Vercel/Netlify**: `vercel --prod` or `netlify deploy --prod`.
   - **Docker**: Build image, push to registry, update deployment.
   - **Kubernetes**: Apply manifests with `kubectl apply`.
   - **SSH**: rsync build artifacts and restart service.
   - **GitHub Pages**: Push to `gh-pages` branch.
4. Execute the deployment:
   - Tag the deployment: `git tag deploy-<env>-<timestamp>`.
   - Run the deployment command.
   - Wait for health check confirmation.
5. Run post-deployment verification:
   - Hit the health endpoint and verify 200 response.
   - Run smoke tests if available.
   - Check error rates in monitoring if accessible.
6. Report deployment status with rollback instructions.

## Format

```
Deployment: <environment>
Version: <git-sha-short>
Status: <success/failed>

Pre-checks:
  - [x] Tests passing
  - [x] Build successful
  - [x] No uncommitted changes

Deployed at: <timestamp>
URL: <deployment-url>
Health: <healthy/unhealthy>

Rollback: <rollback-command>
```

## Rules

- Never deploy to production from a non-default branch without explicit confirmation.
- Always run pre-deployment checks; abort on any failure.
- Create a deployment tag for every production deployment.
- Include rollback instructions in every deployment output.
- Verify the health endpoint responds within 60 seconds after deployment.
