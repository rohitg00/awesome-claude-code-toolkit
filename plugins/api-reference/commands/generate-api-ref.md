# /generate-api-ref - Generate API Reference

Generate API reference documentation from source code and route definitions.

## Steps

1. Detect the API framework: Express, FastAPI, Django REST, Spring Boot, Gin, etc.
2. Scan route definitions to find all API endpoints
3. For each endpoint, extract: HTTP method, path, middleware, handler function
4. Parse handler functions to identify request parameters (path, query, body, headers)
5. Extract request/response schemas from TypeScript types, Pydantic models, or JSDoc
6. Identify authentication requirements from middleware chains
7. Find example request/response pairs from test files or inline documentation
8. Detect rate limiting, pagination, and caching configurations
9. Generate markdown documentation for each endpoint with: method, path, description, parameters, request body, response, errors
10. Group endpoints by resource or router module
11. Add a table of contents and overview section
12. Save documentation to docs/api-reference.md or the specified output path

## Rules

- Include all HTTP methods (GET, POST, PUT, PATCH, DELETE) for each resource
- Document error responses (400, 401, 403, 404, 500) with example payloads
- Use the actual TypeScript/Python types, not simplified versions
- Include authentication requirements for each endpoint
- Show curl examples for at least the primary endpoints
- Do not document internal or health-check endpoints unless requested
- Keep parameter descriptions concise but include type and required status
