# Toolkit Peptide Intelligence

Scientific intelligence for peptide research and pharmaceutical development, built by Toolkit Technologies.

## Current foundation

- Next.js frontend with peptide directory, scientific profile views, interactive knowledge graph and multi-source research workspace and retrieval-only research assistant.
- FastAPI backend with JWT authentication, organization registration, membership-based roles, organization-scoped research projects, scientific review submission/assignment/decision APIs, append-only curation decisions, researcher profiles, verified-record catalogue search, pagination, profile detail, verified peptide knowledge graph and readiness endpoints, plus organization-scoped structured evidence extraction and reviewer field-decision APIs.
- PostgreSQL + pgvector schema for peptide identity, sequences, chemical properties, structures, targets, pathways, publications, research studies, evidence claims, analytical methods, vendor records, certifications and regulatory status.
- Read-only discovery integrations with PubMed abstract retrieval: PubMed, ClinicalTrials.gov API v2, UniProtKB, RCSB PDB and PubChem.
- Additive provenance and curation schema: source content hashes and versions, cross-database candidate entity links, review queue and append-only editorial decisions.
- External results remain unreviewed and are never silently promoted into curated records.
- GitHub Actions workflows for backend API-contract tests and frontend production builds.

## API abuse protection\n\n- Migration `036_shared_api_rate_limiting.sql` creates PostgreSQL-backed fixed-window counters shared across backend instances. Login is limited to 10 requests/minute per immediate client IP, registration to 5/minute per immediate client IP, and direct or saved research-agent execution to 10/minute per authenticated user, while public upstream research discovery to 30/minute per immediate client IP. Limits and window length are configurable with `LOGIN_RATE_LIMIT_PER_WINDOW`, `REGISTRATION_RATE_LIMIT_PER_WINDOW`, `AGENT_RATE_LIMIT_PER_WINDOW`, `PUBLIC_RESEARCH_RATE_LIMIT_PER_WINDOW`, and `RATE_LIMIT_WINDOW_SECONDS`. Exceeded requests return HTTP 429 with `Retry-After`. Stale client buckets are opportunistically removed after 30 days. The application deliberately does not trust arbitrary `X-Forwarded-For` headers; production proxy deployments must configure trusted client-address handling at the ASGI edge.\n\n## Local development

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and APP_SECRET_KEY with long, unique random values.
3. Set NCBI_EMAIL to a valid contact email if you want to enable PubMed discovery. NCBI_API_KEY is optional.
4. AI synthesis is opt-in for local development only: set AI_SYNTHESIS_ENABLED=true, AI_API_KEY, and AI_MODEL. Never expose provider keys to the frontend. The synthesis route is deliberately blocked outside development until authenticated access and rate limiting are implemented.
5. Run docker compose up --build.
6. Open the frontend at http://localhost:3000, peptide directory at http://localhost:3000/peptides, knowledge graph at http://localhost:3000/knowledge-graph, research workspace at http://localhost:3000/research, research assistant at http://localhost:3000/research-assistant, vendor directory at http://localhost:3000/vendors, analytical method catalogue at http://localhost:3000/analytical-methods, formulation intelligence at http://localhost:3000/formulations, process intelligence at http://localhost:3000/process-knowledge, bioinformatics at http://localhost:3000/bioinformatics, structure intelligence at http://localhost:3000/structures, interaction intelligence at http://localhost:3000/interactions, and API docs at http://localhost:8000/docs.

Development startup applies all ordered SQL migrations in `database/migrations`. Migration 016 adds null-safe uniqueness for regulatory version observations (PostgreSQL 15+; the supplied Compose database uses PostgreSQL 16).

