Fetch up-to-date library documentation via Context7 to ensure accurate code generation.

## Steps


1. Identify the library or framework the user needs docs for:
2. Resolve the library ID using Context7:
3. Query the documentation:
4. Present the documentation in a usable format:
5. Apply the documentation to the current task:
6. Cache the result to avoid redundant lookups.

## Format


```
Library: <name>@<version>
Source: Context7
Topic: <what was looked up>
Key APIs:
```


## Rules

- Always verify the documentation version matches the installed version.
- Prefer official documentation over community examples.
- Note any APIs marked as experimental or deprecated.

