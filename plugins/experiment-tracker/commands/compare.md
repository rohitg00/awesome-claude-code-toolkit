Compare multiple ML experiment runs side-by-side to identify the best configuration.

## Steps


1. Load experiment records from the tracking store.
2. Select experiments to compare:
3. Build a comparison table:
4. Analyze parameter sensitivity:
5. Generate visualizations:
6. Identify the winning configuration:
7. Recommend next experiments to try.

## Format


```
Comparison: <N> experiments
Best Run: <experiment name>
Key Findings:
  - <parameter X> has <impact> on <metric Y>
```


## Rules

- Only compare experiments with the same dataset version.
- Use consistent metrics across all compared runs.
- Statistical significance matters; do not draw conclusions from single runs.

