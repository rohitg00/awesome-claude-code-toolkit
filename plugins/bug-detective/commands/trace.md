Trace the execution path of a request or operation through the codebase.

## Steps

1. Identify the starting point: HTTP request handler, event listener, CLI command, or function call.
2. Follow the execution path step by step:
   - Map each function call from entry to exit.
   - Note middleware, interceptors, or decorators in the chain.
   - Track data transformations at each step.
   - Identify async boundaries (awaits, callbacks, event emissions).
3. For each step in the trace, document:
   - File and function name.
   - Input parameters and their values/types.
   - Side effects (database queries, API calls, file writes).
   - Return value or thrown error.
4. Identify potential failure points:
   - Unhandled errors or missing try/catch blocks.
   - Implicit type conversions or coercions.
   - Missing validation at boundaries.
5. Generate a sequence diagram of the execution flow.
6. Highlight any performance bottlenecks (blocking I/O, N+1 queries).

## Format

```
Trace: <operation name>

1. [entry.ts:handleRequest] <- HTTP POST /api/users
2. [middleware/auth.ts:verify] <- checks JWT token
3. [services/user.ts:create] <- validates input, calls DB
4. [db/queries.ts:insert] <- INSERT INTO users ...
5. [services/user.ts:create] -> returns { id, email }
6. [entry.ts:handleRequest] -> 201 Created

Side effects: 1 DB write, 1 email sent
Potential issues: No transaction wrapping steps 4-5
```

## Rules

- Follow the actual code path, not assumptions about what it should do.
- Include error handling paths, not just the happy path.
- Note where logging exists and where it is missing.
- Flag any implicit dependencies or global state access.
