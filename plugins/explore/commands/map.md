Generate a dependency map showing how modules and files relate to each other in the codebase.

## Steps


1. Scan all source files and extract import/require statements.
2. Build a dependency graph:
3. Classify modules by role:
4. Calculate module metrics:
5. Identify high-risk areas:
6. Generate a visual map in text or Mermaid format.

## Format


```
Core Modules (high fan-in):
  - <module>: imported by <N> files

Dependency Chains:
```


## Rules

- Only map first-party code, not node_modules or third-party packages.
- Flag circular dependencies as issues that need resolution.
- Highlight modules that are single points of failure.