- Structured peptide analytical test catalogue: migration `032_analytical_test_catalogue.sql` seeds 12 source-linked draft reference candidates covering identity, purity/related substances, quantity, sequence/structure, amino-acid composition, aggregation/particles, counterions/residual peptide-associated reagents, endotoxins, sterility, bioburden/microbial limits, potency and stability. GET `/api/v1/analytical-methods/test-catalogue` supports text and quality-attribute filtering. Seed entries remain `draft`; candidate method families are discovery prompts only, not method validation, acceptance criteria or a universal test panel. Sources include FDA/ICH Q6B and USP peptide-related documentary standards.

- Analytical reference crosswalk: migration `035_analytical_reference_framework_crosswalk.sql` stores source-linked ICH Q6B, Q2(R2), Q14 and selected USP peptide chapters, including scope, document type, jurisdiction/system, version, effective date and limitations. GET `/api/v1/analytical-methods/test-catalogue/frameworks` exposes draft crosswalk records. These references do not establish legal applicability, mandatory testing or product-specific acceptance criteria.

- Peptide-specific test applicability: migration `034_peptide_test_applicability.sql` links a verified peptide identity to a test-catalogue entry with an evidence-backed assessment (`applicable`, `not_applicable`, `conditional`, or `undetermined`), material form, matrix, intended-use context, rationale, limitations and source provenance. Organization-scoped submission and append-only review decisions are exposed under `/api/v1/analytical-methods/test-catalogue/applicability`. Public discovery requires the applicability assessment, peptide identity and shared test definition each to be independently verified; an organization decision cannot globally verify a shared test definition. This is not a universal panel or a validated method.

- Organization-scoped test-catalogue review: migration `033_analytical_test_catalogue_curation.sql` adds append-only review decisions. Authenticated GET `/api/v1/analytical-methods/test-catalogue/reviews` and POST `/api/v1/analytical-methods/test-catalogue/{test_id}/decisions` allow curators/reviewers to record organization-specific verification, rejection or change requests. These decisions do not globally promote or alter the shared draft catalogue.

## Evidence intelligence and scientific appraisal

- Migration 013 adds reviewer-authored `evidence_appraisals` and organization-scoped `publication_duplicate_candidates`.
- Reviewer endpoints: GET `/api/v1/evidence-intelligence/claims`, POST `/api/v1/evidence-intelligence/appraisals`, GET `/api/v1/evidence-intelligence/appraisals/{claim_id}`, and duplicate candidate create/list/decision routes under `/api/v1/evidence-intelligence/duplicate-candidates`.
- Evidence level, study design, risk of bias, replication and limitations remain distinct; no misleading composite evidence grade is inferred. Duplicate matching is a human-review queue and never automatically merges or deletes records.
- Frontend: `/evidence-intelligence`. Access is limited to organization admins, curators and reviewers.

## Persistent agent research sessions

- Migration 012 adds organization- and user-scoped `agent_sessions` and `agent_session_messages` tables.
- Authenticated endpoints: GET/POST `/api/v1/agents/sessions`, GET `/api/v1/agents/sessions/{session_id}`, POST `/api/v1/agents/sessions/{session_id}/messages`, and PATCH `/api/v1/agents/sessions/{session_id}/archive`.
- Agent messages retain the question, retrieval response, source citation list and workflow metadata. Users can attach an exact verified peptide UUID to include its curator-verified profile and claims in session context.
- Frontend workspace: `/agent-workspace`. Sessions are currently private to their creator even when associated with an organization/project; cross-member collaboration and generative chat are not implemented.

## Specialized research agents

- GET `/api/v1/agents` lists nine specialized research workflows: peptide literature, sequence, structure, target interaction, analytical methods, formulation, process development, regulatory/quality and scientific review.
- POST `/api/v1/agents/{agent_id}/run` invokes a bounded source-grounded workflow using the research retrieval layer and returns source records plus a domain-specific review plan.
- Frontend workbench: `/agents`. The initial release is deterministic orchestration and review framing, not nine autonomous LLM agents. Scientific claims remain unverified until human curation; no clinical decisions, dosing or executable manufacturing instructions are generated.

## Peptide-target interaction intelligence

