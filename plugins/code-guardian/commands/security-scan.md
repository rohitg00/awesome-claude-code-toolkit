# /code-guardian:security-scan

Perform a security-focused scan of the codebase targeting OWASP Top 10 and common vulnerability patterns.

## Process

1. Determine the scan scope:
   - Default: scan the entire project from the repository root
   - If an argument is provided, limit scanning to that path
   - Identify the primary language(s) and framework(s) by checking package.json, requirements.txt, go.mod, Cargo.toml, etc.

2. Scan for each vulnerability category:

### A01: Broken Access Control
- Search for endpoints missing authentication middleware
- Check for direct object reference patterns where user IDs from request params access resources without ownership verification
- Look for missing CORS configuration or overly permissive origins (`*`)
- Find routes that expose admin functionality without role checks

### A02: Cryptographic Failures
- Grep for weak hashing algorithms: MD5, SHA1 used for passwords or tokens
- Check for hardcoded encryption keys, salts, or initialization vectors
- Look for HTTP URLs where HTTPS should be used (API calls, webhooks)
- Verify that sensitive data in logs is masked or redacted

### A03: Injection
- Search for string concatenation or template literals in SQL queries
- Check for unsanitized input in shell exec, spawn, or system calls
- Look for innerHTML assignments, dangerouslySetInnerHTML without sanitization
- Find regex patterns vulnerable to ReDoS (catastrophic backtracking)

### A04: Insecure Design
- Check for missing rate limiting on authentication endpoints
- Look for predictable resource IDs (sequential integers for sensitive resources)
- Verify that file uploads validate type, size, and content
- Check for missing CSRF protection on state-changing requests

### A05: Security Misconfiguration
- Search for debug mode enabled in production configs
- Check for default credentials in config files or environment examples
- Look for overly verbose error messages that leak stack traces
- Verify security headers (CSP, X-Frame-Options, HSTS) in server config

### A06: Vulnerable Components
- If package-lock.json or yarn.lock exists, note that `npm audit` should be run
- Check for pinned versions of known-vulnerable packages
- Look for abandoned dependencies (check last publish date patterns in comments)

### A07: Authentication Failures
- Check JWT implementation: algorithm confusion, missing expiry, weak secrets
- Look for session tokens in URLs or local storage instead of httpOnly cookies
- Find password handling without proper hashing (bcrypt/argon2)
- Check for missing account lockout after failed attempts

### A08: Data Integrity Failures
- Look for deserialization of untrusted data (pickle, yaml.load, JSON.parse of user input into eval)
- Check for missing integrity verification on downloaded artifacts
- Find CI/CD configs that pull unverified external actions or images

### A09: Logging Failures
- Check if authentication events (login, logout, failure) are logged
- Verify that sensitive data (passwords, tokens, PII) is not written to logs
- Look for missing request ID correlation in log entries

### A10: SSRF
- Search for user-controlled URLs passed to HTTP clients or fetch calls
- Check for URL validation that only checks the scheme but not the host
- Look for internal service URLs constructable from user input

3. Additionally scan for:
   - `.env` files committed to the repository
   - Private keys (RSA, SSH, PGP) in the source tree
   - AWS access keys, GCP service account JSON, Azure connection strings
   - Patterns matching API keys: long alphanumeric strings in source code near keywords like `key`, `token`, `secret`

## Output Format

Group findings by OWASP category. For each finding provide:
- Severity (Critical / High / Medium / Low)
- File path and line number
- Description of the vulnerability
- Recommended remediation

## Rules

- Minimize false positives: only flag patterns with clear security implications
- Prioritize findings that are exploitable in production
- Do not flag test files unless they contain real credentials
- Suggest specific fixes, not just "sanitize input"
- End with a security posture summary and top 3 priority actions
