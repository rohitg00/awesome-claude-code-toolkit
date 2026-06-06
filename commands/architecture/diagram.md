Generate Mermaid diagrams from codebase analysis or description.

## Steps

1. Determine the diagram type from the argument or context:
   - `flowchart` - Process flows, request handling, business logic.
   - `sequenceDiagram` - API call sequences, service interactions.
   - `classDiagram` - Module structure, class relationships.
   - `erDiagram` - Database schema, entity relationships.
   - `graph` - Dependency trees, module relationships.
   - `stateDiagram-v2` - State machines, workflow states.
2. If generating from code:
   - Scan imports and exports to map module dependencies.
   - Read route definitions for sequence diagrams.
   - Parse database schemas for ER diagrams.
   - Analyze class hierarchies for class diagrams.
3. If generating from description, parse the user's requirements.
4. Build the Mermaid syntax with proper relationships and labels.
5. Write the diagram to a markdown file or embed in an existing doc.
6. Validate the syntax is correct Mermaid that will render properly.

## Format

````markdown
```mermaid
<diagram-type>
    <nodes and relationships>
```
````

## Rules

- Keep diagrams focused; split large systems into multiple diagrams.
- Use descriptive labels on all edges and nodes.
- Limit diagrams to 20 nodes maximum for readability.
- Use consistent naming conventions matching the codebase.
- Add a brief text description above each diagram explaining what it shows.
- Use subgraphs to group related components.
