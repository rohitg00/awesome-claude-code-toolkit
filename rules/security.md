# Security Rules

## Secrets Management
- Never hardcode secrets, API keys, tokens, or passwords in source code.
- Use environment variables or a secrets manager (AWS Secrets Manager, Vault, Doppler).
- Add `.env`, `.env.local`, and credential files to `.gitignore`.
- Rotate secrets immediately if they are accidentally committed.
- Use different secrets for development, staging, and production.

## Input Validation
- Validate all external inputs at the system boundary (API endpoints, CLI args, file uploads).
- Use schema validation libraries (Zod, Joi, Pydantic) rather than manual checks.
- Reject invalid input early. Do not try to sanitize and proceed.
- Enforce length limits, type constraints, and allowed character sets.
- Validate file uploads: type, size, filename, and content.

## Output Encoding
- Escape user-provided data before rendering in HTML, SQL, shell, or logs.
- Use parameterized queries for all database operations. Never string-interpolate SQL.
- Use template engines with auto-escaping enabled.
- Sanitize data in log messages to prevent log injection.

## Authentication and Authorization
- Hash passwords with bcrypt (cost 12+) or argon2. Never use MD5 or SHA1 for passwords.
- Implement rate limiting on authentication endpoints.
- Use short-lived tokens (15 minutes for access, 7 days for refresh).
- Check authorization on every request at the API layer, not just the UI.
- Use the principle of least privilege for all service accounts and API keys.

## Dependencies
- Run `npm audit` / `pip audit` / `cargo audit` in CI.
- Update dependencies with known vulnerabilities within 48 hours for critical, 7 days for high.
- Pin exact versions in production. Use ranges only in libraries.
- Review new dependencies before adding them. Check maintenance status and download counts.

## HTTP Security
- Set security headers: CSP, HSTS, X-Content-Type-Options, X-Frame-Options.
- Use HTTPS everywhere. Redirect HTTP to HTTPS.
- Set cookie attributes: HttpOnly, Secure, SameSite=Strict.
- Implement CORS with explicit allowed origins. Never use wildcard in production.
