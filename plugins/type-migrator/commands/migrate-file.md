# /migrate-file - Migrate JS to TypeScript

Convert a JavaScript file to TypeScript with proper type annotations.

## Steps

1. Read the target JavaScript file and understand its structure
2. Rename the file from .js to .ts (or .jsx to .tsx for React components)
3. Add TypeScript configuration if tsconfig.json does not exist
4. Infer types from usage patterns: variable assignments, function parameters, return values
5. Add explicit type annotations to function parameters and return types
6. Convert require/module.exports to import/export syntax
7. Add interface definitions for object shapes used in the file
8. Replace `any` types with specific types wherever inferable
9. Handle common patterns: callbacks, promises, event handlers
10. Fix type errors reported by the TypeScript compiler
11. Add JSDoc-compatible type comments where types are complex
12. Run the TypeScript compiler in strict mode and report remaining issues

## Rules

- Enable strict mode in tsconfig.json for maximum type safety
- Use interfaces for object shapes, type aliases for unions and primitives
- Prefer unknown over any for truly unknown types
- Add null checks where variables could be null or undefined
- Convert dynamic property access to typed alternatives
- Keep the same file structure and logic; only add types
- Do not change runtime behavior during migration
