Generate a project analytics report covering code quality, velocity, and health metrics.

## Steps

1. Gather git statistics:
   - `git shortlog -sn --no-merges` for contributor activity.
   - `git log --format='%ai' --since='30 days ago'` for commit frequency.
   - `git diff --stat HEAD~50` for recent change volume.
2. Analyze code quality metrics:
   - Lines of code by language using file extensions.
   - Test-to-code ratio (test files vs source files).
   - Average file size and function length.
   - TODO/FIXME/HACK comment count.
3. Check dependency health:
   - Total dependencies (direct and transitive).
   - Outdated packages count.
   - Known vulnerability count.
4. Measure test health:
   - Run test suite and capture pass/fail ratio.
   - Calculate approximate coverage if coverage tool exists.
5. Assess documentation coverage:
   - README completeness check.
   - API documentation presence.
   - Inline documentation density.
6. Compile findings into a structured report.

## Format

```
Project Health Report - <date>

Code: <N> files, <N> LOC across <N> languages
Tests: <N> tests, <pass rate>% passing
Deps: <N> direct, <N> outdated, <N> vulnerable
Activity: <N> commits in last 30 days by <N> contributors

Score: <A/B/C/D/F>
Top issues:
  1. <most impactful issue>
  2. <second most impactful>
```

## Rules

- Use objective metrics, not subjective assessments.
- Compare against industry benchmarks where possible.
- Highlight trends (improving/declining) over the last 30 days.
- Keep the report under 100 lines for quick consumption.
