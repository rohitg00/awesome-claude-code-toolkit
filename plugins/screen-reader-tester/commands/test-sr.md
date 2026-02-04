# /test-sr - Test Screen Reader Compatibility

Test application compatibility with screen readers.

## Steps

1. Identify the pages or components to test for screen reader compatibility
2. Analyze the HTML structure for semantic markup: headings, landmarks, lists, tables
3. Verify all interactive elements have accessible names (label, aria-label, aria-labelledby)
4. Check that images have meaningful alt text (or empty alt for decorative images)
5. Verify form inputs are associated with labels using for/id or aria-labelledby
6. Test dynamic content updates with aria-live regions and status messages
7. Verify modal dialogs trap focus and announce their purpose
8. Check that custom components expose the correct ARIA roles and states
9. Test page navigation: landmarks are present and properly labeled
10. Verify data tables have proper header associations (th, scope, headers)
11. Generate a reading order analysis showing how content will be announced
12. Report issues with element, expected announcement, and actual markup

## Rules

- Test with at least two screen readers if possible (VoiceOver + NVDA/JAWS)
- Verify the reading order matches the visual layout order
- Check that off-screen content is properly hidden from screen readers (aria-hidden)
- Ensure all state changes are announced (expanded/collapsed, selected, checked)
- Verify error messages are associated with their form fields
- Test single-page app navigation: page title updates, focus management
- Do not use role="presentation" on elements that convey meaningful content
