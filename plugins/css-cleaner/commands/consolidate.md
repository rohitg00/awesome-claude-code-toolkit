# /consolidate - Consolidate CSS

Merge and consolidate duplicate CSS rules and redundant stylesheets.

## Steps

1. Parse all CSS files and build a map of all rules and their properties
2. Identify duplicate selectors with identical property declarations
3. Find selectors with overlapping properties that can be merged
4. Detect redundant property declarations overridden by later rules
5. Identify opportunities to use CSS custom properties for repeated values
6. Find color values that differ by less than 5% and could be unified
7. Consolidate media queries by grouping same-breakpoint rules together
8. Merge small single-purpose CSS files into logical module files
9. Extract common patterns into utility classes or mixins
10. Verify the consolidated CSS produces identical rendered output
11. Run visual regression tests if available to catch rendering changes
12. Report: files merged, rules consolidated, size reduction percentage

## Rules

- Never change the visual output; consolidation must be invisible to users
- Preserve CSS specificity order when merging selectors
- Keep CSS module boundaries intact; do not merge across component scopes
- Convert repeated magic numbers to CSS custom properties
- Maintain source maps for debugging after consolidation
- Process one logical group at a time for safe incremental changes
- Test in multiple browsers after consolidation
