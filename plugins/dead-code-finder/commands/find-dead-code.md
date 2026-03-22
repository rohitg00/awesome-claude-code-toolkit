# /find-dead-code - Find Dead Code

Identify unused code across the codebase.

## Steps

1. Detect the project language and build system
2. Identify entry points: main files, exported modules, route handlers, CLI commands
3. Build a dependency graph starting from all entry points
4. Scan for unused exports: functions, classes, constants, and types not imported anywhere
5. Check for unused files that are not imported or required by any other file
6. Detect unused variables, parameters, and private methods within each file
7. Identify commented-out code blocks longer than 3 lines
8. Check for unreachable code after return, throw, or break statements
9. Cross-reference with test files to exclude test-only utilities
10. Generate a report sorted by file with: item name, type, file path, line number
11. Calculate the total lines of dead code and percentage of codebase
12. Flag high-confidence removals vs items that need manual review

## Rules

- Exclude test files, fixtures, and configuration from dead code detection
- Do not flag dynamically imported modules or reflection-based usage
- Consider decorator and annotation usage (Angular, NestJS, Spring)
- Check for event handler registrations that may appear unused
- Exclude public API exports that may be consumed by external packages
- Mark confidence level: high (definitely unused), medium (likely unused), low (possibly unused)
- Do not auto-delete anything without explicit user confirmation
