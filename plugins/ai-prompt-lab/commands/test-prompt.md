Test an AI prompt against multiple scenarios to verify consistent, quality output.

## Steps

1. Read the prompt to test (command file, CLAUDE.md rule, or inline prompt).
2. Generate test scenarios:
   - **Happy path**: Standard use case with typical input.
   - **Edge case**: Empty input, very large input, unusual formats.
   - **Ambiguous case**: Input that could be interpreted multiple ways.
   - **Error case**: Invalid input that should produce helpful error messages.
3. For each scenario:
   - Formulate the test input.
   - Execute the prompt with that input.
   - Evaluate the output against expected behavior.
   - Score on: accuracy, format compliance, helpfulness.
4. Identify failure patterns:
   - Does the prompt break on certain input types?
   - Does it produce inconsistent output formats?
   - Does it hallucinate when information is missing?
5. Suggest prompt modifications based on test results.

## Format

```
Prompt Test Results: <prompt name>

| Scenario | Input | Result | Score |
|----------|-------|--------|-------|
| Happy path | <input> | pass | 5/5 |
| Edge case | <input> | partial | 3/5 |
| Error case | <input> | fail | 1/5 |

Overall score: <average>/5
Failure patterns: <description>
Recommendations: <improvements>
```

## Rules

- Test at least 5 scenarios for each prompt.
- Include at least one adversarial input that tries to break the prompt.
- Score consistently using the same rubric across all tests.
- Document the exact input used so tests can be reproduced.
- Suggest specific prompt changes for each failure, not just "improve X".
