# Toolkit Peptide Intelligence

Scientific intelligence for peptide research and pharmaceutical development, built by Toolkit Technologies.

## Current foundation

- Next.js frontend with peptide directory, scientific profile views, interactive knowledge graph and multi-source research workspace and retrieval-only research assistant.
- FastAPI backend with JWT authentication, organization registration, membership-based roles, organization-scoped research projects, scientific review submission/assignment/decision APIs, append-only curation decisions, researcher profiles, verified-record catalogue search, pagination, profile detail, verified peptide knowledge graph and readiness endpoints.
- PostgreSQL + pgvector schema for peptide identity, sequences, chemical properties, structures, targets, pathways, publications, research studies, evidence claims, analytical methods, vendor records, certifications and regulatory status.
- Read-only discovery integrations with PubMed abstract retrieval: PubMed, ClinicalTrials.gov API v2, UniProtKB, RCSB PDB and PubChem.
- Additive provenance and curation schema: source content hashes and versions, cross-database candidate entity links, review queue and append-only editorial decisions.
- External results remain unreviewed and are never silently promoted into curated records.
- GitHub Actions workflows for backend API-contract tests and frontend production builds.

## Local development

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and APP_SECRET_KEY with long, unique random values.
3. Set NCBI_EMAIL to a valid contact email if you want to enable PubMed discovery. NCBI_API_KEY is optional.
4. AI synthesis is opt-in for local development only: set AI_SYNTHESIS_ENABLED=true, AI_API_KEY, and AI_MODEL. Never expose provider keys to the frontend. The synthesis route is deliberately blocked outside development until authenticated access and rate limiting are implemented.
5. Run docker compose up --build.
6. Open the frontend at http://localhost:3000, peptide directory at http://localhost:3000/peptides, knowledge graph at http://localhost:3000/knowledge-graph, research workspace at http://localhost:3000/research, research assistant at http://localhost:3000/research-assistant, vendor directory at http://localhost:3000/vendors, analytical method catalogue at http://localhost:3000/analytical-methods, formulation intelligence at http://localhost:3000/formulations, process intelligence at http://localhost:3000/process-knowledge, bioinformatics at http://localhost:3000/bioinformatics, structure intelligence at http://localhost:3000/structures, interaction intelligence at http://localhost:3000/interactions, and API docs at http://localhost:8000/docs.

Development startup applies all ordered SQL migrations in `database/migrations`.

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

Organization workspace endpoints include `GET /api/v1/organizations/me`, `GET /api/v1/organizations/members`, `PATCH /api/v1/organizations/members/{user_id}/role`, `POST /api/v1/organizations/projects` and `GET /api/v1/organizations/projects`. Membership roles are organization_admin, curator, reviewer, researcher and viewer. Project visibility is organization-wide or private; private projects are visible only to their creator or explicitly assigned project members. Membership and project access is scoped to the caller's active organization.

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
- Vendor directory: GET/POST `/api/v1/vendors`, POST `/api/v1/vendors/{id}/services`, POST `/api/v1/vendors/{id}/certifications`, GET `/api/v1/vendors/reviews`, POST `/api/v1/vendors/{id}/decisions`. Migration 007 adds vendor source provenance and append-only vendor review decisions. Public directory shows only curator-reviewed, verified vendor identities.
- GET /api/v1/research/workspace?q=... — parallel discovery across PubMed, ClinicalTrials.gov, UniProtKB and RCSB PDB; each source reports its own availability.
- GET /api/v1/research/assistant/brief?question=... — source-grounded evidence retrieval brief with original-record citations and explicit limitations; retrieval-only.
- POST /api/v1/research/assistant/synthesize — optional development-only AI synthesis over server-retrieved records; disabled by default and blocked outside development pending authentication and rate limiting.
- GET /api/v1/research/pubmed?q=... — PubMed discovery; requires NCBI_EMAIL.
- GET /api/v1/research/clinicaltrials?q=... — ClinicalTrials.gov study discovery.
- GET /api/v1/research/uniprot?q=... — UniProtKB protein discovery.
- GET /api/v1/research/rcsb?q=... — RCSB PDB structure discovery.
- GET /api/v1/research/pubchem?name=... — PubChem compound-property lookup.

External research results remain unreviewed. PubChem compound identity must be checked carefully before linking properties to peptide records.

- Peptide knowledge graph: GET `/api/v1/peptides/{peptide_id}/graph` returns curator-verified connections across sequences, structures, targets, pathways, evidence claims, publications, analytical methods, formulation/stability observations, process knowledge, molecular interaction assessments and accepted evidence appraisals. GET `/api/v1/peptides/{peptide_id}/graph/related` discovers other verified peptides sharing curator-verified targets or pathways. The `/knowledge-graph` workspace supports evidence-type filtering and related-peptide exploration. Shared associations are not proof of equivalent mechanism or clinical interchangeability.\n\n## Scientific governance and safety

Every claim should retain source provenance, study model, evidence classification, limitations and review history. Distinguish measured, calculated, predicted and unverified values; preserve conflicting evidence. The platform is a research-information product, not a clinical decision system. It does not provide patient-specific diagnosis or treatment, unapproved peptide dosing, material-release decisions or GMP manufacturing execution.

This is an early development scaffold, not production-ready software. Production use requires managed authentication, authorization, security testing, backups, monitoring, licensing review and qualified scientific/regulatory review. Do not store real secrets in the repository.
