---
name: authentication-patterns
description: Authentication and authorization patterns including OAuth2, JWT, RBAC, session management, and PKCE flows
---

# Authentication Patterns

## JWT Access and Refresh Tokens

```typescript
import jwt from "jsonwebtoken";

interface TokenPayload {
  sub: string;
  email: string;
  roles: string[];
}

function generateTokens(user: User) {
  const accessToken = jwt.sign(
    { sub: user.id, email: user.email, roles: user.roles },
    process.env.JWT_SECRET!,
    { expiresIn: "15m", issuer: "auth-service" }
  );

  const refreshToken = jwt.sign(
    { sub: user.id, tokenVersion: user.tokenVersion },
    process.env.REFRESH_SECRET!,
    { expiresIn: "7d", issuer: "auth-service" }
  );

  return { accessToken, refreshToken };
}

function verifyAccessToken(token: string): TokenPayload {
  return jwt.verify(token, process.env.JWT_SECRET!, {
    issuer: "auth-service",
  }) as TokenPayload;
}
```

Short-lived access tokens (15 minutes) with longer-lived refresh tokens (7 days). Store refresh tokens in HTTP-only cookies.

## Auth Middleware

```typescript
function authenticate(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing authorization header" });
  }

  try {
    const payload = verifyAccessToken(header.slice(7));
    req.user = payload;
    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: "Token expired" });
    }
    return res.status(401).json({ error: "Invalid token" });
  }
}

function authorize(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ error: "Not authenticated" });
    if (!roles.some(role => req.user.roles.includes(role))) {
      return res.status(403).json({ error: "Insufficient permissions" });
    }
    next();
  };
}

app.get("/admin/users", authenticate, authorize("admin"), listUsers);
```

## OAuth2 Authorization Code Flow with PKCE

```typescript
import crypto from "crypto";

function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString("base64url");
  const challenge = crypto
    .createHash("sha256")
    .update(verifier)
    .digest("base64url");
  return { verifier, challenge };
}

app.get("/auth/login", (req, res) => {
  const { verifier, challenge } = generatePKCE();
  req.session.codeVerifier = verifier;

  const params = new URLSearchParams({
    response_type: "code",
    client_id: process.env.OAUTH_CLIENT_ID!,
    redirect_uri: `${process.env.APP_URL}/auth/callback`,
    scope: "openid profile email",
    code_challenge: challenge,
    code_challenge_method: "S256",
    state: crypto.randomBytes(16).toString("hex"),
  });

  res.redirect(`${process.env.OAUTH_AUTHORIZE_URL}?${params}`);
});

app.get("/auth/callback", async (req, res) => {
  const { code } = req.query;

  const tokenResponse = await fetch(process.env.OAUTH_TOKEN_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: code as string,
      redirect_uri: `${process.env.APP_URL}/auth/callback`,
      client_id: process.env.OAUTH_CLIENT_ID!,
      code_verifier: req.session.codeVerifier,
    }),
  });

  const tokens = await tokenResponse.json();
  const userInfo = jwt.decode(tokens.id_token);

  req.session.user = { id: userInfo.sub, email: userInfo.email };
  res.redirect("/dashboard");
});
```

## RBAC Model

```typescript
interface Permission {
  resource: string;
  action: "create" | "read" | "update" | "delete";
}

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  viewer: [
    { resource: "posts", action: "read" },
    { resource: "comments", action: "read" },
  ],
  editor: [
    { resource: "posts", action: "create" },
    { resource: "posts", action: "read" },
    { resource: "posts", action: "update" },
    { resource: "comments", action: "create" },
    { resource: "comments", action: "read" },
  ],
  admin: [
    { resource: "*", action: "create" },
    { resource: "*", action: "read" },
    { resource: "*", action: "update" },
    { resource: "*", action: "delete" },
  ],
};

function hasPermission(roles: string[], resource: string, action: string): boolean {
  return roles.some(role =>
    ROLE_PERMISSIONS[role]?.some(
      p => (p.resource === resource || p.resource === "*") && p.action === action
    )
  );
}
```

## Anti-Patterns

- Storing JWTs in `localStorage` (vulnerable to XSS; use HTTP-only cookies)
- Using symmetric secrets for JWTs across multiple services (use RS256 with key pairs)
- Not validating `iss`, `aud`, and `exp` claims on token verification
- Implementing custom password hashing instead of using bcrypt/argon2
- Missing CSRF protection on cookie-based authentication
- Returning different error messages for "user not found" vs "wrong password" (user enumeration)

## Checklist

- [ ] Access tokens are short-lived (15 minutes or less)
- [ ] Refresh tokens stored in HTTP-only, Secure, SameSite cookies
- [ ] Passwords hashed with bcrypt or argon2 (never MD5/SHA)
- [ ] OAuth2 PKCE flow used for public clients
- [ ] RBAC permissions checked at both route and data access layers
- [ ] Token revocation supported via version counter or blocklist
- [ ] CSRF protection enabled for cookie-based auth
- [ ] Authentication errors do not reveal whether the user exists
