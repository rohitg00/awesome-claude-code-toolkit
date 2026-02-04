# /tree-shake - Optimize Tree Shaking

Improve tree shaking effectiveness to reduce bundle size.

## Steps

1. Analyze the current build configuration for tree shaking settings
2. Check package.json for sideEffects field configuration
3. Identify imports that prevent tree shaking: namespace imports, CommonJS requires
4. Find barrel files (index.ts re-exports) that bundle entire modules
5. Check for packages that do not support tree shaking (no ES modules)
6. Convert namespace imports to named imports where possible
7. Add sideEffects: false to package.json if all modules are pure
8. Configure the bundler to mark specific files as side-effect-free
9. Replace non-tree-shakeable packages with tree-shakeable alternatives
10. Split barrel files into direct imports for large modules
11. Rebuild and measure the size difference
12. Report: modules eliminated, size reduction, remaining issues

## Rules

- Never mark files with side effects as side-effect-free
- Verify that tree shaking does not remove needed code
- Prefer named imports over namespace imports for better tree shaking
- Check that all internal packages have proper ESM exports
- Do not break the public API of packages when restructuring exports
- Test the application thoroughly after tree shaking changes
- Document any sideEffects configuration with comments explaining why
