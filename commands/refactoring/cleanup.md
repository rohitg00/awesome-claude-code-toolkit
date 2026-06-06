Find and remove dead code, unused imports, and unreachable branches.

## Steps

1. Detect the language and available tooling:
   - TypeScript/JavaScript: Use `tsc --noEmit` for unused locals, `eslint` with `no-unused-vars`.
   - Python: Use `vulture` or `pyflakes` for dead code detection.
   - Go: `go vet` reports unused variables; `staticcheck` finds dead code.
   - Rust: Compiler warnings for dead code with `#[warn(dead_code)]`.
2. Scan for unused exports:
   - Find all exported symbols.
   - Search the codebase for imports of each symbol.
   - Flag exports with zero import references (excluding entry points).
3. Detect unreachable code:
   - Code after unconditional return/throw/break statements.
   - Branches with impossible conditions (always true/false guards).
   - Feature flags that are permanently enabled or disabled.
4. Find unused dependencies:
   - Compare `package.json` dependencies against actual imports.
   - Check for packages used only in removed code.
5. Present findings grouped by category with confidence levels.
6. Apply removals only for high-confidence dead code (no dynamic references).
7. Run tests after each removal batch to catch false positives.

## Format

```
Dead Code Analysis
==================

Unused imports: <N>
  - <file>:<line> - import { <symbol> } from '<module>'

Unused exports: <N>
  - <file>:<line> - export <symbol> (0 references)

Unreachable code: <N>
  - <file>:<lines> - <reason>

Unused dependencies: <N>
  - <package> (last used: never / removed in <commit>)

Safe to remove: <N> items
Needs review: <N> items
```

## Rules

- Never remove code that might be used via dynamic imports, reflection, or string references.
- Preserve exports that are part of a public API or SDK.
- Skip test utilities, fixtures, and development-only code.
- Run the full test suite after removing each batch to catch false positives.
- Log removed code with git commit messages for easy reversal.
