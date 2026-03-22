Scan web application components for accessibility violations against WCAG guidelines.

## Steps

1. Identify the target: component file, page, or entire project.
2. Scan for common WCAG 2.1 violations:
   - **Perceivable**: Images without alt text, videos without captions, low color contrast.
   - **Operable**: Non-keyboard-accessible elements, missing focus indicators, no skip links.
   - **Understandable**: Missing form labels, no error descriptions, inconsistent navigation.
   - **Robust**: Invalid HTML, missing ARIA roles, incorrect heading hierarchy.
3. Check component-level issues:
   - Interactive elements (buttons, links) without accessible names.
   - Custom components missing ARIA roles and states.
   - Dynamic content updates without live region announcements.
   - Modal dialogs without focus trapping.
4. Check form accessibility:
   - Labels associated with inputs via `htmlFor`/`id` or wrapping.
   - Error messages linked to inputs via `aria-describedby`.
   - Required fields marked with `aria-required`.
5. Classify findings by WCAG level (A, AA, AAA) and severity.
6. Provide specific fix instructions for each violation.

## Format

```
Accessibility Scan: <scope>

Violations: <N> (A: <n>, AA: <n>, AAA: <n>)

WCAG A (must fix):
  - <file>:<line> - <element> missing alt text (1.1.1)
  - <file>:<line> - <element> not keyboard accessible (2.1.1)

WCAG AA (should fix):
  - <file>:<line> - contrast ratio 3.2:1, needs 4.5:1 (1.4.3)

Passing:
  - Heading hierarchy is correct
  - Language attribute is set
```

## Rules

- Prioritize WCAG A violations (legal compliance baseline).
- Provide the specific WCAG criterion number for each violation.
- Include fix code snippets, not just descriptions.
- Check both static HTML/JSX and dynamically generated content.
- Test with screen reader considerations (not just automated rules).
