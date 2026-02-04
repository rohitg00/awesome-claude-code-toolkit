# /test-responsive - Test Responsive Design

Test responsive design across multiple device sizes and orientations.

## Steps

1. Define the test device matrix: iPhone SE, iPhone 14, iPad, Android, Desktop
2. Start the application or component preview server
3. Capture screenshots at each device viewport size
4. Check for layout issues: overflow, overlapping elements, cut-off content
5. Verify touch targets are appropriately sized on mobile viewports
6. Test landscape orientation for tablet and mobile views
7. Verify font sizes are readable at each breakpoint
8. Check that images scale properly without distortion or cropping
9. Test interactive elements: dropdowns, modals, tooltips at each size
10. Verify scroll behavior: no horizontal scroll, proper sticky elements
11. Generate a comparison grid showing the layout at each breakpoint
12. Report all issues found with viewport size, element, and description

## Rules

- Test at standard device widths: 375, 390, 414, 640, 768, 1024, 1280, 1440, 1920
- Always test both portrait and landscape on mobile and tablet
- Check for horizontal overflow that causes unwanted horizontal scrolling
- Verify no content is hidden or inaccessible at any viewport size
- Test with browser zoom at 200% for accessibility compliance
- Check that fixed and sticky elements do not overlap content on small screens
- Test with actual device emulation, not just resized browser windows
