Generate API documentation from route definitions and handlers.

## Steps

1. Detect the web framework in use (Express, Fastify, FastAPI, Gin, Actix, etc.).
2. Scan for route definitions:
   - Express/Fastify: `app.get()`, `router.post()`, route files.
   - FastAPI: `@app.get()`, `@router.post()` decorators.
   - Go: `http.HandleFunc()`, gin route groups.
3. For each endpoint, extract:
   - HTTP method and path (including path parameters).
   - Request body schema from TypeScript types, Pydantic models, or struct tags.
   - Query parameters and their types.
   - Response format from return types or response calls.
   - Authentication requirements from middleware.
   - Rate limiting or other middleware constraints.
4. Generate documentation in the specified format (OpenAPI/Swagger, Markdown, or both).
5. Include request/response examples with realistic data.
6. Write the output to `docs/api/` or the specified location.

## Format

```markdown
## <METHOD> <path>

<Description>

**Auth**: Required | Public
**Rate Limit**: <limit>

### Parameters
| Name | In | Type | Required | Description |
|------|-----|------|----------|-------------|

### Request Body
```json
{ "example": "value" }
```

### Response (200)
```json
{ "example": "response" }
```
```

## Rules

- Document every public endpoint; skip internal-only routes.
- Include error responses (400, 401, 403, 404, 500) with example bodies.
- Use actual TypeScript/Python types for schemas, not generic `object` or `any`.
- Keep examples realistic and consistent across related endpoints.
- Note deprecated endpoints clearly with migration guidance.
