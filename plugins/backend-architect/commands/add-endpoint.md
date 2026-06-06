Add a new API endpoint to an existing backend service with validation and tests.

## Steps


1. Define the endpoint specification:
2. Identify the framework and add the route:
3. Implement the handler:
4. Add input validation:
5. Add middleware if needed:
6. Write tests:
7. Update API documentation.

## Format


```
Endpoint: <METHOD> <path>
Auth: <required|optional|none>
Request: <body schema>
Response: <success schema>
```


## Rules

- Follow REST conventions: POST for create, PUT for replace, PATCH for update.
- Return appropriate HTTP status codes (201 for create, 204 for delete).
- Validate all input before processing.

