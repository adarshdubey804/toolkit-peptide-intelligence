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


## IUPHAR/BPS Guide to PHARMACOLOGY (GtoPdb)
- Read-only endpoint: `GET /api/v1/research/gtopdb-peptides?q=...`.
- Searches the expert-curated ligand service for both `Peptide` and `Endogenous peptide` classes and retrieves source-reported ligand interaction records where available.
- These interactions can provide target/action hints for mechanism-of-action research. They remain source-reported evidence and are not automatically promoted to verified MOA records.
- API access requires registration and an API key. Configure `GTOPDB_API_KEY`; the key is sent in the `GTP-API-Key` request header and is never placed in URLs or persisted.
- The source applies an approximate 60 requests/minute rate limit. This adapter limits concurrent ligand interaction lookups to five.
- GtoPdb database data use ODbL and contents use CC BY-SA 4.0. Attribution and share-alike obligations must be assessed before redistributing source data, particularly in commercial deployments.
- Official API and access documentation: https://www.guidetopharmacology.org/webServices.jsp


## DRAMP 5.0 (antimicrobial peptide datasets)
- Read-only endpoint: `GET /api/v1/research/dramp-peptides?q=...`.
- Discovers official FASTA and FASTS download links from the DRAMP downloads page, downloads the non-patent core datasets, and merges records by stable DRAMP identifier.
- Preserves source-reported sequence, dataset category, source release and (where available) SMILES from FASTS annotations. Modified residue symbols in source sequences are not normalized into standard amino acids.
- DRAMP 5.0 reports 32,296 entries and 22,298 sequence/SMILES FASTS annotations. The adapter excludes patent dataset exports pending separate permission; therefore its imported snapshot is not the full 32,296-entry total.
- DRAMP is an antimicrobial-peptide repository, not a complete inventory of all peptide classes or medicines. Activity annotations are not mechanisms of action.
- Non-patent DRAMP data are distributed under CC BY 4.0. Patent AMP downloads are excluded pending separate authorization; retain attribution and release metadata.
- Official downloads and release notes: https://dramp.cpu-bioinfor.org/downloads/ and https://dramp.cpu-bioinfor.org/static/update.php


## European Medicines Agency (EMA) Article 57 public product data
- Read-only endpoint: `GET /api/v1/research/ema-article57?q=...`.
- The adapter downloads the EMA Article 57 XLSX snapshot, searches product name and active substance, and returns source-native product name, active substance, route, country of authorisation and marketing-authorisation holder where present.
- The workbook is cached in-process for six hours; each returned observation records the snapshot retrieval/version metadata and source row locator.
- EMA states that the Article 57 public file contains medicines authorised in the EEA and only products with a valid marketing authorisation are included in the published snapshot. The file is updated periodically.
- A match is **not** a peptide identity assertion. Product-to-peptide linkage and current authorization verification remain curator tasks; the source snapshot is not a replacement for the competent authority's live register.
- The EMA PMS public API beta is deliberately not used by this connector: its published specification describes a limited FHIR R5 dataset, OAuth2 client-credential access and beta/reference-only constraints. Reassess only after EMA's terms and production status permit the intended use.
- Official source: https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/data-medicines-iso-idmp-standards-post-authorisation/public-data-article-57-database.


## DBAASP v4 — experimental antimicrobial peptide evidence
- Read-only search endpoint: `GET /api/v1/research/dbaasp-peptides?q=...`; the source API supports `GET https://dbaasp.org/peptides` and exact record retrieval at `/peptides/{peptideId}`.
- The adapter searches by source name, retrieves bounded detail records, and preserves source IDs, sequence (including source-specific modified symbols), termini, unusual residues, covalent bonds, SMILES, PDB/MD structure references, target activity, antibiofilm activity, hemolytic/cytotoxic measurements, synergy records and publications.
- Assay context is retained as reported: organism/strain, activity measure, value, concentration, unit, medium, pH, ionic strength, salt and reference where available. No values are converted into clinical efficacy or incidence.
- DBAASP v4 covers ribosomal, nonribosomal, synthetic and peptidomimetic antimicrobial records; it is an AMP-focused resource, not a complete inventory of all therapeutic peptides.
- Source combination records may describe a peptide plus antibiotic. They are preserved as source-reported combination observations and are not represented as peptide-peptide synergy. FICI and activity values are not independently reinterpreted by the connector.
- DBAASP's current data policy permits access, copying, adaptation and redistribution with public acknowledgement. Attribution and the current DBAASP citation are retained in every source response and must be included in downstream public materials.
- Official API specification: https://dbaasp.org/v3/api-docs. Usage terms: https://dbaasp.dbaasp.niaidprod.net/terms-and-conditions.
