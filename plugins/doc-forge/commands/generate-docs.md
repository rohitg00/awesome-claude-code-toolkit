# /doc-forge:generate-docs

Generate comprehensive documentation for the current project or a specified module.

## Process

1. Survey the project to understand its architecture:
   - Read the entry point (main.ts, index.js, app.py, main.go, src/lib.rs)
   - Identify the module structure and public API surface
   - Check for existing documentation (docs/ directory, JSDoc, docstrings, rustdoc)
   - Read package.json, pyproject.toml, or Cargo.toml for project metadata

2. Generate documentation for each public module:

### Module Overview
- Purpose: one paragraph explaining what this module does and when to use it
- Dependencies: what this module requires and what depends on it
- Architecture notes: key design decisions and patterns used

### Function/Method Documentation
- For each exported function, document:
  - Purpose in one sentence
  - Parameters with types, descriptions, and default values
  - Return type and description
  - Exceptions/errors that can be thrown and under what conditions
  - Usage example showing the most common invocation
  - Edge cases: behavior with null inputs, empty collections, boundary values

### Type/Interface Documentation
- For each exported type, document:
  - Purpose and when to use this type
  - Each field with its type, description, and constraints
  - Relationships to other types (extends, implements, references)
  - Construction patterns (factory functions, builders, constructors)

### Configuration Documentation
- Environment variables with descriptions, types, defaults, and required/optional status
- Configuration file formats with annotated examples
- Feature flags and their effects on behavior

3. Generate usage examples:
   - Quick start: minimal code to get the module working
   - Common patterns: 3-5 typical use cases with complete code snippets
   - Advanced usage: composition with other modules, custom configuration
   - Error handling: how to properly handle failures from this module

4. Create a table of contents linking all documented modules.

5. Format the documentation appropriate to the language:
   - TypeScript/JavaScript: JSDoc comments in source files + markdown guides
   - Python: docstrings (Google style) in source files + markdown guides
   - Go: godoc comments in source files
   - Rust: rustdoc comments with examples that compile

## Output

Write documentation files to a `docs/` directory. For inline documentation, add it directly to source files. Present a summary of all files created or modified.

## Rules

- Documentation must be accurate: verify claims by reading the actual implementation
- Use concrete examples, not abstract descriptions ("Pass a user ID" not "Pass an identifier")
- Keep examples runnable: they should work if copied into a project
- Do not document private/internal functions unless they are complex and critical
- Match the existing documentation style if the project already has docs
- Avoid restating what the code obviously does; focus on why and when
- Include a "Getting Started" section for top-level project documentation
- Update the table of contents and any index files when adding new documentation
