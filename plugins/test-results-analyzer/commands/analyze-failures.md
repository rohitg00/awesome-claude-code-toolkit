Analyze test failures to identify root causes, patterns, and suggest targeted fixes.

## Steps


1. Run the test suite and capture output:
2. Parse failing tests:
3. Categorize each failure:
4. Identify patterns across failures:
5. For each failure, trace to the root cause:
6. Suggest specific fixes ranked by impact:

## Format


```
Test Results: <passed>/<total> passed, <failed> failed
Failure Groups:
  <category>: <count> tests
    - <test name>: <root cause>
```


## Rules

- Always run the full test suite, not just failing tests.
- Group related failures to avoid fixing the same issue multiple times.
- Prioritize fixes that unblock the most tests.

