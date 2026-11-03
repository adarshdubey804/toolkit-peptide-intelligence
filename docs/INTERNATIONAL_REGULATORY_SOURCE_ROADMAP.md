# International regulatory source integration roadmap

| Jurisdiction | Source | Access mode | Coverage and limitations | Integration status |
|---|---|---|---|---|
| United States | FDA Drugs@FDA / openFDA | Public API | Most FDA-approved human drug products; does not cover every CBER-regulated biologic or unapproved research candidate | Integrated read-only discovery |
| United States | NLM DailyMed SPL | Public API | Current structured labels and versions; SPL presence is not proof of FDA approval and may differ from last FDA-approved label | Integrated read-only discovery |
| United States | FDA Purple Book | Monthly downloadable source snapshot | Biological products licensed under the PHS Act, including reference products, biosimilars and interchangeable products; reconcile exact BLA and product identifiers with Drugs@FDA | Integrated read-only snapshot importer; not a live API |
| Canada | Health Canada Drug Product Database | Public JSON/XML API | Product-specific DINs and approved, marketed, dormant and cancelled statuses; includes human and non-human product classes | Integrated read-only discovery |
| European Union | EMA Article 57 product snapshot | Public XLSX snapshot | Products with valid marketing authorisations in the EEA at the snapshot date; active substance, route, country and holder fields where published | Integrated read-only snapshot importer |
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


## EMA / European Economic Area

### Article 57 public product snapshot — implementable public source
- Public XLSX: `https://www.ema.europa.eu/en/documents/other/article-57-product-data_en.xlsx`
- Official scope: products with valid marketing authorisations in the EEA at the time represented by the snapshot.
- Available fields include product name, active substance, route, authorisation country and marketing authorisation holder.
- The platform imports this as a source snapshot observation. It must not infer peptide identity from a name match or treat a snapshot row as a current, country-by-country regulatory decision without checking the relevant national authority.
- The source publishes only products with valid authorisations; therefore it cannot establish the identity or status of withdrawn, refused, investigational or never-authorised peptide candidates.

### EMA PMS Public API beta — deferred
- The public beta exposes selected FHIR R5 product data but is explicitly a beta service. Its API specification describes OAuth2 client-credential access; EMA terms and beta limitations must be reviewed before use.
- The platform will not use beta/reference-only data as a production authorization source or for commercial purposes unless EMA's current terms explicitly permit that use.

## Additional scientific discovery sources

| Domain | Source | Access mode | Coverage and limitations | Integration status |
|---|---|---|---|---|
| International | IUPHAR/BPS Guide to PHARMACOLOGY | Registered API key | Expert-curated peptide ligands, pharmacological targets and interaction types; ODbL database and CC BY-SA 4.0 content obligations apply | Integrated read-only discovery; API key required |
| International | DBAASP v4 | Public API | Antimicrobial peptide sequences, modifications, activity assays, cytotoxicity, combination observations and references; domain-specific rather than comprehensive | Integrated read-only discovery |
| International | DRAMP 5.0 | Published downloadable datasets | Curated antimicrobial peptide sequence and selected SMILES datasets; patent exports excluded pending separate permission | Integrated read-only snapshot discovery |
| International | UniProt | Public API | Protein sequences and functional annotations; protein records do not automatically identify a therapeutic peptide product | Existing integration |
| International | RCSB Protein Data Bank | Public API | Structural records and macromolecular entities; construct and sequence identity require review | Existing integration |
| International | PubChem | Public API | Chemical identifiers and structures; name similarity does not establish peptide identity | Existing integration |
| International | Antimicrobial Peptide Database (APD6) | External link-out | Specialist antimicrobial peptide research resource | Link-out only; no bulk ingestion |

The platform's source coverage catalogue is available at `/source-coverage`. It lists integrated sources, access modes, coverage boundaries and known limitations. This catalogue must be updated in the same pull request that changes an adapter's production status.
