# /organize - Organize Imports

Sort, group, and clean up import statements across the project.

## Steps

1. Detect the project language and import style (ES modules, CommonJS, Python, Go, etc.)
2. Read the project's linting configuration for import ordering rules
3. Scan target files for all import statements
4. Remove duplicate imports that import the same module
5. Remove unused imports that are not referenced in the file body
6. Group imports into standard categories: built-in, external, internal, relative, type-only
7. Sort imports alphabetically within each group
8. Add blank lines between import groups for visual separation
9. Convert wildcard imports to named imports where only specific exports are used
10. Merge multiple imports from the same module into a single import statement
11. Apply consistent quote style (single or double) matching project conventions
12. Run the linter to verify the organized imports pass all rules

## Rules

- Follow the project's existing import ordering convention if one exists
- Standard grouping order: built-in, external packages, internal aliases, relative paths
- Type-only imports should be grouped separately (TypeScript)
- Do not reorder imports if the order has side effects (CSS imports, polyfills)
- Keep namespace imports when they are used extensively (more than 5 references)
- Use path aliases from tsconfig.json or webpack config when available
- Process one file at a time to allow incremental review
