Validate an existing OpenAPI specification for correctness and completeness.

## Steps


1. Load the OpenAPI spec file (YAML or JSON).
2. Validate structural correctness:
3. Validate references:
4. Check completeness:
5. Check for common issues:
6. Report findings with severity levels.
7. Suggest fixes for each issue found.

## Format


```
Spec: <filename>
Version: <openapi version>
Endpoints: <count>
Schemas: <count>
```


## Rules

- Validate against the official OpenAPI specification schema.
- Errors must be fixed before the spec can be considered valid.
- Warnings indicate best practice violations.

