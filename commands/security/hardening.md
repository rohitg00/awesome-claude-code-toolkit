Apply security hardening measures to the codebase.

## Steps

### 1. HTTP Security Headers
Add or verify these headers in the web server or middleware configuration:
- `Content-Security-Policy`: Restrict script sources, disable inline scripts.
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains`.
- `X-Content-Type-Options`: `nosniff`.
- `X-Frame-Options`: `DENY` or `SAMEORIGIN`.
- `Referrer-Policy`: `strict-origin-when-cross-origin`.
- `Permissions-Policy`: Disable unused browser features (camera, microphone, geolocation).

### 2. Rate Limiting
- Add rate limiting to authentication endpoints (5 attempts per minute).
- Add rate limiting to public API endpoints (100 requests per minute per IP).
- Implement exponential backoff for repeated failures.
- Use sliding window counters, not fixed windows.

### 3. Input Validation
- Add schema validation (Zod, Joi, Pydantic) to all API endpoints.
- Sanitize HTML output to prevent XSS: use DOMPurify or equivalent.
- Validate file upload types, sizes, and names.
- Implement request body size limits.

### 4. Output Encoding
- Ensure all user-provided data is escaped before rendering in HTML, SQL, shell commands, or logs.
- Use parameterized queries for all database operations.
- Use template engines with auto-escaping enabled by default.
- Sanitize data before including in log messages to prevent log injection.

### 5. Authentication Hardening
- Enforce minimum password complexity (12+ characters, no common passwords).
- Implement account lockout after repeated failures.
- Add multi-factor authentication support if not present.
- Set secure cookie attributes: `HttpOnly`, `Secure`, `SameSite=Strict`.
- Implement proper session invalidation on logout.

### 6. Dependency Hardening
- Pin exact dependency versions in production.
- Enable automated dependency updates (Dependabot, Renovate).
- Remove unused dependencies.
- Use `npm ci` instead of `npm install` in CI.

## Rules

- Apply hardening incrementally. Test after each change.
- Do not break existing functionality. Security measures should be transparent to legitimate users.
- Document any hardening that requires configuration changes at deployment time.
- Verify hardening with automated tests where possible (e.g., test that rate limiting returns 429).
