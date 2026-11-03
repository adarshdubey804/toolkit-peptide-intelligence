# International regulatory source integration roadmap

| Jurisdiction | Source | Access mode | Coverage and limitations | Integration status |
|---|---|---|---|---|
| United States | FDA Drugs@FDA / openFDA | Public API | Most FDA-approved human drug products; does not cover every CBER-regulated biologic or unapproved research candidate | Integrated read-only discovery |
| United States | NLM DailyMed SPL | Public API | Current structured labels and versions; SPL presence is not proof of FDA approval and may differ from last FDA-approved label | Integrated read-only discovery |
| United States | FDA Purple Book | Monthly downloadable source snapshot | Biological products licensed under the PHS Act, including reference products, biosimilars and interchangeable products; reconcile exact BLA and product identifiers with Drugs@FDA | Integrated read-only snapshot importer; not a live API |
| Canada | Health Canada Drug Product Database | Public JSON/XML API | Product-specific DINs and approved, marketed, dormant and cancelled statuses; includes human and non-human product classes | Integrated read-only discovery |
| India | CDSCO approved drugs / SUGAM | Official web search portal and published PDF approval lists | CDSCO publishes approved drug/vaccine/rDNA/blood-product search records and annual/new-drug approval lists; available fields vary by record and publication | Official link-out only; automated ingestion pending API, completeness and licensing assessment |
| United Kingdom | MHRA Products | Official public product information search | Nationally licensed medicine information, active-substance and Product Licence search, SPCs, PILs and selected assessment reports; EMA centrally authorised products are a separate source scope | Official link-out only; automated ingestion not integrated |
| Australia | TGA Australian Register of Therapeutic Goods (ARTG) | Official public search | Public register for therapeutic goods that may legally be supplied in Australia; product/formulation and sponsor/manufacturer details where published; exemptions exist | Official link-out only; automated ingestion not integrated |
| Japan | PMDA approved-product lists and product information search | Official public lists and search | Published approved drug product lists, selected review reports and Japanese product information; English translations are selective | Official link-out only; automated ingestion not integrated |
| China | NMPA information-center drug product databases | Official Chinese-language data query portal and published records | Domestic and imported drug product databases; source documentation describes approval/registration numbers, product names, dosage forms, specifications, holders/manufacturers and approval dates | Official link-out only; automated ingestion not integrated |
| China | NMPA Center for Drug Evaluation (CDE) | Official Chinese-language public information portal | Accepted drug applications, review-task disclosures, clinical-trial implied permissions, breakthrough-therapy and priority-review designations, conditional approvals and marketed-drug information | Official link-out only; automated ingestion not integrated |
| Singapore | HSA Register of Therapeutic Products | Official Infosearch and government open-data CSV listing | Product name, licence number, active ingredients, dosage form, route, manufacturer, country of origin, approval date and classification where published; post-registration actions require checking HSA | Official link-out only; automated ingestion not integrated |
| South Korea | MFDS Drug Safety Nara | Official English/Korean public product information and review portal | Product approval information, drug information search, review results and safety/product information | Official link-out only; automated ingestion not integrated |
| Brazil | ANVISA medicine registration consultation | Official Portuguese-language public search | Registered medicines and simplified-notification medicines; ANVISA also regulates biological products and clinical trials | Official link-out only; automated ingestion not integrated |
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

## Priority national authority evaluation queue

The following jurisdictions are priority gaps. They are not production integrations yet; the platform must not imply that their product registers have been queried.

| Jurisdiction | Authority / source family | Evaluation required before integration |
|---|---|---|
| India | CDSCO official approved-drug search, SUGAM and new-drug approval lists | Confirm a documented public API or permitted snapshot-ingestion route; assess searchable portal fields, historical completeness, stable product identifiers and status semantics. Official source links are available, but automated ingestion is not yet integrated |
| United Kingdom | MHRA Products | Official product information link-out is available; evaluate documented bulk/API access, status history, product identifiers and licence terms before ingestion |
| Australia | TGA ARTG | Official public search link-out is available; evaluate permitted export/API access, biologic/peptide coverage, ARTG identifiers and status history before ingestion |
| Japan | PMDA approved-product lists and product information search | Official link-outs are available; evaluate bulk/API access, Japanese/English reconciliation, approval identifiers, product forms and historical status before ingestion |
| China | NMPA information-center drug product databases | Official link-out available; evaluate permitted query/export access, CAPTCHA and access controls, Chinese-language normalization, stable identifiers, status history and update cadence before ingestion |

For every new jurisdiction, an adapter is accepted only after it has: (1) a source-access and licence assessment; (2) a documented source-native schema/status map; (3) pagination/completeness checks; (4) source retrieval timestamps and payload hashes; (5) normalization and identity tests; (6) failure/retry tests; and (7) explicit no-result and ambiguity semantics. A national source being absent from the integration list is not evidence that no peptide products are authorised there.

