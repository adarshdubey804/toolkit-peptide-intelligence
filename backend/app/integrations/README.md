# External research integrations

All integrations are read-only discovery clients. Results returned from external registries are source-attributed and marked `curation_status=not_reviewed`; they must not be silently promoted into curated scientific records.

## PubMed
- NCBI E-utilities ESearch and ESummary.
- Configure `NCBI_EMAIL`; `NCBI_API_KEY` is optional.
- API: `GET /api/v1/research/pubmed?q=...`.

## ClinicalTrials.gov
- ClinicalTrials.gov REST API v2: `GET https://clinicaltrials.gov/api/v2/studies`.
- No API key is required for public study search.
- API: `GET /api/v1/research/clinicaltrials?q=...`; optional `page_token` follows the registry cursor.

## UniProtKB
- UniProt REST API: `GET https://rest.uniprot.org/uniprotkb/search`.
- Search returns accession, protein/gene names, organism, reviewed status and sequence length.
- API: `GET /api/v1/research/uniprot?q=...`.

## RCSB Protein Data Bank
- RCSB Search API v2 plus Data API entry detail.
- Search results are capped at 20; each returned entry includes PDB identifier, title, experimental method and deposit date where available.
- API: `GET /api/v1/research/rcsb?q=...`.

## PubChem
- PubChem PUG REST compound-name property lookup.
- Resolves a chemical name to CID, formula, molecular weight, SMILES, InChI and InChIKey where available.
- API: `GET /api/v1/research/pubchem?name=...`.
- A PubChem compound is not necessarily identical to a biologically active peptide entity, salt, conjugate or formulation. Confirm identity and chemical form before linking properties to a peptide profile.


## FDA Drugs@FDA via openFDA
- Read-only endpoint: `GET /api/v1/research/fda-drugsfda?q=...`.
- Searches the Drugs@FDA application dataset by active ingredient and preserves application, per-product strength/form/route/marketing status, and submission actions separately.
- Optional `OPENFDA_API_KEY` improves operational reliability for regular usage; public API access does not require a key.
- This dataset covers most FDA-approved human drug products but not every CBER-regulated biological product and does not include non-approved products. A missing result is not evidence of non-approval.
- FDA application/submission status must be reviewed at the exact product and application level before creating a regulatory authorization record.

## DailyMed Structured Product Labels
- Read-only endpoint: `GET /api/v1/research/dailymed?q=...` with bounded page size and pagination.
- Uses NLM DailyMed SPL v2 search and returns label Set ID, version, title, published date and stable source links.
- DailyMed provides current SPL information. Current SPL content is not necessarily identical to the last FDA-approved labeling in Drugs@FDA. DailyMed presence is not itself proof of FDA approval.
- Use the exact SPL version and label section when curating mechanism-of-action evidence; retain label publication/version history.
- Mechanism extraction endpoint: `GET /api/v1/research/dailymed/{set_id}/mechanism-of-action`; discovery ingestion also extracts the explicit SPL 12.1 section when available.
- Only LOINC `43679-0` (12.1 Mechanism of Action) is extracted. 12.2 pharmacodynamics and 12.3 pharmacokinetics are not used as substitutes. Extracted text remains `source_asserted` until the exact product and approval label are curator-verified.

## Regulatory interpretation
- FDA Drugs@FDA, FDA Purple Book, FDA labeling resources and DailyMed answer different questions and have different coverage. They are complementary, not interchangeable.
- External search results remain `not_reviewed`; no provider automatically creates or verifies a peptide, product authorization or mechanism claim.


## Health Canada Drug Product Database (DPD)
- Read-only endpoint: `GET /api/v1/research/health-canada-dpd?q=...`.
- Searches the official DPD active-ingredient endpoint and enriches returned drug product codes with product, source status, dosage form and route records.
- Preserves Canadian DIN, brand, company, ingredient/strength and source status. DPD status codes distinguish approved, marketed, dormant and multiple cancelled/interim-order states.
- DPD includes human pharmaceutical and biological products, as well as veterinary, radiopharmaceutical and disinfectant classes; filter and review the product class before treating a result as a human peptide medicine.
- An empty ingredient search is not proof of non-authorization or absence of a peptide. All returned products remain `not_reviewed` until matched to a canonical peptide identity and exact chemical form.
- Official API documentation: https://health-products.canada.ca/api/documentation/dpd-documentation-en.html

## European Medicines Agency (EMA) Product Management Service (PMS)
- The public PMS API exposes a limited FHIR R5 dataset for human medicinal products, including provisional/current records; it excludes nullified products and some confidential fields.
- API access requires prior registration and OAuth2 credentials. The connector is planned but must not be activated until credentials, data terms and supported FHIR resource scopes are configured.
- Official API documentation: https://api.pms.ema.europa.eu/public/v1/swagger


## FDA Purple Book
- Read-only endpoint: `GET /api/v1/research/fda-purple-book?q=...`.
- Discovers the latest monthly CSV from the official FDA Purple Book downloads page and parses the complete product snapshot (the second/full table, not only monthly change rows).
- Preserves BLA number, product number, proper/proprietary names, applicant, license type, strength, dosage form, route, marketing status, licensure and reference-product fields.
- The Purple Book covers FDA-licensed biological products regulated by CDER and CBER, including reference products and biosimilars. It complements Drugs@FDA and is not interchangeable with it.
- A Purple Book match does not establish that the matched biological product is a peptide. Candidate identity remains unresolved until curator review.
- Official downloads: https://purplebooksearch.fda.gov/downloads
