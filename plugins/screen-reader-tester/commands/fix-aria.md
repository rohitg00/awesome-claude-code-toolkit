# /fix-aria - Fix ARIA Attributes

Fix incorrect or missing ARIA attributes for accessibility compliance.

## Steps

1. Scan all HTML/JSX/TSX files for ARIA attribute usage
2. Identify missing ARIA attributes on custom interactive components
3. Detect incorrect ARIA role assignments (role on wrong element type)
4. Find ARIA attributes that reference non-existent IDs (aria-labelledby, aria-describedby)
5. Check for redundant ARIA that duplicates native HTML semantics
6. Verify required ARIA properties are present for each role (e.g., tabpanel needs aria-labelledby)
7. Fix missing accessible names: add aria-label or aria-labelledby
8. Add aria-live regions for dynamic content that updates without page reload
9. Fix aria-expanded, aria-selected, and aria-checked states on interactive elements
10. Add aria-hidden="true" to decorative elements and icons
11. Verify all fixes do not break the visual layout or functionality
12. Run the accessibility audit again to confirm fixes resolve the findings

## Rules

- Use native HTML elements over ARIA when possible (button over div role="button")
- Do not add ARIA attributes that contradict the native element semantics
- Every interactive element must have an accessible name
- ARIA IDs must be unique within the document
- Remove aria-hidden from elements that contain focusable children
- Use aria-describedby for supplementary information, not the primary label
- Test fixes with a screen reader to verify they produce correct announcements
