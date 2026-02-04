Audit all project dependencies for vulnerabilities, licensing issues, and maintenance status.

## Steps

1. Detect the package manager and run native audit:
   - npm: `npm audit --json`
   - pnpm: `pnpm audit --json`
   - pip: `pip-audit --format json`
   - cargo: `cargo audit --json`
2. Check package maintenance status:
   - Last publish date for each dependency.
   - Open issue count and response time.
   - Whether the package is deprecated.
3. Verify license compatibility:
   - List all dependency licenses.
   - Flag any copyleft licenses (GPL) in permissive projects.
   - Flag packages with no license specified.
4. Analyze dependency tree depth and size impact.
5. Identify unused dependencies by cross-referencing imports.
6. Generate a prioritized action list.

## Format

```
Dependency Audit - <date>

Vulnerabilities: <C>critical, <H>high, <M>moderate, <L>low
Licenses: <N> permissive, <N> copyleft, <N> unknown
Maintenance: <N> actively maintained, <N> stale, <N> deprecated
Unused: <list>

Priority actions:
  1. [CRITICAL] Upgrade <pkg> to fix CVE-XXXX
  2. [WARNING] Replace deprecated <pkg> with <alternative>
```

## Rules

- Always report the full vulnerability chain (which direct dep pulls in the vulnerable transitive dep).
- Flag any dependency with no updates in the last 12 months.
- Check that lock files are present and committed.
- Never recommend removing a dependency without verifying it is truly unused.
