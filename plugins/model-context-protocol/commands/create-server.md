Scaffold a new MCP (Model Context Protocol) server with tools, resources, and prompts.

## Steps


1. Determine the MCP server configuration:
2. Create the project structure:
3. Implement the server skeleton:
4. Add example tools:
5. Add example resources (if applicable):
6. Configure for Claude Desktop:
7. Test the server with a sample tool invocation.

## Format


```
Server: <name>
Transport: <stdio|sse>
Tools: <list of tools>
Resources: <list of resources>
```


## Rules

- Use Zod or Pydantic for input validation on all tools.
- Every tool must have a clear description for the AI model.
- Include error handling that returns useful error messages.

