---
name: api-design-patterns
description: REST API design with resource naming, pagination, versioning, and OpenAPI spec generation
---

# API Design Patterns

## Resource Naming

- Use plural nouns: `/users`, `/orders`, `/products`
- Nest for relationships: `/users/{id}/orders`
- Max nesting depth: 2 levels. Beyond that, use query params or top-level resources
- Use kebab-case: `/user-profiles`, not `/userProfiles`
- Never put verbs in URLs: `/users/{id}/activate` is wrong, use `POST /users/{id}/activation`

## HTTP Methods

| Method | Purpose | Idempotent | Request Body | Success Code |
|--------|---------|------------|-------------|-------------|
| GET | Read resource(s) | Yes | No | 200 |
| POST | Create resource | No | Yes | 201 |
| PUT | Full replace | Yes | Yes | 200 |
| PATCH | Partial update | No | Yes | 200 |
| DELETE | Remove resource | Yes | No | 204 |

Return `Location` header on POST with the URL of the created resource.

## Status Codes

```
200 OK              - Successful read/update
201 Created         - Successful creation
204 No Content      - Successful delete
400 Bad Request     - Validation error (include field-level errors)
401 Unauthorized    - Missing or invalid authentication
403 Forbidden       - Authenticated but not authorized
404 Not Found       - Resource does not exist
409 Conflict        - State conflict (duplicate, version mismatch)
422 Unprocessable   - Semantically invalid (valid JSON, bad values)
429 Too Many Reqs   - Rate limited (include Retry-After header)
500 Internal Error  - Unhandled server error (never expose stack traces)
```

## Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Must be a valid email address" },
      { "field": "age", "message": "Must be at least 18" }
    ]
  }
}
```

Use consistent error codes across the API. Document every code in your API reference.

## Cursor-Based Pagination (preferred)

```
GET /users?limit=20&cursor=eyJpZCI6MTAwfQ

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIwfQ",
    "has_more": true
  }
}
```

Use cursor pagination for large or frequently changing datasets. Encode cursors as opaque base64 strings. Never expose raw IDs in cursors.

## Offset-Based Pagination (simple cases only)

```
GET /users?page=3&per_page=20

Response:
{
  "data": [...],
  "pagination": {
    "page": 3,
    "per_page": 20,
    "total": 245,
    "total_pages": 13
  }
}
```

Only use offset pagination when total count is cheap and dataset is small.

## Filtering and Sorting

```
GET /orders?status=pending&created_after=2025-01-01&sort=-created_at,+total
GET /products?category=electronics&price_min=100&price_max=500
GET /users?search=john&fields=id,name,email
```

Use field selection (`fields` param) to reduce payload size. Prefix sort fields with `-` for descending.

## Versioning

Prefer URL path versioning for simplicity:
```
/api/v1/users
/api/v2/users
```

Rules:
- Never break v1 once published. Add fields, never remove them.
- New required fields = new version
- Deprecate old versions with `Sunset` header and 6-month notice
- Support at most 2 active versions simultaneously

## Request/Response Headers

```
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
X-Request-Id: <uuid>          # For tracing
X-RateLimit-Limit: 100        # Requests per window
X-RateLimit-Remaining: 47     # Remaining in window
X-RateLimit-Reset: 1700000000 # Window reset Unix timestamp
Retry-After: 30               # Seconds until rate limit resets
```

Always return `X-Request-Id` in responses for debugging.

## OpenAPI Spec Guidelines

- Write spec first, then implement (spec-driven development)
- Use `$ref` for shared schemas: `$ref: '#/components/schemas/User'`
- Define `examples` for every endpoint
- Use `oneOf`/`anyOf` for polymorphic responses
- Generate client SDKs from the spec, never hand-write them
- Validate requests against the spec in middleware

```yaml
paths:
  /users/{id}:
    get:
      operationId: getUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'
```

## Rate Limiting Strategy

- Apply per-user, per-endpoint limits
- Use sliding window algorithm (not fixed window)
- Return `429` with `Retry-After` header
- Exempt health check and auth endpoints from rate limits
- Log rate-limited requests for abuse detection
