# /compare-models - Compare ML Models

Compare multiple ML models to select the best performer.

## Steps

1. Ask the user for the models to compare and the evaluation dataset
2. Load all models and verify they accept the same input format
3. Run inference with each model on the identical test dataset
4. Calculate the same metrics for all models for fair comparison
5. Create a side-by-side comparison table with all metrics
6. Perform statistical significance testing between model pairs (McNemar, paired t-test)
7. Compare inference performance: latency, throughput, memory footprint
8. Calculate the cost-performance trade-off: accuracy vs compute cost
9. Identify which model performs best on specific data subsets
10. Evaluate robustness: test with noisy or adversarial inputs
11. Create a recommendation based on the use case priorities (accuracy vs speed vs cost)
12. Generate a comparison report with tables, rankings, and the recommended model

## Rules

- Use the exact same test data and preprocessing for all models
- Apply statistical significance tests; do not rely on point estimates alone
- Consider practical significance, not just statistical significance
- Include model size and inference cost in the comparison
- Test edge cases that differentiate the models
- Report the evaluation methodology for reproducibility
- Consider deployment constraints (model size, latency requirements) in recommendations