- GET/POST `/api/v1/interactions` lists verified interaction assessments and accepts source-linked researcher submissions.
- GET `/api/v1/interactions/reviews` and POST `/api/v1/interactions/{id}/decisions` provide organization-scoped curator review with append-only decision history. Migration 011 adds interaction assessment and decision tables.
- Records distinguish experimental complexes, computational docking, molecular dynamics, interface analysis and literature reports; residues, interaction features, tool/version and method-specific scores are retained separately. Computational scores are not treated as measured binding affinities. This module records evidence and does not execute docking.

## Structural biology discovery

- GET `/api/v1/research/alphafold?accession=P01308` retrieves AlphaFold DB prediction metadata, confidence summaries and original PDB/mmCIF/PAE resource links.
- GET `/api/v1/research/rcsb?q=...` discovers experimental PDB structures.
- Frontend `/structures` presents experimental and predicted structure records, confidence metadata and links to official external 3D viewers and structure files. External results remain unreviewed; AlphaFold confidence is not binding evidence.

## Bioinformatics sequence tools

- POST `/api/v1/bioinformatics/analyze` calculates standard-residue composition, average/monoisotopic mass estimates, approximate pI, GRAVY, aromaticity and reduced-state 280 nm extinction coefficient.
- POST `/api/v1/bioinformatics/align` performs bounded Needleman-Wunsch global sequence alignment with configurable simple scoring.
- Inputs are limited to the 20 standard amino acids. Results are estimates for unmodified linear peptides with free termini; no PTM-aware chemistry, structure prediction, docking or biological activity prediction is claimed.

## Authentication foundation

- POST `/api/v1/auth/register` creates an organization and its first `organization_admin` account.
- POST `/api/v1/auth/login` issues a short-lived HS256 bearer token.
- GET `/api/v1/auth/me` returns the current active user and organization membership.
- Passwords are stored as Argon2id hashes; tokens are validated against the current database account and role.
- Set `APP_SECRET_KEY` to a unique random value of at least 32 characters. Never reuse the example value.

Organization workspace endpoints include `GET /api/v1/organizations/me`, `GET /api/v1/organizations/members`, `POST /api/v1/organizations/members`, `PATCH /api/v1/organizations/members/{user_id}/role`, `POST /api/v1/organizations/projects` and `GET /api/v1/organizations/projects`. Organization admins can add an existing registered account by email with a non-admin role; this adds membership immediately and does not send an email invitation. `GET /api/v1/auth/organizations` lists the caller's active memberships and `POST /api/v1/auth/switch-organization` issues a new organization-scoped token after checking active membership. Login accepts an optional `organization_id`; the frontend remembers the last selected organization for subsequent sign-ins and safely falls back to another active membership if that preference is no longer valid. Membership roles are organization_admin, curator, reviewer, researcher and viewer. Project visibility is organization-wide or private; private projects are visible only to their creator or explicitly assigned project members. Membership and project access is scoped to the caller's active organization.

This is an initial authentication foundation, not a complete production identity system: email verification, password reset, refresh-token rotation/revocation, MFA, invitation workflows, edge-level rate limiting and security review remain required. Existing research/catalogue routes remain public; authentication is not yet enforced on all catalogue, research discovery or curation operations. Organization workspace and curation endpoints require authentication. Curation submission is limited to organization admins, researchers and curators; review assignment/decisions are limited to organization admins, curators and reviewers. Submitters cannot decide their own reviews, and decision history is protected against update/delete at the database layer. Production deployments must run reviewed, versioned migrations as a separate deployment step.

## API routes

