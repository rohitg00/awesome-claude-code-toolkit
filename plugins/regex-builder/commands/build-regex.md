# /build-regex - Build Regular Expression

Build a regular expression pattern from a natural language description.

## Steps

1. Ask the user to describe the pattern they want to match in plain language
2. Identify the key components: literal strings, character classes, repetition, groups
3. Determine the regex flavor: JavaScript, Python, Go, Java, PCRE
4. Build the regex pattern incrementally, starting with the simplest matching version
5. Add anchors (^, $) if the pattern should match the entire string
6. Use named capture groups for extracting specific parts
7. Add quantifiers: exact counts, ranges, greedy vs lazy matching
8. Handle edge cases: optional parts, alternatives, escaped special characters
9. Add lookahead/lookbehind assertions if needed for context-dependent matching
10. Optimize the regex for performance: avoid catastrophic backtracking
11. Provide a plain-English explanation of what the regex matches
12. Show the regex with inline comments explaining each part

## Rules

- Start with the simplest pattern that works and add complexity only as needed
- Use non-capturing groups (?:) unless capture is explicitly needed
- Prefer character classes [a-z] over alternation (a|b|c) for single characters
- Avoid nested quantifiers that can cause catastrophic backtracking
- Use named groups for clarity in complex patterns
- Test the regex against edge cases including empty strings
- Provide the pattern in the correct syntax for the target language
