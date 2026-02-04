Design a backend service architecture with clear boundaries, data models, and API contracts.

## Steps


1. Define the service scope:
2. Design the data model:
3. Design the API layer:
4. Plan the service internals:
5. Design inter-service communication:
6. Plan for observability:
7. Document the service contract.

## Format


```
Service: <name>
Domain: <what it owns>
Entities: <data model summary>
API Endpoints: <list>
```


## Rules

- Each service should own its data; no shared databases.
- Design for failure: every external call can fail.
- Use interface segregation; expose only what consumers need.