- GET /health — process health.
- GET /ready — database connectivity; returns 503 when unavailable.
- GET /api/v1/peptides — curator-verified catalogue search.
- GET /api/v1/peptides/{id} — verified profile; ID must be a UUID.
- GET /api/v1/peptides/{id}/graph — curator-verified sequence, target, pathway, structure, claim and publication relationships.
- POST /api/v1/dossiers — create a source-linked peptide dossier with aliases, sequence/modifications, chemical properties and evidence claims; submits it directly to the organization's review queue.
- Frontend `/submit-peptide` — authenticated researcher form for dossier submission (login required).
- Frontend `/curation` — organization-scoped curator dashboard with source inspection, assignment and review decisions.
- POST /api/v1/curation/reviews — submit a peptide or evidence claim for review.
- GET /api/v1/curation/reviews — list the current organization's submitted review queue for reviewers.
- PATCH /api/v1/curation/reviews/{id}/assignment — assign an open review to an organization curator/reviewer.
- POST /api/v1/curation/reviews/{id}/decisions — append a verified, rejected, needs-changes or archived decision with rationale.

- GET `/api/v1/enrichment/peptides/{id}` — authenticated, read-only peptide-specific discovery across PubMed, ClinicalTrials.gov, UniProtKB and RCSB PDB. Returns source-linked, unreviewed candidates.
- POST `/api/v1/enrichment/peptides/{id}/candidates` — persist an organization-scoped source candidate for curator review; only official HTTPS provider domains are accepted.
- GET `/api/v1/enrichment/candidates` — list the organization's enrichment review queue.
- POST `/api/v1/enrichment/candidates/{id}/decisions` — append an accepted, rejected, duplicate or needs-review decision with rationale and audit event.
- Migration 006 adds organization-scoped enrichment candidate storage and append-only decision history. Accepting a candidate does not create a verified scientific claim or peptide relationship.
- Process development intelligence: GET/POST `/api/v1/process-knowledge`, GET `/api/v1/process-knowledge/reviews`, POST `/api/v1/process-knowledge/{id}/decisions`. Migration 010 adds source-linked process profiles, development stages, quality-attribute and impurity context, and append-only curator decisions. The catalogue is descriptive and excludes executable synthesis parameters, batch instructions and release criteria.
- Formulation and stability intelligence: GET/POST `/api/v1/formulations`, GET `/api/v1/formulations/reviews`, POST `/api/v1/formulations/{id}/decisions`. Migration 009 adds source-linked formulation profiles, component context, stability observations and append-only review decisions. Formulation records require source references; linked peptide and analytical-method identities must already be curator-verified. Curator review does not validate formulation performance or shelf life.
- Analytical method intelligence: GET/POST `/api/v1/analytical-methods`, GET `/api/v1/analytical-methods/reviews`, POST `/api/v1/analytical-methods/{id}/decisions`. Migration 008 adds method reference provenance and append-only review decisions. Curation verification is separate from method validation status.
- Facility-specific laboratory capability intelligence: migration `031_laboratory_capability_claims.sql` adds source-backed claims linking an already verified vendor service at an independently verified facility to a curator-verified analytical method, optionally narrowed to a verified peptide. Claims retain test purpose, material form, sample matrix, instrument platform, sample and storage/shipping requirements, evidence scope and limitations. Authenticated POST/GET routes `/api/v1/analytical-methods/laboratory-capabilities`, `/reviews`, and `/{claim_id}/decisions` support submission, public reviewed discovery and organization-scoped independent review. A claim is hidden until reviewed; it does not establish present capacity, sample acceptance, accreditation scope, method validation or guaranteed performance.
- Peptide-specific analytical applicability: GET/POST `/api/v1/analytical-methods/applicability`, GET `/api/v1/analytical-methods/applicability/reviews`, POST `/api/v1/analytical-methods/applicability/{id}/decisions`. Migration 024 links a curator-verified analytical method to a curator-verified peptide only through source-backed applicability evidence, material form, sample matrix, test purpose and limitations. The record has its own organization-scoped review history; a general method record does not imply suitability for every peptide, modification or matrix. This is a method-applicability knowledge layer, not a universal test panel or executable protocol.
- Vendor directory: GET/POST `/api/v1/vendors`, POST `/api/v1/vendors/{id}/services`, POST `/api/v1/vendors/{id}/certifications`, GET `/api/v1/vendors/my-submissions` (submitter-scoped), GET `/api/v1/vendors/reviews` (reviewer-scoped), POST `/api/v1/vendors/{id}/decisions`. Migration 007 adds vendor source provenance and append-only vendor review decisions. Migration 025 assigns new submissions to an explicit organization (legacy rows remain unassigned rather than guessing ownership) and adds independent certification review: GET `/api/v1/vendors/certifications/reviews`, POST `/api/v1/vendors/certifications/{certification_id}/decisions`. Only independently verified certification claims appear publicly; vendor identity verification does not imply certification verification. Public certification records now distinguish curator verification from date-derived validity (`current`, `expired`, `not_yet_valid`, or `date_not_provided`), retain source provenance, and reject impossible validity ranges. Vendor service/capability submissions require an already verified vendor and are independently reviewed through GET `/api/v1/vendors/services/reviews` and POST `/api/v1/vendors/services/{service_id}/decisions`; only verified service claims are displayed. Migration 027 adds source-backed links from verified vendor services to curator-verified peptide identities and/or analytical methods. POST `/api/v1/vendors/services/{service_id}/evidence-links` submits a link; GET `/api/v1/vendors/service-evidence-links/reviews` and POST `/api/v1/vendors/service-evidence-links/{link_id}/decisions` curate it; GET `/api/v1/vendors/{vendor_id}/services` lists independently verified service records for relationship submission; GET `/api/v1/vendors/{vendor_id}/capabilities` exposes only accepted links. These are documented provider capability claims, not guarantees of supply, performance or method validation. Migration 029 adds a nullable facility foreign key to vendor service claims; new submissions require an independently verified facility while legacy services remain explicitly unassigned. Public service and capability records show the facility context. Migration 030 attributes each certification claim to its submitter, enabling self-review prevention. New certification claims for verified vendors require a verified facility; pending vendor identity submissions may include vendor-level certification evidence without claiming a facility. GET `/api/v1/vendors/organization-options` supplies organization-scoped verified vendor/facility choices to authorized contributors. Migration 029 links new service claims to an independently verified facility; the database column remains nullable for legacy records, but new submissions must reference a verified site belonging to the parent vendor. Service review, public capability links and peptide/method relationships are facility-scoped. Migration 028 adds facility-level vendor site records with organization-scoped submission, source provenance, append-only independent review decisions and a public endpoint that returns only reviewed facilities: POST `/api/v1/vendors/{vendor_id}/sites`, GET `/api/v1/vendors/sites/reviews`, POST `/api/v1/vendors/sites/{site_id}/decisions`, and GET `/api/v1/vendors/{vendor_id}/sites`. Legacy facilities remain unassigned and in draft; no ownership is inferred.
- GET /api/v1/research/workspace?q=... — parallel discovery across PubMed, ClinicalTrials.gov, UniProtKB and RCSB PDB; each source reports its own availability.
- GET /api/v1/research/assistant/brief?question=... — source-grounded evidence retrieval brief with original-record citations and explicit limitations; retrieval-only.
- POST /api/v1/research/assistant/synthesize — optional development-only AI synthesis over server-retrieved records; disabled by default and blocked outside development pending authentication and rate limiting.
- GET /api/v1/research/pubmed?q=... — PubMed discovery; requires NCBI_EMAIL.
- GET /api/v1/research/clinicaltrials?q=... — ClinicalTrials.gov study discovery.
- GET /api/v1/research/uniprot?q=... — UniProtKB protein discovery.
- GET /api/v1/research/rcsb?q=... — RCSB PDB structure discovery.
- GET /api/v1/research/pubchem?name=... — PubChem compound-property lookup.

