# /analyze-ci-failure - Analyze CI/CD Failure

Analyze and diagnose a CI/CD pipeline failure.

## Steps

1. Identify the CI/CD platform: GitHub Actions, GitLab CI, CircleCI, Jenkins, Azure DevOps
2. Locate the failed pipeline run from logs, URL, or recent git push
3. Retrieve the full build log output for the failed step
4. Identify the exact failure point: which step, which command, which line
5. Classify the failure type: build error, test failure, lint error, deployment error, infra issue
6. Extract the error message and relevant stack trace
7. Check if the failure is flaky by reviewing recent run history for the same job
8. Analyze the error against common CI failure patterns:
   - Dependency installation failures (network, version conflicts)
   - Test timeouts or resource exhaustion
   - Docker build failures (layer caching, missing base image)
   - Permission or credential issues
9. Check for environment differences between local and CI
10. Suggest specific fixes with code changes or configuration updates
11. If the fix requires a pipeline config change, show the exact diff
12. Provide a confidence level for the diagnosis and suggested fix

## Rules

- Focus on the root cause, not symptoms (a test timeout may be caused by a resource leak)
- Check for recent changes to the CI config file that may have introduced the failure
- Consider caching issues: suggest clearing cache if the error is inconsistent
- Check if the failure only occurs on CI (environment-specific issue)
- Look for secret or credential expiration as a common cause
- Do not expose secret values in the analysis output
- Suggest adding better error handling to prevent obscure failures
