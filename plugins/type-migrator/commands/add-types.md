# /add-types - Add Type Definitions

Add TypeScript type definitions to existing TypeScript files with weak typing.

## Steps

1. Scan the file for `any` types, implicit any parameters, and untyped variables
2. Analyze function call sites to infer parameter and return types
3. Check imported modules for available type definitions
4. Replace `any` types with specific types based on usage analysis
5. Add generic type parameters where functions operate on multiple types
6. Create interface definitions for object literals used as parameters
7. Add union types for variables that accept multiple value types
8. Type event handlers and callback functions with proper signatures
9. Add type assertions only where type narrowing is not possible
10. Ensure all exported functions have explicit parameter and return types
11. Run the TypeScript compiler and fix any new type errors
12. Report: types added, any types remaining, type coverage percentage

## Rules

- Never use type assertions (as) to silence errors; fix the root cause
- Prefer type inference for local variables; add explicit types for function boundaries
- Use utility types (Partial, Required, Pick, Omit) instead of duplicating interfaces
- Add readonly modifiers for properties that should not be mutated
- Use const assertions for literal values and enums
- Check DefinitelyTyped for missing third-party type definitions
- Target 100% type coverage for public API functions
