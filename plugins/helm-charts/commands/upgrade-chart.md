# /upgrade-chart - Upgrade Helm Release

Upgrade an existing Helm release with new chart version or values.

## Steps

1. Identify the target release name and namespace
2. Check the current release status with `helm status`
3. Review the changes between current and new values
4. Run `helm diff upgrade` to preview changes if helm-diff plugin is installed
5. Validate the new chart version with `helm lint`
6. Run `helm upgrade` with the new values or chart version
7. Monitor the rollout status of updated deployments
8. Verify pods are running and healthy after the upgrade
9. Check application logs for startup errors or configuration issues
10. Run smoke tests against the updated deployment if configured
11. If the upgrade fails, provide rollback command and guidance
12. Report: release version, resources updated, rollout status

## Rules

- Always use `--dry-run` first to preview changes before actual upgrade
- Set `--timeout` appropriate to the application startup time
- Use `--atomic` flag to auto-rollback on failed upgrades
- Keep at least 3 release history entries for rollback capability
- Verify the Kubernetes context is correct before upgrading
- Do not upgrade multiple releases simultaneously in the same namespace
- Document the upgrade reason and values changed for audit purposes
