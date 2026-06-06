# Testing Rules

## Test Before Commit
- Run the relevant test suite before every commit.
- All tests must pass before pushing to a shared branch.
- Never merge a PR with failing tests.
- If a test is flaky, fix it immediately or quarantine with a tracking issue.

## Coverage Requirements
- Minimum 80% line coverage on new code.
- Minimum 75% branch coverage on new code.
- Coverage should not decrease on any PR.
- Exclude generated code, type definitions, and config from coverage metrics.

## Test Quality
- Test behavior, not implementation. Tests should survive refactoring.
- Each test case tests exactly one thing. One assertion per logical behavior.
- Tests must be independent. No shared mutable state. No execution order dependency.
- Use descriptive names: `should_reject_expired_token` over `test_token_3`.

## Test Organization
- Mirror source directory structure in test directories.
- Keep test utilities and fixtures in a shared `__tests__/helpers` or `testutils` directory.
- Mark slow tests (>5s) so they can be excluded from fast feedback loops.

## Mocking Rules
- Mock at boundaries: HTTP, database, filesystem, clock, randomness.
- Never mock the unit under test.
- Prefer fakes (in-memory implementations) over mocks for complex interfaces.
- Assert on behavior and outputs, not on how many times a mock was called.

## CI Integration
- No `skip` or `todo` tests in the main branch. Fix or remove them.
- Run tests in CI on every push and every PR.
- Fail the build if coverage drops below thresholds.
- Run tests in parallel where possible to keep CI fast.
- Set a timeout on test suites to catch infinite loops (10 minutes max).

## Anti-Patterns
- Do not write tests that pass when the code under test is deleted.
- Do not test private methods directly. Test through the public interface.
- Do not ignore test failures by increasing timeouts.
- Do not copy-paste tests. Parameterize instead.
