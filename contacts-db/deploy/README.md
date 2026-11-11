# Deploy `contacts.ntxpllc.com` on the Hostinger VPS

Stack: **Hostinger VPS (Docker)** → Caddy (auto-HTTPS) → `ntxp serve-http` (live page + `/api` + `/mcp` + `/carddav`) →
**Supabase Postgres** (canonical DB + persisted council answers).

## What you need to provide (I can't do these for you)
| # | Item | Where |
|---|---|---|
| 1 | **Hostinger VPS** with the Docker template, SSH access | hPanel › VPS |
| 2 | DNS **A record** `contacts.ntxpllc.com` → the VPS IP | your DNS |
| 3 | **Supabase project** → connection string (owner/service role) | Supabase › Project Settings › Database |
| 4 | **Google OAuth client** (Web app). Origin `https://contacts.ntxpllc.com`. Consent screen **User type: Internal** (this is what restricts sign-in to the ntxpllc.com Workspace) | Google Cloud Console |
| 5 | The installed **NTXP Branded Document** skill folder (for server-side PDF/DOCX + the logo) | your machine |

## Steps
```bash
git clone <repo> && cd awesome-claude-code-toolkit/contacts-db/deploy
cp .env.example .env && $EDITOR .env          # Supabase URL + Google client id
./deploy.sh /path/to/ntxp-branded-document-2   # copies engine+logo locally (NOT committed), builds, starts
docker compose exec app ntxp init               # once: creates the schema; RLS lockdown is applied automatically
```
Then load data: `docker compose exec app ntxp import all --all /data` (or the nightly sweep/reconcile jobs), open
<https://contacts.ntxpllc.com>, and sign in with your @ntxpllc.com account.

## Security model
- **Sign-in**: Google Workspace token, `hd == ntxpllc.com`, verified server-side on every request. `deploy.sh` refuses `NTXP_MCP_AUTH=none`.
- **Supabase**: RLS is **enabled with no policies** on every table (re-applied after each migration), and `anon`/`authenticated`
  grants are revoked, so the Supabase Data API can never expose contact PII. Only this server (owner/service role) reads the data.
- **Headers**: CSP limited to Google sign-in + fonts, `X-Frame-Options: DENY`, `nosniff`, HSTS (Caddy).
- **Untrusted data**: contact fields come from Gmail/Calendar/CRMs, so they're escaped in the page and stripped of `<`/`>` before
  reaching the document-engine renderer.
- **Proprietary assets** (engine, logo) live only on the server — `.gitignore`d.

## Not verified in the build environment
There was no Docker daemon, no Supabase project and no Google OAuth client available, so the image build, the live Supabase
connection and the real Google token exchange are **untested end-to-end**. What *was* verified: clean `pip install` of the wheel
(page + migrations packaged), the full suite on SQLite and PostgreSQL 16 (incl. RLS blocking an `anon` role), the production
auth gate in a real browser, and the document-engine render of every report.
