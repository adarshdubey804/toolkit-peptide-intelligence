# Toolkit Peptide Intelligence

Scientific intelligence for peptide research and pharmaceutical development, built by Toolkit Technologies.

## Current foundation

- Next.js frontend with a peptide directory and scientific profile views.
- FastAPI backend with verified-record catalogue search, pagination, profile detail and readiness endpoints.
- PostgreSQL + pgvector schema for peptide identity, sequences, chemical properties, structures, targets, pathways, publications, research studies, evidence claims, analytical methods, vendor records, certifications and regulatory status.
- Read-only PubMed discovery through NCBI E-utilities. External search results are marked not reviewed and are never silently promoted into curated records.
- GitHub Actions workflows for backend API-contract tests and frontend production builds.

## Local development

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and APP_SECRET_KEY with long, unique random values.
3. Set NCBI_EMAIL to a valid contact email if you want to enable PubMed discovery. NCBI_API_KEY is optional.
4. Run docker compose up --build.
5. Open the frontend at http://localhost:3000, peptide directory at http://localhost:3000/peptides, and API docs at http://localhost:8000/docs.

The development API applies the initial schema on startup. Production deployments must run reviewed, versioned migrations as a separate deployment step.

## API routes

- GET /health — process health.
- GET /ready — database connectivity.
- GET /api/v1/peptides — curator-verified catalogue search. Supports q, category, limit (1–100) and offset.
- GET /api/v1/peptides/{id} — verified profile with reviewed sequences, chemistry, structures and evidence claims.
- GET /api/v1/research/pubmed?q=... — live PubMed discovery, limited to 20 records and requiring NCBI_EMAIL.

## Scientific governance

Every published claim should retain its source identifier/URL, retrieval date, study model, evidence classification, review status, reviewer and limitations. Distinguish measured, calculated, predicted and unverified values. Preserve conflicting evidence. A verified record means editorial review of the record; it does not mean regulatory approval or clinical endorsement.

## Scope and safety

This is an early development scaffold, not production-ready software or a validated pharmaceutical system. The platform is a research-information and workflow product, not a clinical decision system. It does not provide patient-specific diagnosis or treatment, unapproved peptide dosing, material-release decisions or GMP manufacturing execution.

Production use requires managed authentication, authorization, security testing, backups, monitoring, licensing review and qualified scientific/regulatory review. Do not store real secrets in the repository.
