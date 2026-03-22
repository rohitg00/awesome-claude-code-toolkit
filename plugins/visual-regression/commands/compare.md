# /compare - Compare Visual Screenshots

Compare current screenshots against baselines to detect visual regressions.

## Steps

1. Verify that baseline screenshots exist in the baselines directory
2. Capture current screenshots using the same configuration as baselines
3. Match current screenshots to their corresponding baselines by name
4. Perform pixel-by-pixel comparison using a diff threshold (default 0.1%)
5. Generate diff images highlighting changed regions in red
6. Calculate the percentage of pixels that differ for each comparison
7. Classify results: pass (below threshold), warn (near threshold), fail (above threshold)
8. Present a summary table: page, viewport, diff percentage, status
9. For failures, display the baseline, current, and diff images side by side
10. Ask the user whether to update baselines for intentional changes
11. Save comparison report with all results and diff images

## Rules

- Use an anti-aliasing tolerance to avoid false positives from font rendering
- Default diff threshold is 0.1%; allow user to configure per-component
- Always generate diff images for failed comparisons
- Do not auto-update baselines without user confirmation
- Exclude known dynamic areas from comparison using ignore regions
- Report the total number of new pages without baselines
- Clean up temporary screenshot files after comparison
