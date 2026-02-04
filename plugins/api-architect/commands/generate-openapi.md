# /api-architect:generate-openapi

Generate an OpenAPI 3.1 specification from the existing codebase or API design.

## Process

1. Discover existing API routes and handlers:
   - For Express/Fastify: search for `app.get`, `app.post`, `router.use` patterns
   - For FastAPI/Flask: search for `@app.route`, `@router.get` decorators
   - For Go: search for `http.HandleFunc`, `r.GET`, `mux.Handle` patterns
   - For Spring: search for `@GetMapping`, `@PostMapping`, `@RestController` annotations
   - Read each handler to understand request parameters, body, and response shape

2. Extract schema information:
   - Parse TypeScript interfaces, Python dataclasses/Pydantic models, Go structs, or Java DTOs
   - Map field types to OpenAPI types (string, integer, number, boolean, array, object)
   - Identify required vs optional fields from type annotations or validation rules
   - Extract enum values from code constants or type unions
   - Document field constraints (minLength, maxLength, pattern, minimum, maximum)

3. Build the OpenAPI specification:

### Info Section
- Set title from package.json name or project directory
- Set version from package.json version or git tag
- Write a concise description of the API's purpose

### Servers
- Add localhost development server
- Add placeholder for production server URL

### Paths
- One path entry per route
- Include all HTTP methods supported by each path
- Define path parameters with types and descriptions
- Define query parameters for list endpoints (pagination, filtering, sorting)
- Reference request body schemas from components
- Define response schemas for each status code (200, 201, 400, 401, 404, 500)

### Components
- Define reusable schemas for each domain entity
- Create shared error response schema
- Create pagination metadata schema
- Define security schemes (Bearer JWT, API Key, OAuth2 as applicable)
- Use `$ref` extensively to avoid duplication

### Security
- Apply security requirements globally or per-operation
- Document which endpoints are public (override global security with empty array)

4. Validate the specification:
   - Ensure all `$ref` references resolve correctly
   - Verify that every path parameter has a corresponding parameter definition
   - Check that request bodies have content types specified
   - Confirm response schemas match the actual handler return types

5. Generate example values for each schema to make the spec immediately testable.

## Output

Write the specification to `openapi.yaml` (or `openapi.json` if the project prefers JSON).
If an existing spec file is found, present a diff and ask before overwriting.

## Rules

- Use OpenAPI 3.1.0 for JSON Schema compatibility
- Every endpoint must have a summary, description, and at least one response defined
- Use semantic operation IDs: `listUsers`, `getUserById`, `createOrder`
- Include realistic example values, not placeholder text like "string" or "0"
- Group related endpoints with tags matching the resource name
- Add `x-codegen` extensions if the project uses code generation tools
- Prefer YAML format for readability unless the project convention is JSON
