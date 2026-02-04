Scan the codebase for leaked secrets, API keys, tokens, and credentials.

## Steps

1. Define patterns to search for:
   - AWS keys: `AKIA[0-9A-Z]{16}`, `aws_secret_access_key`.
   - API keys: `sk-[a-zA-Z0-9]{32,}`, `api[_-]?key\s*[:=]`.
   - Tokens: `ghp_`, `gho_`, `github_pat_`, `xoxb-`, `xoxp-`.
   - Private keys: `-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----`.
   - Database URLs: `(postgres|mysql|mongodb)://[^:]+:[^@]+@`.
   - Generic secrets: `password\s*[:=]\s*["'][^"']+["']`, `secret\s*[:=]`.
2. Scan all tracked files: `git ls-files` (skip binary files).
3. Also scan `.env` files that may not be tracked.
4. Exclude known false positives (test fixtures, documentation examples, `.env.example`).
5. For each finding, determine severity:
   - **CRITICAL**: Real credentials with high entropy that appear functional.
   - **WARNING**: Patterns that look like secrets but may be placeholders.
   - **INFO**: References to secret names without values.
6. Check if `.gitignore` properly excludes sensitive files (`.env`, `*.pem`, `*.key`).
7. Suggest remediation for each finding.

## Format

```
Secrets Scan Results
====================

CRITICAL (immediate action required):
  - <file>:<line> - <type>: <masked-value>

WARNING (review needed):
  - <file>:<line> - <type>: <description>

.gitignore check:
  - [ ] .env files excluded
  - [ ] Key files excluded

Remediation:
  1. Rotate <credential type>
  2. Add <pattern> to .gitignore
```

## Rules

- Never print full secret values; mask all but the first 4 characters.
- Scan both tracked and untracked files.
- Check git history for secrets in past commits using `git log -p --all -S`.
- Suggest `.gitignore` additions for any unprotected secret file patterns.
- Recommend using environment variables or secret managers for all findings.
