# /analyze-bundle - Analyze Frontend Bundle

Analyze JavaScript bundle size and identify optimization opportunities.

## Steps

1. Detect the build tool: webpack, Vite, Rollup, esbuild, or Parcel
2. Run a production build with bundle analysis enabled
3. Parse the bundle stats to identify all chunks and their sizes
4. List the top 20 largest modules by gzipped size
5. Identify duplicate packages included multiple times in the bundle
6. Detect packages that could be replaced with smaller alternatives
7. Calculate the total bundle size: raw, minified, and gzipped
8. Break down the bundle by category: app code, node_modules, assets
9. Check for source maps leaking to production builds
10. Identify dynamic import opportunities for code splitting
11. Compare against performance budgets if configured
12. Generate a report with size breakdown, duplicates, and recommendations

## Rules

- Always report gzipped sizes as that reflects actual transfer size
- Flag any single chunk larger than 250KB gzipped as a concern
- Identify tree-shaking failures (importing entire libraries for one function)
- Check for development-only code included in production builds
- Compare against the previous build if stats are available
- Suggest specific alternatives for oversized dependencies
- Do not suggest removing dependencies without checking usage