External research results remain unreviewed. PubChem compound identity must be checked carefully before linking properties to peptide records.

- Peptide knowledge graph: GET `/api/v1/peptides/{peptide_id}/graph` returns curator-verified connections across sequences, structures, targets, pathways, evidence claims, publications, analytical methods, formulation/stability observations, process knowledge, molecular interaction assessments and accepted evidence appraisals. GET `/api/v1/peptides/{peptide_id}/graph/related` discovers other verified peptides sharing curator-verified targets or pathways. The `/knowledge-graph` workspace supports evidence-type filtering and related-peptide exploration. Shared associations are not proof of equivalent mechanism or clinical interchangeability.\n\n- Comparative peptide research: GET `/api/v1/peptides/compare?ids={uuid}&ids={uuid}` compares two to five curator-verified peptide profiles, sequence records, chemical properties, targets, pathways, evidence claims and linked publications. The `/compare` workspace presents a side-by-side matrix. It does not infer therapeutic equivalence or clinical efficacy.\n\n- Scientific research dossier: GET `/api/v1/peptides/{peptide_id}/report` assembles a source-traceable dossier from verified peptide identity, sequence, chemistry, structures, targets/pathways, claims, accepted appraisals, analytical methods, formulation/stability, process knowledge, interaction assessments, publications and source records. The `/reports` workspace supports browser print/Save as PDF. Reports are a current database snapshot, not an independently validated clinical or regulatory assessment.\n\n- Regulatory guidance intelligence: migration `014_regulatory_guidance_intelligence.sql`; public GET `/api/v1/regulatory` lists only curator-verified references with jurisdiction, authority, document type, version, effective date and original source. Authenticated POST `/api/v1/regulatory` submits source-backed references; organization-scoped GET `/api/v1/regulatory/reviews` and POST `/api/v1/regulatory/{guidance_id}/decisions` provide curator review. The `/regulatory` page is a reference library, not a legal/compliance determination.\n\n
- Regulatory change monitoring: migration `015_regulatory_change_monitoring.sql` adds version snapshots and human-reviewed change events. Authenticated POST `/api/v1/regulatory/{guidance_id}/observations` records a source URL, version metadata, optional SHA-256 content hash and submitter change summary; GET `/api/v1/regulatory/{guidance_id}/history` exposes accepted observations; curator review routes are `/api/v1/regulatory/changes/reviews` and `/api/v1/regulatory/changes/{event_id}/decisions`. This is a human-submitted workflow, not an automated crawler or automatic legal interpretation.

