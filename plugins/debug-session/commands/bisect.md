Use git bisect to find the exact commit that introduced a bug through binary search.

## Steps


1. Identify a known good state and a known bad state:
2. Start the bisect session:
3. For each step git presents:
4. When bisect identifies the culprit commit:
5. End the bisect session: `git bisect reset`.
6. Create a fix based on the identified commit.
7. Document the bisect result with the commit hash and explanation.

## Format


```
Bisect Result:
  First Bad Commit: <hash>
  Author: <name>
  Date: <date>
```


## Rules

- Always reset bisect when done to return to the original branch.
- Automate the test when possible: `git bisect run <test-command>`.
- If a commit cannot be tested, use `git bisect skip`.

