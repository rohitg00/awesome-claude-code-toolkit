Add a new feature module to an existing project with all supporting files.

## Steps

1. Parse the feature specification from the argument:
   - Feature name and description.
   - Type: CRUD resource, service, middleware, CLI command, UI component.
2. Analyze the existing project structure:
   - Detect conventions for file organization.
   - Identify existing patterns for routing, models, services.
   - Check for shared utilities and types.
3. Generate feature files based on type:
   - **CRUD resource**: Model, service, controller/handler, routes, validation schema, tests.
   - **Service**: Service class/module, interface/types, tests.
   - **Middleware**: Middleware function, configuration, tests.
   - **CLI command**: Command definition, handler, help text, tests.
   - **UI component**: Component, styles, stories, tests.
4. Wire up the feature:
   - Add routes to the router.
   - Register middleware in the app configuration.
   - Export from the module index.
5. Generate tests for the new feature.
6. Verify the project still builds and existing tests pass.

## Format

```
Feature added: <name>
Type: <feature-type>

Files created:
  - src/<feature>/model.ts
  - src/<feature>/service.ts
  - src/<feature>/routes.ts
  - tests/<feature>/service.test.ts

Wired up:
  - Routes registered at /<feature>
  - Tests added: <N>
```

## Rules

- Follow existing project conventions for naming, structure, and patterns.
- Include validation for all inputs at the boundary.
- Add error handling consistent with the project's error handling approach.
- Generate at least one test per public function or endpoint.
- Update the project CLAUDE.md with the new feature's purpose and location.
