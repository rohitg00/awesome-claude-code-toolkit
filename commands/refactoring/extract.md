Extract a function, component, or module from existing code into its own unit.

## Steps

1. Identify the code block to extract from the argument (file path and line range, or description).
2. Read the target file and analyze the selected code:
   - Determine all variables used within the block that are defined outside it (parameters).
   - Determine all variables modified within the block that are used after it (return values).
   - Identify side effects (I/O, mutations, DOM manipulation).
3. Choose the extraction type:
   - **Function**: Pure logic with clear inputs and outputs.
   - **Component**: UI rendering with props interface (React, Vue, Svelte).
   - **Module**: Related functions that form a cohesive unit.
   - **Hook**: Stateful logic with lifecycle concerns (React hooks).
   - **Class method**: Logic belonging to a specific class.
4. Create the extracted unit:
   - Name it descriptively based on its purpose.
   - Define a clear parameter interface (TypeScript types, Python type hints).
   - Add a return type annotation.
5. Replace the original code with a call to the extracted unit.
6. Update imports in the original file and any files that need the new export.
7. Run tests to verify the refactoring preserves behavior.

## Format

```
Extracted: <type> <name> from <source-file>
  To: <destination-file>
  Parameters: <param-list>
  Returns: <return-type>
  Lines replaced: <start>-<end>
  Tests: <pass/fail>
```

## Rules

- The extraction must be behavior-preserving; run tests before and after.
- Choose names that describe the purpose, not the implementation.
- Keep the extracted unit's parameter count under 5; use an options object if more.
- Maintain the same error handling behavior in the extracted code.
- Update all call sites if moving a function to a different module.
