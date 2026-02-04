# /capture-baseline - Capture Visual Baseline

Capture baseline screenshots for visual regression testing.

## Steps

1. Identify the pages or components to capture baselines for
2. Check if a visual testing tool is configured (Percy, Chromatic, reg-suit, or Playwright)
3. Determine viewport sizes for captures: mobile (375px), tablet (768px), desktop (1280px)
4. Start the application or Storybook server if needed
5. Navigate to each target page and wait for all assets to load
6. Remove dynamic content (timestamps, ads, animations) using CSS injection or masking
7. Capture full-page screenshots at each viewport size
8. Save screenshots to the baselines directory with descriptive naming: `{page}-{viewport}-baseline.png`
9. Generate a manifest file listing all captured baselines with timestamps
10. Report total baselines captured, file sizes, and storage location
11. Commit baseline images to the repository or upload to cloud storage

## Rules

- Always capture at minimum three viewport sizes (mobile, tablet, desktop)
- Wait for network idle before capturing to avoid incomplete renders
- Mask or hide dynamic content that changes between runs
- Use consistent browser and device emulation settings
- Name baselines clearly with page name and viewport size
- Store baselines in a dedicated directory separate from test code
- Compress images to keep repository size manageable
