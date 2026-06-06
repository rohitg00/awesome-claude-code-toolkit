Generate an n8n workflow JSON from a natural language description of the automation.

## Steps


1. Parse the automation description:
2. Design the workflow node graph:
3. Generate the n8n workflow JSON:
4. Add error handling:
5. Add workflow metadata:
6. Test the workflow structure for validity.
7. Provide setup instructions for required credentials.

## Format


```json
{
  "name": "<workflow name>",
  "nodes": [...],
  "connections": {...},
```


## Rules

- Use the latest n8n node types and API formats.
- Include credential placeholders, never hardcode secrets.
- Add error handling nodes for production workflows.

