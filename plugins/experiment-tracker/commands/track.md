Track an ML experiment by logging parameters, metrics, and artifacts for comparison.

## Steps


1. Define the experiment metadata:
2. Log hyperparameters:
3. Log metrics during and after training:
4. Save artifacts:
5. Record environment details:
6. Tag the experiment with status (running, completed, failed).
7. Store results in a structured format for later comparison.

## Format


```
Experiment: <name>
Date: <timestamp>
Hypothesis: <what is being tested>
Params: { learning_rate: X, batch_size: Y, ... }
```


## Rules

- Always log random seeds for reproducibility.
- Record the exact dataset version used.
- Never overwrite previous experiment results.

