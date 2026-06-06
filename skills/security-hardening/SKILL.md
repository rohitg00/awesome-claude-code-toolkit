---
name: security-hardening
description: Application security covering input validation, auth, headers, secrets management, and dependency auditing
---

# Security Hardening

## Input Validation

Validate all input at the boundary. Never trust client-side validation alone.

```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  age: z.number().int().min(13).max(150),
});

function createUser(req: Request) {
  const result = CreateUserSchema.safeParse(req.body);
  if (!result.success) {
    return { status: 400, errors: result.error.flatten().fieldErrors };
  }
  // result.data is typed and validated
}
```

Rules:
- Validate type, length, format, and range on every input
- Use allowlists over denylists (accept known good, reject everything else)
- Validate file uploads: check MIME type, file extension, and magic bytes
- Limit request body size at the server/proxy level (e.g., 1MB max)

## Output Encoding

```typescript
// Prevent XSS: encode output based on context
// HTML context: use framework auto-escaping (React does this by default)
// Never use dangerouslySetInnerHTML with user input

// URL context: encode parameters
const safeUrl = `/search?q=${encodeURIComponent(userInput)}`;

// JSON context: use JSON.stringify (handles escaping)
const safeJson = JSON.stringify({ query: userInput });
```

Never construct HTML strings with user input. Use templating engines with auto-escaping enabled.

## SQL Injection Prevention

```python
# NEVER do this
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Always use parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

```typescript
// NEVER do this
db.query(`SELECT * FROM users WHERE email = '${email}'`);

// Always use parameterized queries
db.query("SELECT * FROM users WHERE email = $1", [email]);
```

Use an ORM or query builder. If writing raw SQL, always parameterize.

## CSRF Protection

```typescript
// Server: generate and validate CSRF tokens
import { randomBytes } from 'crypto';

function generateCsrfToken(): string {
  return randomBytes(32).toString('hex');
}

// Middleware: validate on state-changing requests
function csrfMiddleware(req, res, next) {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) {
    const token = req.headers['x-csrf-token'] || req.body._csrf;
    if (!timingSafeEqual(token, req.session.csrfToken)) {
      return res.status(403).json({ error: 'Invalid CSRF token' });
    }
  }
  next();
}
```

For APIs with token-based auth (Bearer tokens), CSRF is not needed since the token is not auto-sent by browsers.

## Content Security Policy

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

Start strict, relax as needed. Use `nonce` for inline scripts instead of `unsafe-inline`. Report violations with `report-uri` directive. Test with `Content-Security-Policy-Report-Only` first.

## Security Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

Set these on every response. Use `helmet` (Node.js) or equivalent middleware.

## Rate Limiting

```typescript
// Per-user, per-endpoint rate limiting
const rateLimits = {
  'POST /auth/login':    { window: '15m', max: 5 },
  'POST /auth/register': { window: '1h',  max: 3 },
  'POST /api/*':         { window: '1m',  max: 60 },
  'GET /api/*':          { window: '1m',  max: 120 },
};
```

Use sliding window algorithm. Store counters in Redis. Return `429` with `Retry-After` header. Apply stricter limits to authentication endpoints.

## JWT Best Practices

- Use short expiry (15 minutes) for access tokens
- Use refresh tokens (7-30 days) stored in httpOnly cookies
- Sign with RS256 (asymmetric) for microservices, HS256 (symmetric) for monoliths
- Never store sensitive data in JWT payload (it is base64 encoded, not encrypted)
- Validate `iss`, `aud`, `exp`, and `nbf` claims on every request
- Implement token revocation via a denylist or short expiry + rotation

```typescript
// Verify JWT with all checks
const payload = jwt.verify(token, publicKey, {
  algorithms: ['RS256'],
  issuer: 'auth.example.com',
  audience: 'api.example.com',
  clockTolerance: 30,
});
```

## Secrets Management

- Never commit secrets to version control (use `.gitignore` for `.env`)
- Use environment variables for runtime secrets
- Use a secrets manager in production (AWS Secrets Manager, HashiCorp Vault, Doppler)
- Rotate secrets regularly (90-day maximum for API keys)
- Use different secrets per environment (dev/staging/prod)
- Scan for leaked secrets in CI: `trufflehog`, `gitleaks`, `git-secrets`

```bash
# Check for secrets in git history
gitleaks detect --source . --verbose

# Pre-commit hook to prevent secret commits
gitleaks protect --staged
```

## Dependency Auditing

```bash
# Node.js
npm audit --production
npx better-npm-audit audit --level=high

# Python
pip-audit
safety check

# Go
govulncheck ./...
```

Run dependency audits in CI on every PR. Block merges on critical/high vulnerabilities. Pin dependency versions. Update dependencies weekly with automated PRs (Dependabot, Renovate).

## Checklist Before Deploy

1. All inputs validated with schema validation
2. SQL queries parameterized
3. Security headers configured
4. HTTPS enforced with HSTS
5. Secrets externalized, not in code
6. Dependencies audited, no critical vulnerabilities
7. Rate limiting on all public endpoints
8. Authentication tokens expire and rotate
9. Error messages do not leak internal details
10. Logging captures security events without sensitive data
