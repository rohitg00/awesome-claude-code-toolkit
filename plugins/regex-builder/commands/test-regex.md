# /test-regex - Test Regular Expression

Test a regular expression against sample inputs and edge cases.

## Steps

1. Take the regex pattern from the user or the most recently built pattern
2. Ask for test strings or generate common test cases based on the pattern
3. Run the regex against each test string and report: match (yes/no), matched text, groups
4. Test with edge cases: empty string, very long string, special characters
5. Test with strings that should NOT match to verify specificity
6. Show captured groups for each matching test case
7. Measure the regex execution time with long input strings to check performance
8. Test for catastrophic backtracking by providing adversarial inputs
9. Compare the pattern behavior across regex flavors if relevant
10. Suggest improvements if false positives or false negatives are found
11. Generate a test table: input, expected, actual, match, captured groups
12. Report overall accuracy: true positives, true negatives, false positives, false negatives

## Rules

- Always test with both matching and non-matching inputs
- Include boundary cases: start of string, end of string, empty input
- Test with Unicode characters if the pattern handles international text
- Check for unintended partial matches (missing anchors)
- Time the regex with at least 1000-character inputs to detect performance issues
- Test captured groups individually, not just the overall match
- Report the regex flavor being tested for accurate results
