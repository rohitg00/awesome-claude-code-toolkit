# /browserbase:capture-design

Capture screenshots of a website and generate a modular `design.md` file that documents the full visual design language as a reusable scaffold.

## Input

Either:
- A **direct URL** — e.g. `https://stripe.com`
- A **search query** — e.g. "best SaaS landing page 2024" — the tool will Google it, pick the top result, and screenshot that

## Process

1. **Resolve the target**
   - If the user gave a URL, use it directly.
   - If the user gave a search query, use Stagehand to:
     a. Navigate to `https://www.google.com/search?q=<query>`
     b. Extract the first organic result URL via `page.extract()`
     c. Navigate to that URL
   - Confirm the final URL with the user before proceeding.

2. **Capture screenshots** — take all of these in a single browser session:
   | Screenshot | Settings |
   |-----------|----------|
   | Full page (desktop) | `1440×900` viewport, `fullPage: true` |
   | Above the fold (desktop) | `1440×900` viewport, `fullPage: false` |
   | Mobile | `390×844` viewport (iPhone 14), `fullPage: true` |
   | Key sections | Scroll to each major section, screenshot individually |

   Save all screenshots to `.browserbase/design-captures/<domain>-<timestamp>/`.

3. **Analyze the design** — using the screenshots AND the live DOM, extract:

   ### Colors
   - Primary, secondary, accent colors (hex)
   - Background colors (light/dark surfaces)
   - Text colors (heading, body, muted)
   - Semantic colors (success, warning, error, info)
   - Gradient definitions if present

   ### Typography
   - Font families (display, body, mono) — identify the actual fonts via CSS inspection
   - Type scale (h1–h6, body, caption, overline sizes)
   - Font weights used
   - Line heights and letter spacing
   - Text alignment patterns

   ### Spacing
   - Base spacing unit (4px, 8px, etc.)
   - Section padding
   - Component internal padding
   - Gap patterns between elements

   ### Layout
   - Max content width
   - Grid system (columns, gutters)
   - Breakpoints observed
   - Common layout patterns (hero, feature grid, CTA band, footer)

   ### Components
   - Buttons (primary, secondary, ghost — border radius, padding, font)
   - Cards (shadow, radius, padding, border)
   - Navigation (type, sticky behavior, hamburger breakpoint)
   - Forms (input style, label position, focus state)
   - Any distinctive components (pricing tables, testimonials, etc.)

   ### Effects
   - Box shadows (elevation levels)
   - Border radii (small, medium, large, pill)
   - Transitions/animations observed
   - Backdrop blur, overlays, gradients

4. **Generate `design.md`** — write the scaffold file following the template below.

5. **Report to user** — show the screenshot paths, the generated file path, and a summary of what was captured.

## Output Template

The generated `design.md` must follow this exact modular structure:

```markdown
# Design Language — [Site Name]
> Captured from [URL] on [date]

## Color Palette

| Role | Hex | Usage |
|------|-----|-------|
| Primary | #XXXXXX | CTAs, links, key UI elements |
| Secondary | #XXXXXX | Supporting elements |
| ... | ... | ... |

### CSS Custom Properties
\`\`\`css
:root {
  --color-primary: #XXXXXX;
  --color-secondary: #XXXXXX;
  /* ... */
}
\`\`\`

## Typography

| Role | Family | Size | Weight | Line Height |
|------|--------|------|--------|-------------|
| Display | ... | ... | ... | ... |
| Heading 1 | ... | ... | ... | ... |
| Body | ... | ... | ... | ... |

### CSS Custom Properties
\`\`\`css
:root {
  --font-display: '...', sans-serif;
  --font-body: '...', sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  /* ... */
}
\`\`\`

## Spacing System

| Token | Value | Usage |
|-------|-------|-------|
| --space-1 | 4px | Tight gaps |
| --space-2 | 8px | Default gap |
| ... | ... | ... |

## Layout

- **Max width**: ...
- **Grid**: ...
- **Breakpoints**: sm: ..., md: ..., lg: ..., xl: ...

## Components

### Buttons
\`\`\`css
.btn-primary { /* ... */ }
.btn-secondary { /* ... */ }
\`\`\`

### Cards
\`\`\`css
.card { /* ... */ }
\`\`\`

### Navigation
\`\`\`css
.nav { /* ... */ }
\`\`\`

(... more components as discovered ...)

## Effects

### Shadows
\`\`\`css
--shadow-sm: ...;
--shadow-md: ...;
--shadow-lg: ...;
\`\`\`

### Border Radii
\`\`\`css
--radius-sm: ...;
--radius-md: ...;
--radius-lg: ...;
--radius-full: 9999px;
\`\`\`

## Page Sections

| Section | Layout | Key Components |
|---------|--------|---------------|
| Hero | ... | ... |
| Features | ... | ... |
| CTA | ... | ... |
| Footer | ... | ... |

## Screenshots

- Desktop full: `[path]`
- Desktop fold: `[path]`
- Mobile full: `[path]`
- Sections: `[paths]`
```

## Rules

- Always use `env: "BROWSERBASE"` — never headless local.
- Save screenshots to `.browserbase/design-captures/` with domain + timestamp subdir.
- Extract colors from actual computed CSS, not just guessing from screenshots.
- Use `page.evaluate()` to inspect `getComputedStyle()` on real DOM elements for accurate values.
- Identify fonts by reading `font-family` from computed styles, not by guessing.
- The generated `design.md` must be copy-pasteable into any project as a design system reference.
- Every CSS value must be a real extracted value, never a placeholder.
- If Google search is used, always confirm the chosen URL before screenshotting.