## Scientific governance and safety

Every claim should retain source provenance, study model, evidence classification, limitations and review history. Distinguish measured, calculated, predicted and unverified values; preserve conflicting evidence. The platform is a research-information product, not a clinical decision system. It does not provide patient-specific diagnosis or treatment, unapproved peptide dosing, material-release decisions or GMP manufacturing execution.

This is an early development scaffold, not production-ready software. Production use requires managed authentication, authorization, security testing, backups, monitoring, licensing review and qualified scientific/regulatory review. Do not store real secrets in the repository.


## Regulatory version integrity

- Regulatory version observations are manually submitted snapshots; this is not an automated crawler or alerting service.
- Migration 016 enforces null-safe uniqueness across guidance, source URL, optional revision and optional SHA-256 content hash, preventing duplicate observations when optional fields are absent.
- A reviewer decision of `confirmed_change` or `published` accepts the associated version snapshot; `not_a_change` rejects it. Accepted snapshots alone appear in public history.
- The supplied Compose database is PostgreSQL 16. Deployments must use PostgreSQL 15 or newer for the `NULLS NOT DISTINCT` unique index.


## Official regulatory source registry

- Migration 017 adds an organization-scoped registry for authority sources, including authority, jurisdiction, source type, HTTPS feed URL, declared official domain and suggested polling interval.
- Curators and organization admins can register sources; reviewers can inspect the organization registry.
- Registration validates HTTPS and that the URL host matches the declared domain or a subdomain. It does not prove the domain is genuinely operated by the named authority.
- This milestone stores source metadata only. It does not fetch feeds, crawl websites, run scheduled polling or send alerts. Retrieval connectors must be added with network/SSRF controls and authority-domain verification before enabling ingestion.


