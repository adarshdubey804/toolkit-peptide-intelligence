# Production readiness and deployment gates

**Status: not approved for public production deployment.** The repository has useful authentication, tenant scoping, curation controls and CI coverage, but the controls below must be completed or supplied by the deployment environment before exposing the service to untrusted traffic.

## Controls already present

- JWT authentication with issuer, audience and expiry validation.
- Current-user resolution bound to the organization ID in the signed token and an active database membership.
- Role checks on supported organization, curation, evidence-review, vendor, analytical, formulation and process-submission workflows.
- Organization admins can add an existing registered account with a bounded non-admin role; membership changes and organization-context switches are audit logged.
- Direct research-agent execution requires authentication. The agent catalogue remains public and read-only.
- AI synthesis and structured extraction are development-only. Keep AI_SYNTHESIS_ENABLED=false in production.
- Development migrations are checksum-tracked and run automatically only when APP_ENV=development. Production migrations must be run as a separate, controlled deployment job.
- Backend PostgreSQL migration tests and frontend build run in CI. Frontend CI now runs npm audit at moderate severity and blocks a build if any moderate, high or critical advisory is present.

These controls do not amount to a complete production security program.

### Limited row-level-security pilot

The current row-level-security pilot spans migrations 044–061. Covered modules include vendor material offerings and batch evidence; organization-owned analytical methods and their sources/decisions; formulations and process-knowledge records and child evidence; molecular interaction assessments; evidence appraisals and duplicate-review workflows; organization-scoped curation reviews and append-only decisions; user-private agent sessions and messages; regulatory guidance review history and source polling artifacts; vendor identities, facilities, certifications, services and peptide/method evidence links; laboratory capability claims; and peptide-method and peptide-test applicability assessments; organization-private editorial decisions on the shared analytical test catalogue; tamper-evident audit events scoped to the owning organization and authenticated actor. Authenticated API requests bind the organization and user from the validated JWT and active membership to app.organization_id and app.user_id using transaction-local set_config(..., true). Public reads are limited to explicitly public and verified records under each module's parent-evidence rules; verification alone does not publish organization submissions. The source registry remains outside RLS because the scheduler enumerates due sources across organizations; a dedicated worker database role is still required to close that control-plane gap. This is a bounded pilot, not comprehensive tenant isolation: remaining tenant-owned tables, route authorization, privileged operator access, background workers and connection-pool behavior still require independent validation. PostgreSQL clears transaction-local context at transaction end, and CI exercises reset behavior.

Public policies permit anonymous reads only for records explicitly marked public and verified. Physical lots, analytical reports and review decisions are organization-scoped. Method source links inherit their parent method's visibility; method review decisions are organization-scoped. Formulation and process child records inherit their parent visibility; public child observations require verified child status. Writes require the transaction's organization context.

**This is a bounded pilot, not complete tenant isolation.** Other tenant-owned tables and background workers are not yet covered. Every worker or maintenance job that accesses these RLS-protected tables must establish its own trusted transaction-local organization context, or use a separately controlled administrative database role. Do not rely on a connection-level/session-level setting. Continue the table-by-table RLS rollout only after endpoint, worker, connection-pool and cross-tenant tests are in place.


## Mandatory deployment controls

### 1. Network boundary and HTTPS

- Terminate TLS at a maintained reverse proxy or managed ingress.
- Do not publish the backend port 8000 directly to the public internet. Keep the API and database on private container/network segments; expose only the HTTPS ingress.
- Do not publish PostgreSQL port 5432.
- Set FRONTEND_ORIGIN to the exact HTTPS frontend origin and NEXT_PUBLIC_API_BASE_URL to the HTTPS API origin.
- If a load balancer or CDN sits in front of the proxy, trust forwarded client-IP headers only from explicitly configured proxy ranges. Never trust arbitrary X-Forwarded-For.

### 2. Rate limiting and abuse controls

