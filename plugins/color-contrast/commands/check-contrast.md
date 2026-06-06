# /check-contrast - Check Color Contrast

Check color contrast ratios against WCAG accessibility requirements.

## Steps

1. Scan CSS, SCSS, and styled-components for all text color and background color pairs
2. Resolve CSS custom properties and theme variables to actual color values
3. Calculate the luminance contrast ratio for each foreground/background pair
4. Check against WCAG 2.1 requirements: 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold)
5. Check non-text contrast for UI components and graphical objects: 3:1 ratio
6. Identify text on images or gradients that may have insufficient contrast
7. Check focus indicator contrast against adjacent colors
8. Verify contrast in both light and dark themes if the app supports them
9. Flag transparent or semi-transparent colors that reduce effective contrast
10. Generate a report: element, foreground color, background color, ratio, pass/fail
11. Show the total pass/fail count and compliance percentage
12. Highlight the worst offenders that need immediate attention

## Rules

- Test both light and dark mode color schemes
- Account for opacity when calculating effective contrast
- Large text threshold: 18px regular or 14px bold
- Do not flag disabled elements as they are exempt from contrast requirements
- Check placeholder text contrast (should meet 4.5:1 even though many sites skip this)
- Consider adjacent color contrast for interactive component boundaries
- Report all unique color pairs, not every instance
