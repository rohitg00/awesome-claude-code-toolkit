Generate an OpenAPI 3.1 specification from existing API routes and handlers.

## Steps


1. Scan the project for API route definitions:
2. For each endpoint, extract:
3. Generate the OpenAPI spec:
4. Add authentication schemes:
5. Add examples for each endpoint.
6. Validate the generated spec:
7. Save as openapi.yaml or openapi.json.

## Format


```yaml
openapi: "3.1.0"
info:
  title: <API Name>
  version: <version>
```


## Rules

- Use OpenAPI 3.1 unless the project requires 3.0 compatibility.
- Every endpoint must have at least one response defined.
- Use $ref for reusable schemas instead of inline definitions.

