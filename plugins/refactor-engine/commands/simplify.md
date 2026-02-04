Simplify complex code by reducing nesting, eliminating duplication, and improving clarity.

## Steps

1. Measure the current complexity:
   - Count nesting depth (target: max 3 levels).
   - Count lines per function (target: max 30 lines).
   - Identify duplicated patterns (3+ occurrences).
   - Check cyclomatic complexity if tooling available.
2. Apply simplification techniques:
   - **Early returns**: Replace nested if/else with guard clauses.
   - **Extract variables**: Name complex expressions for readability.
   - **Decompose conditionals**: Move complex conditions into named functions.
   - **Replace loops**: Use map/filter/reduce where clearer.
   - **Eliminate duplication**: Extract repeated patterns into shared functions.
   - **Simplify state**: Reduce the number of mutable variables.
3. For each simplification:
   - Show the before and after code.
   - Explain why the change improves the code.
   - Verify behavior is preserved.
4. Run tests after all simplifications.
5. Measure the new complexity and compare to the original.

## Format

```
Simplification Report: <file>

Before: <complexity metrics>
After: <complexity metrics>

Changes:
  1. <description>: reduced nesting from 5 to 2 levels
  2. <description>: extracted 3 duplicated blocks into shared function
  3. <description>: replaced nested ternary with lookup table

Tests: all passing
```

## Rules

- Never change behavior while simplifying; this is purely structural.
- Simplify the most complex functions first for maximum impact.
- Preserve meaningful variable names; do not over-abbreviate.
- Run tests after each simplification to catch regressions early.
- Do not simplify code that is intentionally optimized for performance.
