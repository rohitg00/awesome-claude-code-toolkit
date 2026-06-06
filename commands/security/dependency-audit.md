Audit project dependencies for known vulnerabilities and outdated packages.

## Steps

1. Detect the package manager and run the native audit command:
   - npm: `npm audit --json`
   - pnpm: `pnpm audit --json`
   - yarn: `yarn audit --json`
   - pip: `pip-audit --format json` or `safety check --json`
   - cargo: `cargo audit --json`
   - go: `govulncheck ./...`
2. Parse audit results and categorize by severity (critical, high, moderate, low).
3. For each vulnerability:
   - Identify the affected package and version range.
   - Check if a patched version is available.
   - Determine if it is a direct or transitive dependency.
   - Assess actual exploitability in the project context.
4. Check for outdated dependencies: `npm outdated`, `pip list --outdated`.
5. Generate an upgrade plan prioritized by:
   - Critical vulnerabilities first.
   - Direct dependencies over transitive.
   - Minimal version bumps (patch > minor > major).
6. Test compatibility of recommended upgrades if possible.
7. Offer to apply safe upgrades automatically.

## Format

```
Dependency Audit Report
=======================

Vulnerabilities: <critical>C / <high>H / <moderate>M / <low>L

| Package | Current | Patched | Severity | Type | CVE |
|---------|---------|---------|----------|------|-----|

Outdated (no vulnerabilities):
| Package | Current | Latest | Type |
|---------|---------|--------|------|

Recommended actions:
1. <action with command>
```

## Rules

- Always distinguish between direct and transitive dependencies.
- Do not auto-upgrade major versions without user confirmation.
- Report vulnerabilities even if no fix is available yet.
- Check that lock files are committed and up to date.
- Verify upgrades do not break the test suite before recommending them.
