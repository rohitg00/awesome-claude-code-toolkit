# /evaluate-model - Evaluate ML Model

Evaluate machine learning model performance with comprehensive metrics.

## Steps

1. Ask the user for the model type: classification, regression, NLP, or generative
2. Load the model and test dataset from the specified paths
3. Run inference on the entire test dataset and collect predictions
4. For classification models, calculate: accuracy, precision, recall, F1-score, AUC-ROC
5. For regression models, calculate: MAE, MSE, RMSE, R-squared, MAPE
6. For NLP models, calculate: BLEU, ROUGE, perplexity, exact match
7. Generate a confusion matrix for classification tasks
8. Identify the worst-performing classes or data segments
9. Calculate calibration metrics: expected calibration error
10. Run performance profiling: inference time per sample, memory usage, throughput
11. Check for bias: evaluate performance across demographic subgroups if applicable
12. Generate a comprehensive evaluation report with all metrics and visualizations

## Rules

- Use stratified sampling if the test set is imbalanced
- Report confidence intervals for all metrics when sample size allows
- Include both micro and macro averages for multi-class metrics
- Test on held-out data never seen during training
- Report inference latency percentiles (p50, p95, p99) not just averages
- Check for data leakage between train and test sets
- Include baseline comparisons (random, majority class, previous model version)
