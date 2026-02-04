Simplify code to improve readability and maintainability.

## Steps

### 1. Reduce Nesting
- Convert nested if/else chains to early returns (guard clauses).
- Replace nested loops with flatMap, reduce, or helper functions.
- Extract deeply nested callbacks into named functions.
- Target: maximum 3 levels of indentation in any function.

### 2. Extract Functions
- Identify code blocks with a comment explaining what they do. The comment is a sign the block should be a function with that name.
- Extract repeated logic into shared functions.
- Each function should do one thing. If you need "and" to describe it, split it.
- Name functions to describe what they return or what side effect they perform.

### 3. Improve Naming
- Rename single-letter variables (except loop counters `i`, `j`, `k`).
- Replace abbreviations with full words: `usr` -> `user`, `btn` -> `button`, `cfg` -> `config`.
- Boolean variables should read as questions: `isValid`, `hasPermission`, `canEdit`.
- Functions that return booleans should start with `is`, `has`, `can`, `should`.

### 4. Remove Duplication
- Identify repeated patterns across the codebase using search.
- Extract shared logic into utility functions, hooks, or base classes.
- Use parameterization instead of copy-paste with minor changes.
- Tolerate duplication across module boundaries if coupling would be worse.

### 5. Simplify Conditionals
- Replace complex boolean expressions with descriptive variables.
- Use lookup tables or maps instead of long switch/if-else chains.
- Replace ternary chains with if/else or early returns.
- Use optional chaining and nullish coalescing where appropriate.

### 6. Verify
- Run the full test suite after each simplification.
- Compare behavior before and after. Simplification should not change behavior.
- Check that the code is actually more readable, not just shorter.

## Rules

- Simpler means easier to understand on first read, not fewer lines.
- Do not sacrifice clarity for cleverness. Explicit beats implicit.
- Preserve all existing behavior. This is refactoring, not rewriting.
- If a function is complex because the domain is complex, add documentation rather than oversimplifying.
- Make one kind of simplification per commit for clean diffs.
