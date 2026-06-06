# /doc-forge:api-docs

Generate API reference documentation from source code annotations, types, and route definitions.

## Process

1. Discover the API surface:
   - Scan for route definitions, controller classes, or handler functions
   - Read middleware chain to understand request preprocessing (auth, validation, parsing)
   - Identify the response format conventions (JSON envelope, error structure, pagination)
   - Check for existing API documentation (Swagger UI, Redoc, custom docs)

2. For each endpoint, extract and document:

### Endpoint Header
- HTTP method and full URL path (including base path and version prefix)
- Brief description of what the endpoint does
- Authentication requirement (public, authenticated, admin-only)
- Rate limit tier if applicable

### Request Documentation
- **Path Parameters**: name, type, description, example value, validation constraints
- **Query Parameters**: name, type, required/optional, default value, description, allowed values
- **Headers**: required custom headers beyond standard ones (Accept, Content-Type)
- **Request Body**: full schema with field descriptions, types, constraints, and example payload
  - Mark required fields explicitly
  - Document nested objects and arrays with their own field descriptions
  - Include validation rules (min/max length, regex patterns, enum values)

### Response Documentation
- For each possible status code:
  - Status code and meaning in context
  - Response body schema with field descriptions
  - Complete example response payload
- Standard status codes to document:
  - 200/201 for success
  - 400 for validation errors (with example of error detail format)
  - 401 for unauthenticated requests
  - 403 for insufficient permissions
  - 404 for resource not found
  - 409 for conflict (duplicate creation, version mismatch)
  - 429 for rate limit exceeded
  - 500 for server errors (with error correlation ID format)

### Code Examples
- curl command for the most common use case
- Language-specific examples if SDK libraries exist (JavaScript fetch, Python requests)
- WebSocket examples if the API includes real-time features

3. Generate cross-reference documentation:
   - List all shared types/schemas used across multiple endpoints
   - Document the authentication flow end-to-end (obtain token, refresh, revoke)
   - Describe pagination patterns with examples of traversing pages
   - Document webhook payloads if the API sends outbound notifications

4. Organize endpoints by resource:
   - Group related endpoints under resource headers (Users, Orders, Products)
   - Order operations within each group: List, Get, Create, Update, Delete
   - Include a quick-reference table at the top with all endpoints

5. Add operational information:
   - Base URL for each environment (development, staging, production)
   - Authentication setup instructions
   - Rate limiting policy and headers
   - Versioning policy and migration guide for deprecated endpoints
   - Error handling best practices

## Output

Generate documentation in the format most appropriate for the project:
- Markdown files in `docs/api/` for static documentation
- OpenAPI spec for tool-generated documentation (Swagger UI, Redoc)
- Inline source annotations if the project uses auto-generation tools

## Rules

- Every example must be a valid, working request that returns the documented response
- Do not document internal-only endpoints unless explicitly requested
- Keep descriptions concise: one sentence for the summary, expand only when behavior is non-obvious
- Use the actual field names from the code, not renamed or prettified versions
- Document deprecated endpoints with their replacement and sunset date
- Include rate limit information per endpoint if limits vary
- Verify response schemas match the actual serializer or response builder output
