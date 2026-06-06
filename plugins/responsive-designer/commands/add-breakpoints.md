# /add-breakpoints - Add Responsive Breakpoints

Implement responsive design breakpoints for a component or page.

## Steps

1. Identify the target component or page to make responsive
2. Define breakpoints aligned with the design system: mobile (< 640px), tablet (640-1024px), desktop (> 1024px)
3. Analyze the current layout and identify elements that need responsive behavior
4. Implement mobile-first styles as the base layout
5. Add tablet breakpoint styles: adjust grid columns, spacing, font sizes
6. Add desktop breakpoint styles: wider containers, side-by-side layouts
7. Handle images responsively: srcset, sizes, object-fit, aspect-ratio
8. Adjust typography scale across breakpoints for readability
9. Handle navigation: mobile hamburger menu, tablet condensed, desktop full nav
10. Test touch targets: minimum 44x44px on mobile devices
11. Add container queries for component-level responsiveness if supported
12. Verify layout at all breakpoints and in-between sizes

## Rules

- Always design mobile-first and add complexity for larger screens
- Use relative units (rem, em, %) instead of fixed pixels for layout
- Minimum touch target size of 44x44px on mobile
- Do not hide critical content at any breakpoint; rearrange instead
- Test at exact breakpoint boundaries and between breakpoints
- Use CSS Grid or Flexbox for responsive layouts, not floats
- Ensure text remains readable (16px minimum) at all breakpoints
