# API Design

## REST Conventions
- Use plural nouns for resource paths: `/users`, `/orders`, `/products`.
- Map HTTP methods to operations: GET (read), POST (create), PUT (full update), PATCH (partial update), DELETE (remove).
- Use nested routes for relationships: `/users/:id/orders` not `/getUserOrders`.
- Keep URLs lowercase with hyphens: `/order-items` not `/orderItems`.
- Limit nesting to two levels. Beyond that, use query parameters or top-level routes.

## Status Codes
- 200 OK: Successful read or update.
- 201 Created: Successful resource creation. Include `Location` header.
- 204 No Content: Successful delete with no response body.
- 400 Bad Request: Validation failure or malformed input.
- 401 Unauthorized: Missing or invalid authentication.
- 403 Forbidden: Authenticated but lacks permission.
- 404 Not Found: Resource does not exist.
- 409 Conflict: Duplicate or state conflict.
- 422 Unprocessable Entity: Valid syntax but semantic errors.
- 429 Too Many Requests: Rate limit exceeded. Include `Retry-After` header.
- 500 Internal Server Error: Unhandled server failure. Never expose stack traces.

## Versioning
- Use URL path versioning for public APIs: `/api/v1/users`.
- Use header versioning for internal APIs: `Accept: application/vnd.api.v2+json`.
- Support the previous version for at least 6 months after deprecation.
- Return a `Deprecation` header on sunset-path endpoints.

## Pagination
- Use cursor-based pagination for large or real-time datasets: `?cursor=abc&limit=20`.
- Use offset pagination only for small, static datasets: `?page=1&per_page=25`.
- Default limit: 20 items. Maximum limit: 100 items.
- Return pagination metadata in the response: `{ data, meta: { cursor, hasMore, total } }`.

## Response Format
- Consistent envelope: `{ data, error, meta }` across all endpoints.
- Error responses: `{ error: { code: "VALIDATION_ERROR", message: "...", details: [...] } }`.
- Use ISO 8601 for all timestamps: `2026-01-15T09:30:00Z`.
- Return `null` for absent optional fields, not missing keys.
- Include `requestId` in all responses for traceability.

## Rate Limiting
- Public endpoints: 60 requests per minute.
- Authenticated endpoints: 600 requests per minute.
- Write endpoints: 30 requests per minute.
- Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
