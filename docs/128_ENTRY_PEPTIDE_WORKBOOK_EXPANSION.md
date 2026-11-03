# 128-entry peptide workbook expansion

## Input inventory
The user-provided workbook `peptides_fda_status_by_treatment.xlsx` contains 128 rows on the `Peptides` sheet, plus a summary sheet and notes/sources sheet. The workbook is a discovery seed, not a regulator-verified dataset.

## Required record model
Each row must resolve to a stable peptide dossier UUID, presented as an independently editable virtual folder. Do not create one physical source-code directory per peptide; the database dossier is the source of truth and the UI folder is a navigable view.

Each dossier should expose independently editable sections:
1. Identity: preferred name, aliases, peptide class, source identifiers, canonicalization and identity confidence.
2. Sequence: amino-acid sequence, sequence notation, residue stereochemistry, noncanonical residues, termini, cyclization and modifications.
3. Chemical forms: salts/counterions, conjugates, molecular formula, average and monoisotopic mass, SMILES, InChI and InChIKey, with provenance and calculation method.
4. Product and regulatory status: exact product, active ingredient, dosage form, strength, route, indication, application/authorization identifier, authority, jurisdiction, approval/effective/withdrawal dates and official label/source.
5. Mechanism of action: mechanism statement, target and target action, binding/interaction, downstream signalling, pathways, biological effect, tissue/species context, evidence level, limitations and source locator.
6. Pharmacology/PK: receptor pharmacology, potency/affinity when reported, absorption, distribution, metabolism, elimination, half-life and exposure context.
7. Clinical evidence: trial registry identifiers, phase, design, population, intervention, comparator, endpoints, results and limitations.
8. Preclinical evidence: model, species, dose/exposure as reported, outcomes, methods and limitations.
9. Safety: adverse events, contraindications, warnings, immunogenicity, toxicology and route/form-specific risks.
10. Formulation and stability: dosage form, excipients, compatibility, storage, stability-indicating evidence and packaging.
11. Analytical and manufacturing: identity, purity, potency, impurities, assay methods, specifications, process controls and batch evidence.
12. Literature and patents: DOI, PMID, PMCID, patent identifiers, exact source URLs, excerpts/locators, publication type and evidence appraisal.
13. Provenance and audit: original source payload, retrieval time, content hash, reviewer, immutable revisions and change history.

## Import rules
- Import all 128 workbook rows as source-specific discovery observations first.
- Preserve every workbook field verbatim, including brand/other names, treatment category, indication, reported FDA status, status detail, first US approval and notes.
- Keep all rows in a review queue until identity resolution and independent source verification are complete.
- Never convert a workbook's `FDA Approved?` value directly into a verified regulatory authorization or a global approved/not-approved flag.
- Distinguish FDA marketing authorization from compounding policy, withdrawn nominations, discontinued products and investigational/research status.
- Resolve duplicate names and salts/forms conservatively. Name similarity alone must not merge entities.
- Missing sequence, chemistry, MOA, PK, clinical, safety or manufacturing data must display as `Not yet curated`, not as a negative scientific finding.
- Mechanism statements must be source-linked and evidence-graded. Separate label-supported human pharmacology from clinical outcome evidence, animal, in-vitro, computational and review-derived hypotheses.
- Every section must support revision history and source provenance; one peptide's edits must not alter another peptide.

## Acceptance criteria
- Exactly 128 workbook rows are accounted for, with a stable import identifier for each.
- Re-running the import is idempotent and creates no duplicate source observations.
- Each row opens its own editable dossier workspace.
- Source claims remain distinct from curator-verified facts.
- FDA status is product-, indication-, authority- and jurisdiction-specific.
- Dossier sections show evidence gaps explicitly.
- Automated tests cover import count, idempotency, provenance, identity separation and regulatory non-promotion.
- UI and API tests verify that edits are scoped to the selected dossier.
