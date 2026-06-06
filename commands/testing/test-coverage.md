Analyze test coverage gaps and generate tests for uncovered code paths.

## Steps

### 1. Run Coverage Analysis
- Detect the test framework and run coverage:
  - **JS/TS**: `npx vitest run --coverage` or `npx jest --coverage`
  - **Python**: `pytest --cov=src --cov-report=term-missing`
  - **Go**: `go test -coverprofile=cover.out ./... && go tool cover -func=cover.out`
  - **Rust**: `cargo tarpaulin --out Stdout`

### 2. Identify Gaps
- List files below 80% line coverage.
- For each low-coverage file, identify:
  - Uncovered branches (if/else, switch cases, error paths).
  - Uncovered functions or methods.
  - Edge cases not exercised (null inputs, empty collections, boundary values).

### 3. Prioritize
- Rank gaps by risk: business logic > data access > utilities > configuration.
- Focus on branches where bugs are most likely to hide: error handling, boundary conditions, type coercion.

### 4. Generate Tests
- Write tests for the highest-priority uncovered paths.
- Each test targets a specific uncovered branch or function.
- Use existing test patterns and conventions from the codebase.
- Follow the Arrange-Act-Assert structure.

### 5. Verify
- Re-run coverage to confirm the gaps are filled.
- Ensure no existing tests broke.

## Rules

- Do not write tests purely to increase numbers. Every test must assert meaningful behavior.
- Exclude generated code, type definitions, and configuration from coverage targets.
- Target 80% line coverage and 75% branch coverage as minimums.
- If a function is genuinely untestable (e.g., thin wrappers), document why rather than writing a meaningless test.