The application now provides shared PostgreSQL fixed-window limits for login, registration, direct and saved agent execution, and public research discovery. This is initial coverage, not a complete abuse-control layer: additional sensitive write/enrichment routes still need limits, and production must configure trusted proxy client identity and ingress/WAF controls.

At minimum, apply stricter limits to:
- POST /api/v1/auth/login
- POST /api/v1/auth/register
- POST /api/v1/agents/{agent_id}/run
- External research retrieval routes under /api/v1/research/
- Any future AI synthesis or extraction endpoint

Illustrative Nginx policy (adapt upstream names, TLS configuration, trusted proxy ranges and thresholds to the actual deployment):

~~~nginx
limit_req_zone $binary_remote_addr zone=auth_per_ip:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=research_per_ip:10m rate=15r/m;

server {
    listen 443 ssl;
    server_name peptide.example.org;

    limit_req_status 429;

    location = /api/v1/auth/login {
        limit_req zone=auth_per_ip burst=5 nodelay;
        proxy_pass http://backend:8000;
    }

    location = /api/v1/auth/register {
        limit_req zone=auth_per_ip burst=2 nodelay;
        proxy_pass http://backend:8000;
    }

    location ^~ /api/v1/agents/ {
        limit_req zone=research_per_ip burst=5 nodelay;
        proxy_pass http://backend:8000;
    }

    location ^~ /api/v1/research/ {
        limit_req zone=research_per_ip burst=10 nodelay;
        proxy_pass http://backend:8000;
    }

    location /api/ {
        proxy_pass http://backend:8000;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
~~~

This is an ingress example, not a configuration already installed by this repository. Per-IP limits alone are not sufficient against distributed abuse; use account-level controls and a shared limiter/WAF where appropriate. Validate that legitimate research workloads are not blocked.

### 3. Identity lifecycle

The current identity foundation still lacks:
- Email ownership verification
- Password reset and account recovery
- MFA
- Refresh-token rotation and revocation
- Email-based invitations and membership acceptance

The current member-management workflow adds an existing registered account immediately; it does not send an invitation or verify email ownership. Do not describe it as an invitation workflow.

### 4. Audit and review governance

- Audit-event rows are now append-only, organization-scoped and actor-bound at the database layer. Event coverage is still not comprehensive across every state-changing endpoint.
- Reviewer qualification and conflict-of-interest controls require a defined operating policy.
- Perform an independent authorization and tenant-isolation review, including negative tests across all organization-scoped endpoints.
- Confirm that operational logs do not expose passwords, bearer tokens, API keys or sensitive research data.
- Define retention, export and tamper-resistance requirements for audit records.

### 5. Operations and recovery

Before production:
- Store database credentials and APP_SECRET_KEY in a managed secret store. Use a unique random secret of at least 32 characters.
- Set APP_ENV=production; never use the development migration startup path.
- Apply forward-only migrations through a reviewed deployment job and verify migration checksums.
- Configure encrypted database connections where the database is remote.
- Schedule encrypted backups and perform restore drills.
- Add error monitoring, health/readiness probes, alerting, resource limits and an incident-response procedure.
- Pin frontend dependencies with a committed lockfile and use reproducible installation (npm ci) in CI and the production image. The repository currently has no committed frontend/package-lock.json; this remains a reproducibility task.

## Release decision checklist

A release owner should explicitly confirm all of the following before public launch:

- [ ] HTTPS ingress and private backend/database networking verified
- [ ] Login, registration, agent and research rate limits deployed and tested
- [ ] Identity lifecycle controls or documented compensating controls approved
- [ ] Cross-tenant and role-based negative tests completed
- [ ] Audit coverage and reviewer governance approved
- [ ] Production migrations rehearsed and rollback/recovery plan reviewed
- [ ] Backups restored successfully in a drill
- [ ] Dependency lockfile committed and vulnerability audit clean
- [ ] Independent security review completed
- [ ] AI synthesis remains disabled unless separately approved and secured

A successful CI run alone does not satisfy this checklist.
