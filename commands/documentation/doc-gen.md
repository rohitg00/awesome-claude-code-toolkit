Generate documentation from the codebase for the specified scope.

## Steps

### 1. Determine Scope
- If a specific file or module is provided, document that.
- If no scope is given, identify the most important public-facing modules.
- Focus on: exported functions, public classes, API endpoints, configuration options.

### 2. Read the Code
- Read source files to understand function signatures, types, and behavior.
- Look at existing tests for usage examples.
- Check for existing doc comments or README sections to update rather than replace.

### 3. Generate API Documentation
For each public function/method:
```
### functionName(param1: Type, param2: Type): ReturnType

Brief description of what it does.

**Parameters:**
- `param1` - Description and constraints.
- `param2` - Description and defaults.

**Returns:** Description of return value.

**Throws:** Error conditions.

**Example:**
```code
const result = functionName("value", { option: true });
```
```

### 4. Generate README Sections
- **Installation**: How to install and configure.
- **Quick Start**: Minimal example to get started.
- **Configuration**: Available options with defaults.
- **API Reference**: Link to or inline the API docs.

### 5. Add Inline Documentation
For complex logic (non-obvious algorithms, business rules, workarounds):
- Add a brief comment explaining **why**, not what.
- Document preconditions and postconditions for critical functions.
- Note any gotchas or non-obvious behavior.

## Rules

- Document behavior, not implementation. Describe what a function does, not how.
- Use concrete examples, not abstract descriptions.
- Keep docs close to code: inline comments for complex logic, JSDoc/docstrings for public APIs.
- Do not document obvious code (getters, setters, simple wrappers).
- If a function is too complex to document clearly, that is a signal to refactor it.
- Update existing documentation rather than creating duplicate files.
