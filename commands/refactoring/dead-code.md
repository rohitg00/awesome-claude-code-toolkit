Find and remove dead code from the codebase.

## Steps

### 1. Unused Imports
- Run the linter with unused import detection:
  - **TypeScript**: `tsc --noUnusedLocals --noUnusedParameters --noEmit`
  - **ESLint**: Check for `no-unused-vars`, `no-unused-imports` violations.
  - **Python**: `ruff check --select F401` or `flake8 --select=F401`.
  - **Go**: The compiler already catches unused imports.
- Remove all unused imports.

### 2. Unused Exports
- For each exported function, class, or constant, search the codebase for imports of that symbol.
- If a symbol is exported but never imported elsewhere, check if it is part of the public API.
- If it is internal and unused, remove the export and the code.
- Pay attention to dynamic imports and re-exports.

### 3. Unreachable Code
- Look for code after `return`, `throw`, `break`, or `continue` statements.
- Find branches that can never be true based on type narrowing or constant conditions.
- Identify functions that are defined but never called.
- Check for commented-out code blocks and remove them.

### 4. Dead Feature Flags
- Search for feature flags or environment variable checks.
- Identify flags that are always true/false in all environments.
- Remove the dead branch and the flag check.

### 5. Verify
- Run the full test suite to confirm nothing depends on the removed code.
- Run the build to confirm compilation succeeds.
- Check that no public API contracts were broken if this is a library.

## Rules

- Remove code in small, focused commits. One category of dead code per commit.
- If unsure whether code is used, check git blame for when it was last modified. Code untouched for 6+ months with no references is likely dead.
- Do not remove code that is part of a public API without a deprecation period.
- Keep test utilities and fixtures even if they seem unused; they may be needed for future tests.
- Never remove error handling or fallback code just because it has not been triggered yet.
