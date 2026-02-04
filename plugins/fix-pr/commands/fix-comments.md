Address PR review comments by implementing requested changes automatically.

## Steps


1. Fetch the PR details and review comments:
2. Parse each review comment:
3. For each actionable comment:
4. Run the test suite to ensure nothing is broken.
5. Stage and commit fixes with a message referencing the review:
6. Push the changes to the PR branch.
7. Reply to resolved comments if the gh CLI supports it.

## Format


```
PR: #<number>
Comments Addressed: <count>
Changes Made:
  - <file>:<line> - <what was changed>
```


## Rules

- Address all blocking comments before pushing.
- Do not modify code outside of what reviewers requested.
- If a comment is unclear, flag it rather than guessing.

