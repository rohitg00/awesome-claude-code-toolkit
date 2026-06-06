Rename a symbol (variable, function, class, file) across the entire codebase.

## Steps

1. Accept the old name and new name from the argument.
2. Determine the symbol type:
   - Variable, function, or class name.
   - File or directory name.
   - Database column or table name.
   - CSS class or ID.
3. Find all references to the symbol:
   - Source code: imports, exports, usages, type references.
   - Tests: test descriptions, assertions, mocks.
   - Configuration: env vars, config files, CI pipelines.
   - Documentation: README, comments, API docs.
4. If renaming a file:
   - Update all import paths referencing the old filename.
   - Update any dynamic imports or require statements.
   - Update references in configuration files (tsconfig paths, webpack aliases).
5. Preview all changes before applying:
   - Show each file that will be modified with the specific line changes.
   - Highlight any ambiguous matches that might be false positives.
6. Apply changes across all files simultaneously.
7. Run the test suite and type checker to verify nothing broke.

## Format

```
Rename: <old-name> -> <new-name>
Type: <function|variable|class|file>

Files affected: <N>
  - <file>:<line> - <context of change>

Verification:
  - Type check: <pass/fail>
  - Tests: <pass/fail>
```

## Rules

- Show a preview of all changes and get confirmation before applying.
- Handle case sensitivity: distinguish `myFunc`, `MyFunc`, `MY_FUNC`.
- Do not rename symbols in `node_modules`, `vendor`, or other dependency directories.
- Preserve casing conventions (camelCase, PascalCase, snake_case, UPPER_CASE).
- Check for string literals that reference the symbol name (API routes, error messages).
- Update both the symbol and related names (e.g., renaming `User` should also update `UserProps`, `UserSchema`).
