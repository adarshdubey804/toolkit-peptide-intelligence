# External research integrations

All integrations are read-only discovery clients. Results returned from external registries are source-attributed and marked `curation_status=not_reviewed`; they must not be silently promoted into curated scientific records.

## PubMed

- NCBI E-utilities ESearch and ESummary.
- Configure `NCBI_EMAIL`; `NCBI_API_KEY` is optional.
- API: `GET /api/v1/research/pubmed?q=...`.

## ClinicalTrials.gov

- ClinicalTrials.gov REST API v2, `GET https://clinicaltrials.gov/api/v2/studies`.
- No API key is required for the public API.
- Search uses `query.term`; pagination is cursor-based using `nextPageToken` / `pageToken`.
- API: `GET /api/v1/research/clinicaltrials?q=...`; optional `page_token` continues the same query.
- Returned trial summaries preserve NCT identifiers and link to the registry record. Results remain unreviewed external records.
