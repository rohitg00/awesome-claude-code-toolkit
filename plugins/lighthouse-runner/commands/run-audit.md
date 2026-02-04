# /run-audit - Run Lighthouse Audit

Execute a Lighthouse performance audit on web pages.

## Steps

1. Ask the user for the target URL or list of URLs to audit
2. Determine the audit categories: Performance, Accessibility, Best Practices, SEO, PWA
3. Configure Lighthouse settings: device type (mobile/desktop), throttling, viewport
4. Run Lighthouse audit for each target URL
5. Parse the results: overall scores and individual metric values
6. Extract Core Web Vitals: LCP, FID/INP, CLS with pass/fail status
7. List all failing audits grouped by category with their impact level
8. Identify the top 5 performance opportunities with estimated savings
9. Extract diagnostic information: main thread blocking time, resource counts
10. Compare scores against targets: green (90+), orange (50-89), red (0-49)
11. Save the full HTML report and JSON results to the reports directory
12. Present a summary dashboard with scores and key recommendations

## Rules

- Default to mobile device emulation as it is the stricter test
- Run audits at least 3 times and use median scores to reduce variability
- Focus on Core Web Vitals as they directly impact search ranking
- Do not audit localhost unless the user explicitly requests it
- Include the Lighthouse version in the report for reproducibility
- Compare against previous audit results when available
- Flag any score drop of more than 5 points as a regression
