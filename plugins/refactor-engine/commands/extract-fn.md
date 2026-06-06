Extract a block of code into a well-named, reusable function with proper typing.

## Steps

1. Identify the code block to extract:
   - Accept file path with line range, or a description of the logic.
   - If no range given, detect the longest or most complex function and suggest extraction.
2. Analyze the code block:
   - Variables read from outer scope become function parameters.
   - Variables written and used later become return values.
   - Side effects (I/O, mutations) are documented in the function's contract.
3. Determine the function signature:
   - Name: verb + noun describing the action (e.g., `calculateTotalPrice`).
   - Parameters: typed, ordered by importance, grouped in object if more than 3.
   - Return type: explicit annotation.
4. Extract the function:
   - Move the code block to the new function.
   - Add type annotations for parameters and return value.
   - Replace the original code with a function call.
5. If the function is reusable across modules, move it to a shared utilities file.
6. Run tests to verify behavior is preserved.

## Format

```
Extracted: <functionName>
  From: <file>:<startLine>-<endLine>
  To: <destination file>
  Params: (<paramList>)
  Returns: <returnType>
  Tests: passing
```

## Rules

- The extraction must preserve identical behavior; run tests before and after.
- Name functions based on purpose, not implementation.
- Keep parameter count under 4; use an options object for more.
- Add a doc comment explaining what the extracted function does.
- Do not extract trivially short code (under 3 lines) unless it clarifies intent.
