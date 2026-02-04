# Deploy Context

You are preparing or executing a deployment. Prioritize safety and reversibility.

## Pre-Deploy Checklist
- All CI checks pass on the deployment branch.
- Database migrations are backward-compatible with the current running version.
- Environment variables are set in the target environment before deploy.
- Feature flags are configured for any partially-shipped features.
- The changelog or release notes are updated.
- A rollback plan is documented and ready.

## Deployment Steps
1. Verify the build artifact matches the tested commit (check SHA or tag).
2. Run database migrations before deploying the new application version.
3. Deploy to staging first. Smoke test critical paths.
4. Deploy to production using a rolling or blue-green strategy.
5. Monitor error rates, latency, and health checks for 15 minutes post-deploy.
6. Confirm success in the team channel. Tag the release in git.

## Rollback Criteria
- Error rate exceeds 2x the pre-deploy baseline.
- P99 latency exceeds 3x the pre-deploy baseline.
- Health check failures on more than one instance.
- Any data corruption or integrity violation.
- Customer-reported critical issues within the deploy window.

## Post-Deploy
- Close related issues and update the project board.
- Monitor Sentry and logging dashboards for new error patterns.
- Notify stakeholders of the completed deployment.
- Schedule a post-mortem if the deploy had issues.

## Avoid
- Do not deploy on Fridays or before holidays without explicit approval.
- Do not skip staging for "small changes." All changes go through staging.
- Do not run destructive migrations during peak traffic hours.
- Do not deploy multiple unrelated changes in a single release.
