# /suggest-colors - Suggest Accessible Colors

Suggest alternative colors that meet WCAG contrast requirements.

## Steps

1. Identify the failing color pairs from the contrast audit
2. For each failing pair, determine the target ratio: 4.5:1 (AA normal) or 3:1 (AA large)
3. Calculate the minimum adjustment needed to meet the target ratio
4. Generate color alternatives by adjusting lightness while preserving hue and saturation
5. Provide at least 3 alternative colors for each failing pair
6. Verify each suggestion meets the target contrast ratio
7. Check that suggested colors fit within the project's design system palette
8. Show color swatches (hex codes) with their contrast ratios
9. Suggest pairing options: darkening the foreground vs lightening the background
10. Verify suggested colors also work for color-blind users (deuteranopia, protanopia)
11. Generate a CSS variable override file with the accessible alternatives
12. Present before/after comparison showing the visual difference

## Rules

- Prefer minimal color changes to maintain the design intent
- Suggest colors that stay within the same hue family
- Provide options for both adjusting foreground and background
- Check suggestions against the full color palette for consistency
- Verify suggestions work for all color blindness types
- Do not suggest pure black/white unless the design already uses them
- Include the exact hex/RGB values for easy implementation
