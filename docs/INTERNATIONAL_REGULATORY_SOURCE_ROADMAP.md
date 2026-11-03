# International regulatory source integration roadmap

| Jurisdiction | Source | Access mode | Coverage and limitations | Integration status |
|---|---|---|---|---|
| United States | FDA Drugs@FDA / openFDA | Public API | Most FDA-approved human drug products; does not cover every CBER-regulated biologic or unapproved research candidate | Integrated read-only discovery |
| United States | NLM DailyMed SPL | Public API | Current structured labels and versions; SPL presence is not proof of FDA approval and may differ from last FDA-approved label | Integrated read-only discovery |
| United States | FDA Purple Book | Monthly downloadable CSV/XLSX | Biological products licensed under the PHS Act, including reference products, biosimilars and interchangeable products; data must be reconciled with Drugs@FDA and exact biologic identifiers | Planned batch importer; not a live API |
| Canada | Health Canada Drug Product Database | Public JSON/XML API | Product-specific DINs and approved, marketed, dormant and cancelled statuses; includes human and non-human product classes | Integrated read-only discovery |
| European Union | EMA Product Management Service (PMS) public API | FHIR R5 API with prior registration and OAuth2 | Limited public subset of non-nullified human medicinal products; current/provisional status scope and confidential-field exclusions | Planned; credentials and access scope required |
| European Union | EMA ePI pilot API | Public API for published pilot product information | Published electronic product information pilot; not a complete register of all EU products | Planned source evaluation |
| International | ClinicalTrials.gov | Public API | Registered study records, not regulatory approval or proof of efficacy | Existing integration |
| International | PubMed | Public NCBI E-utilities | Literature discovery, not regulatory status | Existing integration |

## Source interpretation rules

1. Each source record is jurisdiction-specific, source-specific and time-stamped.
2. Preserve source-native identifiers and original status terms. Normalize into an internal status only with a versioned mapping and documented rationale.
3. Do not treat a product label, clinical trial, database search result or sponsor statement as interchangeable evidence.
4. Regulatory approval belongs to an exact product, active ingredient, chemical form, strength, dosage form, route, indication, jurisdiction and effective period.
5. A source omission or search miss is recorded as `not_found_in_checked_sources` for that source/query/date, never as global non-approval.
6. Distinguish authorization from marketed availability. A product can remain authorized while dormant or cancelled after marketing.
7. The same peptide may have multiple products, applications, labels, indications and jurisdictional statuses. Store each independently and link them to a canonical peptide only after identity review.

## Operational ingestion

- Use provider adapters with bounded queries, timeouts, retry/backoff and rate limits.
- Persist the original response payload and source locator before extraction.
- Hash normalized payloads for duplicate suppression; preserve every changed observation.
- Compare source versions and create change events; never overwrite previous regulatory observations.
- Run entity resolution as a candidate process. Ambiguous identity must go to a review queue.
- Keep source polling health, last successful retrieval, page/pagination completeness and known coverage exclusions visible.
- Do not infer worldwide coverage from a subset of national sources.
