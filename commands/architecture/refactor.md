Perform a systematic refactoring of the specified code area.

## Steps

### 1. Identify Code Smells
Read the target code and identify issues:
- **Long functions** (>40 lines): break into smaller functions with descriptive names.
- **Deep nesting** (>3 levels): use early returns, guard clauses, or extract functions.
- **Duplicate logic**: extract shared functions or use parameterization.
- **God objects/modules**: split into focused, single-responsibility units.
- **Primitive obsession**: introduce domain types or value objects.
- **Feature envy**: move logic to the class/module that owns the data.
- **Unclear naming**: rename variables, functions, and files to reveal intent.

### 2. Verify Test Coverage
- Run existing tests to establish the green baseline.
- If coverage is insufficient, write characterization tests that capture current behavior before changing anything.
- Every refactored path must have a test that would catch a regression.

### 3. Plan Changes
- List each refactoring step in order.
- Each step should be a single, atomic change (one rename, one extract, one move).
- Order steps to minimize risk: rename before restructure, restructure before optimize.

### 4. Execute
- Apply one refactoring at a time.
- Run tests after each step to confirm behavior is preserved.
- Commit after each successful step if the changes are significant.

### 5. Verify
- Run the full test suite.
- Check that type checking passes.
- Compare behavior before and after (same inputs produce same outputs).

## Rules

- Refactoring changes structure, not behavior. If behavior changes, that is a feature or a fix.
- Never refactor and add features in the same step.
- If tests are missing, add them before refactoring, not after.
- Keep diffs reviewable: prefer multiple small commits over one massive change.
- If a refactoring reveals a bug, note it and fix it in a separate commit.
