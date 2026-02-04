# /code-guardian:review

Perform a thorough code review of the current uncommitted changes or a specified file/directory.

## Process

1. Gather the changes to review:
   - Run `git diff` for unstaged changes and `git diff --cached` for staged changes
   - If a specific file or directory is provided as an argument, focus the review there
   - If no changes exist, review the most recent commit with `git diff HEAD~1`

2. Analyze each changed file across these dimensions:

### Correctness
- Logic errors, off-by-one mistakes, incorrect boolean conditions
- Unhandled null/undefined values and missing error boundaries
- Race conditions in async code, missing awaits, unhandled promise rejections
- Incorrect type assertions or unsafe casts

### Security
- User input flowing to SQL queries, shell commands, or file paths without sanitization
- Hardcoded credentials, API keys, tokens, or connection strings
- Missing authentication or authorization checks on new endpoints
- Unsafe deserialization of external data

### Performance
- N+1 query patterns in database access
- Unnecessary re-renders in React components (missing memoization, unstable references)
- Unbounded data fetching without pagination or limits
- Synchronous blocking operations on hot paths
- Memory leaks from unclosed resources, event listeners, or subscriptions

### Design
- Single Responsibility violations: functions or classes doing too many things
- Tight coupling between modules that should be independent
- Missing abstractions where patterns repeat three or more times
- Public API surface area: are new exports intentional and well-designed?

### Readability
- Variable and function names that obscure intent
- Deeply nested conditionals that should be flattened or extracted
- Magic numbers or strings that should be named constants
- Missing or misleading type annotations

3. Classify each finding by severity:
   - **CRITICAL** - Will cause bugs, data loss, or security vulnerabilities in production
   - **WARNING** - Likely to cause issues under certain conditions or during maintenance
   - **SUGGESTION** - Improvement opportunity that is not urgent

4. For each finding, provide:
   - The file path and line range
   - A clear description of the issue
   - A concrete fix or code suggestion

## Output Format

Present findings grouped by severity, then by file. Lead with critical issues.
Skip categories that have no findings. End with a brief summary of overall quality.

## Rules

- Be specific and actionable, not vague ("this could be improved")
- Do not flag style preferences unless they impact readability significantly
- Acknowledge well-written code briefly at the end
- Limit total findings to the 15 most impactful to avoid noise
- If the diff is very large, prioritize new code over modified code