## Regulatory RSS ingestion (controlled pilot)
- Migration 019 stores organization-scoped feed observations with stable identifiers, content hashes, raw metadata and pending human-review status.
- Curators/reviewers can manually poll RSS sources with POST `/api/v1/regulatory/sources/{source_id}/poll`, inspect pending observations at GET `/api/v1/regulatory/sources/observations`, and record accepted/rejected/duplicate decisions at POST `/api/v1/regulatory/sources/observations/{observation_id}/decision`.
- Polling is limited to registered RSS feeds on a fixed platform allowlist: FDA, EMA, UK government, CDSCO and WHO domains. HTTPS only, redirects disabled, 15-second timeout, 2 MB response cap, XML content-type checks and DTD/entity rejection are enforced.
- The allowlist is a network safety control, not proof of legal authority or source authenticity. Feed items remain observations and are not automatically promoted to verified regulatory guidance or interpreted as legal changes. Polling is manual; scheduled jobs and notifications remain future work.


## Regulatory polling scheduler
- Migration 020 adds per-source last/next poll timestamps, last status and durable poll-run history.
- The one-shot worker is `backend/app/services/regulatory_scheduler.py`. Run from the backend directory with `python -m app.services.regulatory_scheduler`; invoke it periodically using an external scheduler. Each invocation processes at most 25 due RSS sources.
- Row claiming uses PostgreSQL `FOR UPDATE SKIP LOCKED` and advances the next due time before network I/O to reduce duplicate work when scheduler instances overlap. Per-source successes/failures are recorded; failed sources are eligible again at their next configured interval.
- Authenticated reviewer endpoints expose the schedule at GET `/api/v1/regulatory/sources/due` and run history at GET `/api/v1/regulatory/sources/poll-runs`.
- No cron/Kubernetes schedule is installed by this repository change. Operators must provision the recurring invocation and monitor failures. Automated polling still creates unreviewed observations only.


## AI research synthesis citation audit
- The development-only source-constrained synthesis endpoint now checks every emitted citation identifier against the retrieved source allowlist and performs a conservative sentence-level citation-coverage audit.
- The response reports valid identifiers, unknown identifiers, and sentences with no valid citation, with a warning status when coverage is incomplete.
- This is a citation-presence check only. It does not establish that a cited paper semantically supports the sentence, that the retrieved record is relevant, or that a scientific conclusion is correct. Human review of original full-text sources remains mandatory.
- AI synthesis remains disabled by default and is blocked outside development until authenticated access, rate limiting and production security controls are implemented.


## Independent evidence review and decision history
- Migration 021 adds append-only decision records for evidence appraisals and publication duplicate candidates.
- Appraisals awaiting review can be accepted, rejected or marked superseded by a different organization reviewer; the original appraiser cannot approve their own work.
- Duplicate-candidate decisions now preserve the rationale and reviewer identity in a dedicated append-only history table rather than relying only on the candidate's current status.
- Decision history is available through the evidence-intelligence API. Database triggers reject updates and deletes to decision-history rows.
- These controls improve traceability; they do not independently validate scientific conclusions or guarantee reviewer expertise.


## Structured scientific evidence extraction (development pilot)
- Migration 022 adds organization-scoped extraction runs and source-linked extracted evidence records.
- POST `/api/v1/research/assistant/extract` retrieves bounded PubMed, ClinicalTrials.gov, UniProtKB and RCSB records, requests structured extraction, validates output fields and citation IDs, then persists records as `not_reviewed`.
- GET `/api/v1/research/assistant/extractions/{run_id}` retrieves the run and its extracted records within the active organization.
- Extracted fields include study design, evidence class, peptide identity, sequence, modifications, target, mechanism, model/population, sample size, methods, endpoints, findings, limitations, conflicts and extraction notes.
- Unsupported or missing scalar fields remain null; missing list fields remain empty. Source citation IDs must match the retrieved source set. Unsupported classifications are rejected.
- The endpoint is authenticated and organization-scoped but remains development-only while AI synthesis is disabled by default and production authentication/rate-limiting controls are not yet complete.
- These are machine-generated research leads, not verified claims, measured results or scientific conclusions. Review the original source before accepting any extracted field. The current pilot stores one record per source and does not yet provide a field-by-field reviewer workflow.


