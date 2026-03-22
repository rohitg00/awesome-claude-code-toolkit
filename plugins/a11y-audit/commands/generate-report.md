# /generate-report - Generate Accessibility Report

Generate a detailed accessibility audit report with remediation steps.

## Steps

1. Compile all findings from the accessibility audit
2. Organize findings by WCAG principle: Perceivable, Operable, Understandable, Robust
3. Assign severity levels: critical, serious, moderate, minor
4. For each finding, include: WCAG criterion, element, issue description, impact
5. Add code snippets showing the current problematic markup
6. Provide remediation code showing the corrected markup for each issue
7. Calculate a WCAG compliance score based on pass/fail criteria
8. Generate an executive summary with total issues by severity
9. Create a remediation priority matrix: effort vs impact
10. Include before/after examples for the most common issues
11. Add references to WCAG understanding documents for each criterion
12. Save the report in markdown and HTML formats

## Rules

- Group similar issues together to reduce repetitive findings
- Include the user impact description for each issue (who is affected and how)
- Provide specific code fixes, not just descriptions of what to change
- Reference the WCAG success criterion number and name for each finding
- Include both automated and manual testing results
- Add estimated remediation effort for each issue (quick fix, moderate, significant)
- Track compliance percentage against the target WCAG level
