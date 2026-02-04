# Coding Style

## Naming Conventions
- Variables and functions: camelCase (JS/TS), snake_case (Python/Rust/Go).
- Classes and types: PascalCase in all languages.
- Constants: UPPER_SNAKE_CASE for true constants, camelCase for derived values.
- Booleans: prefix with `is`, `has`, `can`, `should` (e.g., `isActive`, `hasPermission`).
- Files: kebab-case for most files, PascalCase for React components.

## File Organization
- One exported concept per file. If a file has multiple unrelated exports, split it.
- Group files by feature (not by type) in larger projects.
- Keep files under 300 lines. If longer, extract sub-modules.
- Index files should only re-export, never contain logic.

## Import Ordering
1. Standard library / built-in modules.
2. External packages (node_modules, pip packages).
3. Internal absolute imports (from project root).
4. Relative imports (from current directory).
5. Type-only imports last.
- Blank line between each group. Alphabetical within each group.

## Code Clarity
- No magic numbers. Extract named constants with descriptive names.
- No nested ternaries. Use if/else or extract to a function.
- Maximum function length: 40 lines. If longer, extract helpers.
- Maximum function parameters: 3. Use an options object for more.
- Prefer explicit over implicit. Avoid clever one-liners that sacrifice readability.
- Remove all dead code. Do not comment out code "for later."

## Formatting
- Use the project's formatter (Prettier, Black, gofmt, rustfmt). Do not manually format.
- Consistent indentation: 2 spaces (JS/TS), 4 spaces (Python), tabs (Go).
- Trailing commas in multi-line structures (JS/TS).
- No trailing whitespace. Files end with a single newline.
