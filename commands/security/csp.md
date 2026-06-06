Generate Content Security Policy headers for a web application.

## Steps

1. Scan the project for frontend assets and their sources:
   - JavaScript files: inline scripts, external CDN scripts, dynamic imports.
   - CSS files: inline styles, external stylesheets, CSS-in-JS libraries.
   - Images: local assets, external image CDNs, data URIs.
   - Fonts: Google Fonts, self-hosted, CDN-hosted.
   - API calls: `fetch`, `XMLHttpRequest`, WebSocket connections.
   - Frames: iframes, embedded content.
2. Identify all external domains referenced in the codebase.
3. Build CSP directives:
   - `default-src`: Fallback policy.
   - `script-src`: JavaScript sources with nonce or hash strategy.
   - `style-src`: CSS sources.
   - `img-src`: Image sources.
   - `connect-src`: API endpoints, WebSocket URLs.
   - `font-src`: Font sources.
   - `frame-src`: Iframe sources.
   - `object-src`: Plugin sources (should be `'none'`).
4. Add reporting configuration: `report-uri` or `report-to`.
5. Generate both enforcing and report-only headers.
6. Output as HTTP header format and as meta tag format.

## Format

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-{random}' https://cdn.example.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https://images.example.com;
  connect-src 'self' https://api.example.com;
  font-src 'self' https://fonts.gstatic.com;
  object-src 'none';
  frame-ancestors 'none';
  report-uri /csp-report;
```

## Rules

- Never use `unsafe-inline` for scripts; prefer nonces or hashes.
- Always include `object-src 'none'` and `frame-ancestors 'self'`.
- Start with a strict policy and relax only as needed.
- Provide a `Content-Security-Policy-Report-Only` header for testing.
- Document each allowed domain with a comment explaining why it is needed.
