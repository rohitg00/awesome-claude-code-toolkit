# /mutate - Run Mutation Testing

Run mutation testing to evaluate test suite effectiveness.

## Steps

1. Detect the project language and testing framework from configuration files
2. Check if a mutation testing tool is installed (Stryker for JS/TS, mutmut for Python, PITest for Java)
3. If not installed, provide installation instructions for the appropriate tool
4. Identify the source files and their corresponding test files
5. Configure mutation operators: arithmetic, conditional, string, return value mutations
6. Run the mutation testing tool on the target source files
7. Monitor progress: total mutants generated, killed, survived, timed out
8. Calculate the mutation score (killed / total * 100)
9. List survived mutants with file location, line number, and mutation description
10. For each survived mutant, identify which test should have caught it
11. Suggest specific test cases to write for the top 10 survived mutants
12. Save the mutation report to the reports directory

## Rules

- Start with a single file or module to keep execution time reasonable
- Set a timeout per mutant of 10x the normal test execution time
- Exclude test files, configuration files, and generated code from mutation
- A mutation score below 80% indicates weak test coverage
- Focus on survived mutants in critical business logic first
- Do not count equivalent mutants (mutations that produce identical behavior)
- Report execution time and mutant count for performance tracking
