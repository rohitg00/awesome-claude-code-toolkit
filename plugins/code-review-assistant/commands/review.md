Perform an automated code review with categorized findings and severity ratings.

## Steps


1. Identify the scope of the review:
2. Review for correctness:
3. Review for security:
4. Review for maintainability:
5. Review for performance:
6. Assign severity to each finding:

## Format


```
Review: <scope>
Findings: <total count>
  [CRITICAL] <file>:<line> - <issue>
  [WARNING] <file>:<line> - <issue>
```


## Rules

- Read the full file context, not just the diff.
- Be specific: reference exact lines and suggest concrete fixes.
- Balance criticism with acknowledgment of good patterns.

