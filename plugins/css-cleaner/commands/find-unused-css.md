# /find-unused-css - Find Unused CSS

Identify CSS rules that are not used by any component or page.

## Steps

1. Scan all CSS, SCSS, and styled-component files in the project
2. Extract all CSS selectors: classes, IDs, element selectors, attribute selectors
3. Scan all HTML, JSX, TSX, and template files for referenced CSS classes
4. Check JavaScript files for dynamically applied classes (classList, className)
5. Account for CSS modules by checking module import usage
6. Cross-reference selectors with their usage across all template files
7. Identify selectors with zero references in any template or component
8. Check for CSS custom properties (variables) that are defined but never used
9. Detect duplicate CSS rules with identical properties
10. Calculate unused CSS as a percentage of total CSS
11. Report unused selectors with file path, line number, and selector name
12. Estimate bundle size savings from removing unused CSS

## Rules

- Account for dynamic class generation (template literals, classnames library)
- Do not flag global reset styles or normalize.css as unused
- Check for CSS used in third-party component overrides
- Consider media query variants of the same class
- Exclude CSS-in-JS runtime styles from static analysis
- Flag utility classes only if no utility framework (Tailwind) is configured
- Report confidence level for each unused selector finding
