Implement data anonymization and pseudonymization for PII protection.

## Steps


1. Identify data that needs anonymization:
2. Choose the anonymization technique:
3. Implement anonymization:
4. Build the anonymization pipeline:
5. Verify anonymization:
6. Automate the pipeline for recurring use.

## Format


```
Anonymization: <dataset or table>
Technique: <masking|pseudonymization|generalization>
Fields Processed:
  - <field>: <technique applied> (<example>)
```


## Rules

- Never use production data in development without anonymization.
- Pseudonymized data must not be reversible without the key.
- Maintain referential integrity across related tables.

