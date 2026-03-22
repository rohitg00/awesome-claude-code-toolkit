# /simplify-fn - Simplify Complex Function

Refactor a complex function to reduce cyclomatic complexity.

## Steps

1. Read the target function and calculate its current complexity score
2. Identify the primary complexity drivers: nested ifs, loops, switch statements
3. Map the function's control flow to understand all execution paths
4. Apply Extract Method refactoring: pull out logical blocks into named functions
5. Replace nested conditionals with guard clauses (early returns)
6. Convert switch statements to lookup tables or strategy pattern where appropriate
7. Replace complex boolean expressions with named boolean variables
8. Decompose loops with multiple responsibilities into separate loops or higher-order functions
9. Apply polymorphism to replace type-checking conditionals when applicable
10. Verify the refactored code preserves all original behavior by running tests
11. Calculate the new complexity score and report the improvement
12. Ensure the refactored code is readable and properly named

## Rules

- Preserve all existing behavior; this is refactoring, not feature change
- Run tests after each refactoring step to catch regressions immediately
- Target a complexity score of 5 or below for the main function
- Keep extracted functions small (under 15 lines) and single-purpose
- Use descriptive names for extracted functions that explain the "why"
- Do not introduce new dependencies or external libraries
- If tests do not exist, write them before refactoring
