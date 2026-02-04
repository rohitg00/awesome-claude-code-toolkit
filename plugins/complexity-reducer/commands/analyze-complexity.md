# /analyze-complexity - Analyze Code Complexity

Calculate cyclomatic complexity and identify overly complex functions.

## Steps

1. Detect the project language to select the appropriate complexity analysis tool
2. Scan all source files excluding tests, vendor, and generated code
3. Calculate cyclomatic complexity for each function and method
4. Calculate cognitive complexity as a secondary metric
5. Identify functions exceeding the threshold (default: cyclomatic > 10)
6. Rank the top 20 most complex functions by complexity score
7. For each complex function, identify the complexity drivers: nested conditionals, switch cases, loops
8. Calculate file-level complexity averages and identify the most complex files
9. Compare against industry benchmarks: low (1-5), moderate (6-10), high (11-20), very high (21+)
10. Generate a formatted report with function name, file, line, complexity score
11. Suggest specific refactoring strategies for the top 5 most complex functions
12. Save the report and track complexity trends over time

## Rules

- Use cyclomatic complexity as the primary metric
- Include cognitive complexity as a complementary measure
- Exclude generated code, migrations, and configuration files
- Threshold of 10 for warnings, 20 for critical flags
- Consider function length alongside complexity (long + complex = priority)
- Do not count simple switch/case with returns as highly complex
- Report both absolute values and percentile rankings
