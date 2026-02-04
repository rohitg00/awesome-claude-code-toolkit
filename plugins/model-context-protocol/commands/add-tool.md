Add a new tool to an existing MCP server with proper schema and handler.

## Steps


1. Understand the tool requirements:
2. Define the tool schema:
3. Implement the tool handler:
4. Register the tool with the MCP server:
5. Add input validation:
6. Write a test for the tool handler.
7. Update the server documentation with the new tool.

## Format


```
Tool: <name>
Description: <what it does>
Parameters:
  - <name>: <type> (<required|optional>) - <description>
```


## Rules

- Tool names must be unique within the server.
- Descriptions must be clear enough for an AI to use the tool correctly.
- All required parameters must be validated before execution.

