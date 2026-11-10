# Deploy runbook — `contacts.ntxpllc.cloud` on the Hostinger VPS + Supabase

For any Claude session that has the **Hostinger connector** (`mcp.ntxpllc.cloud`) — or follow the manual ssh path below.
Verified account facts (hostinger-ntxp-skill, 2026-10-08/09): VPS id **1243476**, IPv4 **72.61.144.53**, DNS zone **`ntxpllc.cloud`**.
Steps marked **⛔ confirm** change shared infrastructure — state the exact change and wait for a yes first.

## 0. You provide (nothing below can be done without these)
1. **Supabase**: run `deploy/supabase_setup.sql` once (SQL editor) with a real password → the session-pooler connection string for role `ntxp_contacts_app.<project-ref>`.
2. **Google OAuth client** (Web application), consent screen **Internal**, authorised origin `https://contacts.ntxpllc.cloud` → client id.
3. **GitHub package** `ghcr.io/ntxptrevor/ntxp-contacts` is built by CI on merge to `main`. The Docker Manager can't log in to a registry → set the package **public** (it contains only code: no secrets, no NTXP engine/logo).
4. The three peer secrets: `ntxp peers keygen schedules|contracts|formfill`, then give each app its secret.

## 1. Read before writing (no changes)
```
VPS_getProjectContentsV1 { virtualMachineId: 1243476, projectName: "hostinger-mcp" }
```
Copy its proxy pattern: the **network name** (→ `PROXY_NETWORK`), whether the proxy is **Traefik** (→ labels in `docker-compose.yml`, plus the
cert-resolver name → `TRAEFIK_CERTRESOLVER`) or Caddy/other (then swap the labels for that proxy's mechanism). Also `VPS_getProjectListV1` to see what's running.
Never publish 80/443 from this app — the existing proxy owns them.

## 2. DNS — ⛔ confirm (the skill's safe-write sequence)
```
DNS_getDNSRecordsV1 { domain: "ntxpllc.cloud" }          # note existing records
DNS_getDNSSnapshotListV1 { domain: "ntxpllc.cloud" }     # rollback point
DNS_validateDNSRecordsV1 { domain, zone: [{name:"contacts", type:"A", ttl:300, records:[{content:"72.61.144.53"}]}], overwrite:false }
# state the diff, get a yes, then:
DNS_updateDNSRecordsV1  { ...same..., overwrite:false }
DNS_getDNSRecordsV1     { domain: "ntxpllc.cloud" }      # verify
```
(`getent hosts contacts.ntxpllc.cloud` returned nothing on 2026-10-30, so the record doesn't exist yet.)

## 3. One-time: put the proprietary engine + logo on the VPS (not in git, not in the image)
Needs ssh/scp (the Docker Manager can't upload files):
```bash
ssh root@72.61.144.53 'mkdir -p /docker/ntxp-contacts/engine /docker/ntxp-contacts/assets'
scp -r <skill>/ntxp-branded-document-2/{scripts,templates,types,assets,reference} root@72.61.144.53:/docker/ntxp-contacts/engine/
scp <skill>/ntxp-branded-document-2/assets/ntxp_logo_reversed.png root@72.61.144.53:/docker/ntxp-contacts/assets/
```
Skip this and the app still works — reports fall back to the browser's Save-as-PDF.

## 4. Create the project — ⛔ confirm
```
VPS_createNewProjectV1 { virtualMachineId: 1243476, project_name: "ntxp-contacts",
                         content: <contents of deploy/docker-compose.yml>, environment: <values from deploy/.env.example> }
```
`environment` carries secrets — don't echo it into logs or chat. Then `VPS_getProjectLogsV1` until you see the server start.

## 5. Initialise + verify
```
docker exec <container> ntxp init        # creates the schema in ntxp_contacts, applies RLS lockdown
curl -fsS https://contacts.ntxpllc.cloud/health
curl -s -o /dev/null -w '%{http_code}\n' https://contacts.ntxpllc.cloud/api/contacts      # expect 401
```
Then open the site and sign in with an @ntxpllc.com account. Load data: `ntxp import all --all /data` (or run the nightly sweep/reconcile),
`ntxp peers status` to confirm the three peers, `ntxp peers backfill <peer>` for each webhook peer.

## Update / rollback
`VPS_updateProjectV1` pulls the newest image and keeps volumes; pin a `:<sha>` tag in the compose to roll back.

## Manual path (no Hostinger connector)
ssh to the VPS, `mkdir -p /docker/ntxp-contacts`, save `docker-compose.yml` + an `.env` there, `docker compose --env-file .env up -d`.

## Not verified when this was written
No Docker daemon, Supabase project, Google OAuth client or Hostinger session was available in the build environment, so the image build, the
CI workflow, the live Supabase connection, the Traefik routing and the Google token exchange are untested end-to-end. What *was* verified: the
Supabase role/schema SQL on real PostgreSQL (isolation + RLS + anon denial), the app against PostgreSQL 16, and a clean wheel install.
