# /run-audit - Run Accessibility Audit

Execute a comprehensive accessibility audit against WCAG guidelines.

## Steps

1. Ask the user for the target URL or component to audit
2. Configure the audit scope: WCAG 2.1 Level A, AA, or AAA
3. Run automated accessibility scanning using axe-core or similar engine
4. Check all WCAG success criteria applicable to the content type
5. Test keyboard navigation: all interactive elements reachable and operable
6. Verify focus management: visible focus indicators, logical focus order
7. Check ARIA usage: proper roles, states, properties, and landmark regions
8. Validate heading hierarchy: logical order without skipping levels
9. Test color contrast ratios: 4.5:1 for normal text, 3:1 for large text
10. Check form accessibility: labels, error messages, required field indicators
11. Verify media accessibility: alt text, captions, audio descriptions
12. Compile findings into a prioritized report by impact level

## Rules

- Test against WCAG 2.1 AA as the minimum standard
- Automated tools catch about 30% of issues; note that manual testing is also needed
- Prioritize issues by user impact: critical (blocks access), serious, moderate, minor
- Include WCAG success criterion reference for each finding
- Test with actual assistive technology when possible (VoiceOver, NVDA)
- Do not flag decorative images that correctly have empty alt attributes
- Include remediation guidance with each finding
