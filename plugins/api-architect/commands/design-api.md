# /api-architect:design-api

Design a RESTful or GraphQL API based on the project's domain model and requirements.

## Process

1. Analyze the existing codebase to understand the domain:
   - Read database models, schemas, or type definitions to identify entities
   - Check existing routes or resolvers to understand current API surface
   - Look for DTOs, serializers, or validation schemas
   - Identify relationships between entities (one-to-many, many-to-many)

2. Design the resource hierarchy following REST conventions:
   - Map each core entity to a resource with a plural noun URL (`/users`, `/orders`, `/products`)
   - Nest sub-resources only one level deep (`/users/{id}/orders`, not `/users/{id}/orders/{id}/items`)
   - Use query parameters for filtering, sorting, and pagination on collection endpoints
   - Define standard operations for each resource:
     - `GET /resources` - List with pagination (cursor-based preferred over offset)
     - `GET /resources/{id}` - Retrieve single resource
     - `POST /resources` - Create new resource
     - `PUT /resources/{id}` - Full update (replace)
     - `PATCH /resources/{id}` - Partial update
     - `DELETE /resources/{id}` - Remove resource

3. Define request and response shapes:
   - Use consistent envelope format: `{ "data": ..., "meta": { "total", "cursor" } }`
   - Include only necessary fields in list responses (summary representation)
   - Return full representation on single-resource endpoints
   - Define error response format: `{ "error": { "code": "...", "message": "...", "details": [...] } }`
   - Use ISO 8601 for dates, UUIDs for identifiers, lowercase snake_case for field names

4. Design authentication and authorization:
   - Recommend Bearer token (JWT or opaque) via Authorization header
   - Define permission model: which roles can access which endpoints
   - Identify public vs authenticated vs admin-only endpoints
   - Include rate limiting headers in response design (X-RateLimit-Limit, X-RateLimit-Remaining)

5. Plan for versioning:
   - Recommend URL prefix versioning (`/v1/resources`) for simplicity
   - Document the deprecation policy for old versions
   - Design backward-compatible extension patterns (additive fields, optional parameters)

6. Design cross-cutting concerns:
   - Pagination: cursor-based with `?cursor=` and `?limit=` parameters
   - Filtering: field-based query params (`?status=active&created_after=2024-01-01`)
   - Sorting: `?sort=created_at:desc,name:asc`
   - Field selection: `?fields=id,name,email` for bandwidth optimization
   - Bulk operations: `POST /resources/batch` for creating multiple items

## Output

Present the API design as a structured table of endpoints with:
- HTTP method and path
- Description
- Request body (if applicable)
- Response shape
- Authentication requirement
- Example curl command for each endpoint

## Rules

- Follow the principle of least surprise: APIs should behave as developers expect
- Use standard HTTP status codes correctly (201 for creation, 204 for deletion, 409 for conflicts)
- Design idempotent operations where possible (PUT and DELETE should be safe to retry)
- Never expose internal IDs, database column names, or implementation details
- Consider forward compatibility: design fields that can be extended without breaking clients
- Ask the user for clarification on business rules before making assumptions
