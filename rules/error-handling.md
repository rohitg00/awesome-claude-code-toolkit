# Error Handling Rules

## Error Types
- Define specific error types for different failure categories.
- Use error codes or error classes, not raw strings.
- Include context in errors: what operation failed, what input caused it, what was expected.
- Distinguish between client errors (bad input) and server errors (internal failure).

## Error Chains
- Wrap lower-level errors with context when propagating up the stack.
- Preserve the original error as a `cause` for debugging.
- Do not swallow errors silently. If you catch, either handle it or re-throw with context.
- Log the full error chain at the point where the error is finally handled.

```typescript
try {
  await db.query(sql);
} catch (err) {
  throw new DatabaseError("Failed to fetch user by email", { cause: err });
}
```

## User-Facing Messages
- Show clear, actionable messages to users. Tell them what happened and what to do next.
- Never expose stack traces, internal paths, or database details to users.
- Use error codes that users or support can reference.
- Provide different detail levels: user message (UI), error code (API), full trace (logs).

## Logging
- Log errors with structured data: timestamp, error type, message, stack, request context.
- Use log levels appropriately: ERROR for failures, WARN for degraded behavior, INFO for operations.
- Include correlation IDs to trace errors across services.
- Do not log sensitive data (passwords, tokens, PII) even in error messages.

## Recovery Patterns
- Use retry with exponential backoff for transient failures (network, rate limits).
- Set maximum retry counts and circuit breakers for external dependencies.
- Provide fallback values or degraded functionality when non-critical services fail.
- Use timeouts on all external calls. A hanging request is worse than a failed one.

## API Error Responses
- Use standard HTTP status codes: 400 (bad input), 401 (unauthenticated), 403 (unauthorized), 404 (not found), 422 (validation), 429 (rate limit), 500 (internal).
- Return consistent error response shapes across all endpoints.
- Include a machine-readable error code and a human-readable message.

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Email format is invalid",
    "details": [{ "field": "email", "issue": "Must be a valid email address" }]
  }
}
```

## Anti-Patterns
- Do not use `catch (e) {}` (empty catch blocks).
- Do not use exceptions for control flow (e.g., using throw to exit a loop).
- Do not return null/undefined to indicate failure. Use Result types or throw typed errors.
- Do not log and throw the same error (causes duplicate log entries).
