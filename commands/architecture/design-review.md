Conduct a structured design review of a module, feature, or system component.

## Steps

1. Identify the scope of review from the argument (module path, feature name, or PR number).
2. Map the component boundaries:
   - Entry points (APIs, event handlers, CLI commands).
   - Internal modules and their responsibilities.
   - External dependencies and integration points.
   - Data flow from input to output.
3. Evaluate against design principles:
   - **Single Responsibility**: Does each module have one clear purpose?
   - **Dependency Direction**: Do dependencies flow inward (clean architecture)?
   - **Interface Segregation**: Are interfaces minimal and focused?
   - **Error Handling**: Are failures handled consistently and explicitly?
   - **Testability**: Can components be tested in isolation?
4. Check for common anti-patterns:
   - God objects or modules with too many responsibilities.
   - Circular dependencies between modules.
   - Leaky abstractions exposing internal implementation.
   - Configuration scattered across multiple locations.
5. Assess scalability and operational concerns:
   - Can this handle 10x current load?
   - What are the failure modes and recovery paths?
   - Is observability built in (logging, metrics, tracing)?
6. Produce a structured review with actionable recommendations.

## Format

```
## Design Review: <Component Name>

### Architecture Score: <1-5>/5

### Strengths
- What is well designed

### Concerns
- CRITICAL: Issues that need immediate attention
- WARNING: Issues to address before next milestone

### Recommendations
1. Specific actionable improvement
2. Specific actionable improvement

### Diagram
<Mermaid diagram of current architecture>
```

## Rules

- Be constructive; pair every criticism with a concrete suggestion.
- Focus on structural issues, not cosmetic ones.
- Consider the team's current constraints and pragmatic tradeoffs.
- Reference specific files and line numbers where applicable.
