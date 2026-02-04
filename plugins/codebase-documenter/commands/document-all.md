Auto-document the entire codebase by generating module-level docs, function signatures, and API references.

## Steps


1. Scan the project structure to identify all source files and their organization.
2. For each module or directory:
3. For each public function or method:
4. Generate an API reference organized by module.
5. Create a dependency graph showing how modules relate.
6. Identify undocumented or poorly documented areas.
7. Output documentation in the project's preferred format (JSDoc, docstrings, etc.).

## Format


```
# Module: <name>
Purpose: <what this module does>
Exports: <list of public APIs>
Dependencies: <what it imports>
```


## Rules

- Follow existing documentation conventions in the project.
- Only document public/exported APIs, not internal helpers.
- Include real usage examples found in the codebase, not fabricated ones.

