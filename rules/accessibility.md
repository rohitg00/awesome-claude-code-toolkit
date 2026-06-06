# Accessibility

## WCAG 2.2 Compliance
- Target WCAG 2.2 Level AA for all user-facing features.
- Test with at least two screen readers (NVDA + VoiceOver or JAWS).
- Run automated accessibility checks (axe-core, Lighthouse) in CI.
- Conduct manual keyboard-only testing for all interactive flows.

## Semantic HTML
- Use correct heading hierarchy: one `<h1>` per page, sequential `<h2>`-`<h6>`.
- Use `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>` for page landmarks.
- Use `<button>` for actions, `<a>` for navigation. Never use `<div>` with `onClick` for either.
- Use `<ul>`/`<ol>` for lists, `<table>` for tabular data with `<thead>`, `<th>`, and `scope`.
- Use `<form>`, `<label>`, `<fieldset>`, and `<legend>` for form structures.

## ARIA
- Prefer native HTML elements over ARIA attributes. ARIA is a last resort.
- Every ARIA role must have the required properties (e.g., `role="slider"` needs `aria-valuemin`, `aria-valuemax`, `aria-valuenow`).
- Use `aria-label` or `aria-labelledby` on elements without visible text labels.
- Use `aria-live="polite"` for dynamic content updates (toasts, search results, status messages).
- Use `aria-expanded`, `aria-controls`, and `aria-haspopup` for interactive disclosure widgets.
- Never use `aria-hidden="true"` on focusable elements.

## Keyboard Navigation
- All interactive elements must be reachable via Tab key in logical order.
- Provide visible focus indicators with a minimum 3:1 contrast ratio.
- Support Escape to close modals, dropdowns, and overlays.
- Trap focus within modal dialogs. Restore focus to trigger element on close.
- Implement arrow key navigation for menus, tabs, and listboxes.

## Visual Design
- Minimum color contrast: 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold).
- Do not convey information through color alone. Use text labels, icons, or patterns.
- Support `prefers-reduced-motion` to disable or reduce animations.
- Support `prefers-color-scheme` for dark mode compatibility.
- Minimum touch target size: 44x44 CSS pixels for mobile interfaces.

## Media
- Provide `alt` text for all images. Use empty `alt=""` for decorative images.
- Provide captions for video content and transcripts for audio content.
- Do not auto-play audio or video. If unavoidable, provide a pause control within the first 3 seconds.