### India — CDSCO official source access (link-out stage)
- CDSCO's official SUGAM approved-drug search portal: `https://cdscoonline.gov.in/CDSCO/cdscoDrugs`.
- CDSCO's official published "List of Approved New Drugs": `https://cdsco.gov.in/opencms/en/Approval_new/Approved-New-Drugs/`.
- The portal presents search fields for drug, manufacturer, indication and drug type; published records can include composition, dosage, indication, manufacturer and approval date. The official public page does not document a supported open API in the material reviewed for this integration.
- Current platform status is link-out only. Do not automate access to authenticated SUGAM workflows, infer complete national coverage from visible search results, or treat the absence of a search result as proof of non-approval.

### United Kingdom — MHRA Products (link-out stage)
- Official search: `https://products.mhra.gov.uk/`.
- The service provides national UK medicine product information searchable by product, active substance or Product Licence number, including SPCs, PILs and selected Public Assessment Reports.
- MHRA states that this service covers nationally licensed medicines; centrally authorised products are a separate EMA scope. Product information may remain visible for a period after marketing authorisation cancellation.
- Current platform status: link-out only. Do not infer current authorisation solely from a historical product-information page.

### Australia — TGA ARTG (link-out stage)
- Official ARTG information and search instructions: `https://www.tga.gov.au/products/regulations-all-products/about-australian-register-therapeutic-goods-artg/searching-australian-register-therapeutic-goods-artg`.
- TGA describes ARTG as the public database of therapeutic goods that can be legally supplied in Australia and identifies product/formulation, sponsor and manufacturer information among its fields.
- Exempt therapeutic goods may not need ARTG inclusion. Therefore, ARTG absence is not a universal statement that a therapeutic good cannot be supplied.
- Current platform status: link-out only; automated ingestion requires access, licence and completeness review.

### Japan — PMDA approved products (link-out stage)
- PMDA English approved drug product lists: `https://www.pmda.go.jp/english/review-services/reviews/approved-information/drugs/0002.html`.
- PMDA Japanese product information search: `https://www.pmda.go.jp/PmdaSearch/iyakuSearch/`.
- PMDA publishes approved-product lists and product information; English review reports are selective translations and Japanese originals prevail if translations differ.
- Current platform status: link-out only; automated ingestion requires bilingual normalization, product identifier mapping and source-status review.

### China — NMPA drug product databases (link-out stage)
- Official NMPA Information Center: `https://www.nmpaic.org.cn/`.
- Official NMPA public service window: `https://www.nmpa.gov.cn/zwfwqjd/index.html`.
- NMPA's drug base-code guidance describes separate domestic and imported drug databases and fields such as approval/registration number, product name, dosage form, specification, marketing authorisation holder/manufacturer, approval date and validity information.
- Current platform status: link-out only. The public query workflow, language normalization, CAPTCHA/access controls and historical status completeness have not been validated for automated ingestion.

### China — NMPA Center for Drug Evaluation (CDE) (link-out stage)
- Official CDE portal: `https://www.cde.org.cn/`.
- CDE publicly exposes accepted product applications, review-task information, clinical-trial implied permissions, breakthrough-therapy and priority-review designations, conditional approvals and marketed-drug information.
- These states represent different regulatory/development milestones. An accepted application, clinical-trial implied permission or designation is not a marketing authorisation.
- Current platform status: link-out only; automated ingestion requires source-native status mapping, Chinese-language normalization, stable identifiers and historical change coverage.

### Singapore — HSA Register of Therapeutic Products (link-out stage)
- Official HSA Infosearch: `https://www.hsa.gov.sg/e-services/infosearch/`.
- HSA's official data.gov.sg listing provides product name, licence number, active ingredients, dosage form, manufacturer, country of origin, approval date and classification fields; the published listing is updated periodically.
- Check HSA Infosearch for current registration and post-registration actions such as transfers, cancellations and recalls.
- Current platform status: link-out only; automated ingestion and status history are not integrated.

### South Korea — MFDS Drug Safety Nara (link-out stage)
- Official English portal: `https://nedrug.mfds.go.kr/eng/index`.
- The portal exposes drug information search, approval information and review-result functions. Korean-language records may contain more complete information than English views.
- Current platform status: link-out only; bilingual normalization, stable identifiers and historical status reconciliation are not integrated.

### Brazil — ANVISA medicine registration (link-out stage)
- Official medicine registration consultation: `https://www.gov.br/anvisa/pt-br/sistemas/consulta-a-registro-de-medicamentos`.
- ANVISA's regulatory scope includes medicines and biological products and authorisation of clinical trials in Brazil.
- Current platform status: link-out only; Portuguese-language normalization, product identifiers and regulatory status history are not integrated.
