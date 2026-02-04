# /fix-issues - Fix Lighthouse Issues

Apply fixes for Lighthouse audit failures to improve scores.

## Steps

1. Load the most recent Lighthouse audit results
2. Prioritize issues by impact: high-impact, medium-impact, low-impact
3. For Performance issues:
   - Add lazy loading to below-the-fold images
   - Optimize image formats and sizes (WebP, AVIF)
   - Add preload hints for critical resources
   - Defer non-critical JavaScript and CSS
4. For Accessibility issues:
   - Add missing alt text to images
   - Fix color contrast ratios
   - Add ARIA labels to interactive elements
   - Ensure proper heading hierarchy
5. For Best Practices issues:
   - Fix mixed content (HTTP resources on HTTPS pages)
   - Add security headers (CSP, X-Frame-Options)
   - Update deprecated APIs
6. For SEO issues:
   - Add missing meta descriptions and titles
   - Fix mobile viewport configuration
   - Add structured data markup
7. Apply each fix incrementally and verify it resolves the flagged audit
8. Re-run Lighthouse to measure the improvement
9. Report: fixes applied, score changes, remaining issues

## Rules

- Fix high-impact issues first for maximum score improvement
- Do not break existing functionality while fixing audit issues
- Test visual appearance after applying performance optimizations
- Verify accessibility fixes with manual keyboard navigation
- Keep performance optimizations progressive (do not block rendering)
- Document each fix for team awareness and future maintenance