## Structured scientific evidence extraction and review

- Migration 022 stores source-linked machine-extracted evidence records separately from canonical scientific claims; extraction remains unreviewed by default.
- Development-only authenticated extraction endpoints: POST `/api/v1/research/assistant/extract` and GET `/api/v1/research/assistant/extractions/{run_id}`.
- Migration 023 adds append-only field-level reviewer decisions. Curators, reviewers and organization admins can accept, correct or reject individual fields through POST `/api/v1/research/assistant/extractions/{run_id}/records/{record_id}/fields/{field_name}/review`.
- Field review history is available at GET `/api/v1/research/assistant/extractions/{run_id}/records/{record_id}/history`. Original AI extraction JSON is not overwritten; corrections are separate decision events with reviewer identity and rationale.
- Frontend reviewer workspace: `/evidence-review`. Reviewers sign in and load a run UUID returned by the extraction endpoint.
- Field-level editorial decisions do not automatically promote records into the verified peptide catalogue or canonical evidence claims. Source review and canonical curation remain separate.


### Source-backed vendor candidate intake

Authorized organization contributors can batch-import up to 25 vendor candidates with `POST /api/v1/vendors/import-candidates`. The endpoint requires an HTTPS service/identity source URL and an evidence-scope note for every candidate. Each candidate may include a separate `identity_source` (for example, an official contact or imprint page) so the company reference country and service claim can retain distinct provenance. It creates organization-owned records with `review_status=in_review` and `verification_status=unverified`; these records are not publicly listed until independent curator review. Duplicate official website URLs within the batch or organization are skipped. The endpoint does not create facilities, certifications, or service-capability records from a company-level marketing page.

A starter manifest with five candidates and separate service/identity source records is provided at `data/vendor_candidates/starter_batch_2026-11.json` and served to the authenticated workspace from `frontend/public/vendor-candidates/starter_batch_2026-11.json`. In the vendor directory, an authorized contributor can preview the batch and explicitly import it into the current organization. Each entry is a research candidate supported by the cited official page, not a verified vendor, facility, certification, current inventory, or guarantee of peptide-specific service availability. Curators must verify company identity and source scope before approval; facility, service and certification claims follow their separate review workflows.

Example request:

```bash
curl -X POST "$API_BASE/api/v1/vendors/import-candidates" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @data/vendor_candidates/starter_batch_2026-11.json
```

Facility candidate batch intake: authorized contributors can submit up to 25 source-backed facility candidates for a verified vendor through `POST /api/v1/vendors/{vendor_id}/import-site-candidates`. The endpoint checks parent-vendor ownership, HTTPS source URLs on the official vendor domain, duplicate facility identity, and records each submission as `in_review` with source provenance and audit history. A starter facility manifest is available at `data/vendor_facility_candidates/starter_batch_2026-11.json` and in the vendor workspace. Import is explicit and requires a verified parent vendor; no facility is publicly listed until independent facility review. The starter contains Bachem and CordenPharma site candidates only. Facility claims reflect the scope of the linked official page and do not establish current capacity, availability, certification validity or site-specific regulatory status.

Facility candidate records can include up to five additional official evidence sources when the address, site identity and capability scope are documented on separate pages. These sources are stored as distinct `vendor_site_sources` records with separate evidence-scope notes; the site is not approved merely because multiple URLs are attached. The facility starter manifest includes PolyPeptide Ambernath with a manufacturing-site page for peptide synthesis scope and a separate corporate contacts page for its postal address.
