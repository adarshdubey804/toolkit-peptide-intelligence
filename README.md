# Toolkit Peptide Intelligence

Scientific intelligence for peptide research and pharmaceutical development, built by Toolkit Technologies.

## Current foundation

- Next.js frontend with peptide directory, scientific profile views, interactive knowledge graph and multi-source research workspace and retrieval-only research assistant.
- FastAPI backend with verified-record catalogue search, pagination, profile detail, verified peptide knowledge graph and readiness endpoints.
- PostgreSQL + pgvector schema for peptide identity, sequences, chemical properties, structures, targets, pathways, publications, research studies, evidence claims, analytical methods, vendor records, certifications and regulatory status.
- Read-only discovery integrations: PubMed, ClinicalTrials.gov API v2, UniProtKB, RCSB PDB and PubChem.
- Additive provenance and curation schema: source content hashes and versions, cross-database candidate entity links, review queue and append-only editorial decisions.
- External results remain unreviewed and are never silently promoted into curated records.
- GitHub Actions workflows for backend API-contract tests and frontend production builds.

## Local development

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and APP_SECRET_KEY with long, unique random values.
3. Set NCBI_EMAIL to a valid contact email if you want to enable PubMed discovery. NCBI_API_KEY is optional.
4. Run docker compose up --build.
5. Open the frontend at http://localhost:3000, peptide directory at http://localhost:3000/peptides, knowledge graph at http://localhost:3000/knowledge-graph, research workspace at http://localhost:3000/research, research assistant at http://localhost:3000/research-assistant, and API docs at http://localhost:8000/docs.

Development startup applies all ordered SQL migrations in `database/migrations`. Production deployments must run reviewed, versioned migrations as a separate deployment step.

## API routes

- GET /health — process health.
- GET /ready — database connectivity; returns 503 when unavailable.
- GET /api/v1/peptides — curator-verified catalogue search.
- GET /api/v1/peptides/{id} — verified profile; ID must be a UUID.\n- GET /api/v1/peptides/{id}/graph — curator-verified sequence, target, pathway, structure, claim and publication relationships.
- GET /api/v1/research/workspace?q=... — parallel discovery across PubMed, ClinicalTrials.gov, UniProtKB and RCSB PDB; each source reports its own availability.\n- GET /api/v1/research/assistant/brief?question=... — source-grounded evidence retrieval brief with original-record citations and explicit limitations; not generative AI.\n- GET /api/v1/research/pubmed?q=... — PubMed discovery; requires NCBI_EMAIL.
- GET /api/v1/research/clinicaltrials?q=... — ClinicalTrials.gov study discovery.
- GET /api/v1/research/uniprot?q=... — UniProtKB protein discovery.
- GET /api/v1/research/rcsb?q=... — RCSB PDB structure discovery.
- GET /api/v1/research/pubchem?name=... — PubChem compound-property lookup.

External research results remain unreviewed. PubChem compound identity must be checked carefully before linking properties to peptide records.

## Scientific governance and safety

Every claim should retain source provenance, study model, evidence classification, limitations and review history. Distinguish measured, calculated, predicted and unverified values; preserve conflicting evidence. The platform is a research-information product, not a clinical decision system. It does not provide patient-specific diagnosis or treatment, unapproved peptide dosing, material-release decisions or GMP manufacturing execution.

This is an early development scaffold, not production-ready software. Production use requires managed authentication, authorization, security testing, backups, monitoring, licensing review and qualified scientific/regulatory review. Do not store real secrets in the repository.
