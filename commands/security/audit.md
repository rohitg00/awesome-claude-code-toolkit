Perform a security audit of the codebase covering common vulnerability categories.

## Steps

### 1. Dependency Vulnerabilities
- Run the package manager's audit: `npm audit`, `pip audit`, `cargo audit`, `govulncheck ./...`.
- List critical and high severity vulnerabilities.
- For each, determine if the vulnerable code path is actually reachable in this project.
- Recommend specific version upgrades or patches.

### 2. Secrets Scan
- Search for hardcoded secrets, API keys, tokens, and passwords:
  - Patterns: `password\s*=`, `api[_-]?key`, `secret`, `token`, `Bearer `, base64-encoded strings.
  - Files: `.env` files committed to git, config files, source code.
- Check `.gitignore` for proper exclusion of sensitive files.
- Verify environment variables are used for all secrets.

### 3. OWASP Top 10 Check
- **Injection**: SQL injection, command injection, XSS. Search for string concatenation in queries, `eval()`, `innerHTML`.
- **Broken Auth**: Weak password policies, missing rate limiting, session fixation.
- **Sensitive Data Exposure**: Unencrypted data at rest/transit, verbose error messages, logs containing PII.
- **Broken Access Control**: Missing authorization checks, IDOR vulnerabilities, privilege escalation paths.
- **Security Misconfiguration**: Default credentials, unnecessary features enabled, CORS wildcards.

### 4. Input Validation
- Verify all user inputs are validated before processing.
- Check for proper type coercion and boundary checking.
- Ensure file uploads have type, size, and name validation.
- Verify URL and redirect validation prevents open redirects.

### 5. Authentication and Authorization Review
- Check password hashing (bcrypt/argon2, not MD5/SHA1).
- Verify JWT token expiration and rotation.
- Check for proper CSRF protection.
- Verify role-based access control at the API layer, not just the UI.

### 6. Report
Produce a findings report organized by severity (Critical, High, Medium, Low, Info) with:
- Finding description.
- Affected file and line.
- Recommended fix.
- Reference (CWE number or OWASP category).

## Rules

- Prioritize findings by exploitability and impact, not just theoretical risk.
- Include proof-of-concept for critical findings when safe to do so.
- Do not just list tools to run. Actually analyze the output and provide actionable recommendations.
- Check both the application code and infrastructure configuration (Dockerfiles, CI configs, cloud configs).
