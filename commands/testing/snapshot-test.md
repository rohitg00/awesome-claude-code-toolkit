Generate snapshot tests for UI components or serializable outputs.

## Steps

1. Identify the target component or function from the argument.
2. Detect the testing framework and snapshot support (Jest snapshots, Vitest, pytest-snapshot).
3. Analyze the component props or function parameters to determine meaningful test cases.
4. For each component or function:
   - Create a snapshot test with default props/arguments.
   - Create snapshot tests for each significant visual state (loading, error, empty, populated).
   - Create snapshot tests for responsive variants if applicable.
5. For React/Vue components, use the appropriate renderer:
   - `@testing-library/react` with `render` for DOM snapshots.
   - `react-test-renderer` for tree snapshots if needed.
6. Run the tests to generate initial snapshots.
7. List all generated snapshot files and their locations.

## Format

```
Generated: <N> snapshot tests in <file>

Snapshots:
  - <ComponentName> default rendering
  - <ComponentName> loading state
  - <ComponentName> error state
  - <ComponentName> with data

Snapshot file: <path to .snap file>
```

## Rules

- Snapshot tests should capture meaningful visual states, not implementation details.
- Avoid snapshotting entire page trees; focus on individual components.
- Use inline snapshots (`toMatchInlineSnapshot`) for small outputs under 20 lines.
- Add a comment explaining what each snapshot verifies.
- Do not snapshot timestamps, random IDs, or other non-deterministic values; use serializers to strip them.
