# Peptide workbook audit — 2026-11-03

## Source workbook
- File: `peptides_fda_status_by_treatment.xlsx`
- Worksheets: `Peptides`, `Summary`, `Notes & Sources`
- Peptide worksheet columns: generic/common name, brand/other names, treatment category, primary use/indication, FDA status, status detail, first US approval, notes.
- Data rows: **128**
- Populated names: **128**
- Blank names: **0**
- Duplicate names: **0**

## Workbook status distribution
| Workbook FDA status | Rows |
|---|---:|
| Yes | 88 |
| Previously (withdrawn/discontinued) | 4 |
| No | 36 |
| **Total** | **128** |

## Treatment category distribution
| Category | Rows |
|---|---:|
| Diabetes, Obesity & Metabolic | 21 |
| Infectious Disease | 15 |
| Oncology & Hematology | 11 |
| Immunology, Inflammation & Transplant | 10 |
| Growth Hormone Axis & Body Composition | 10 |
| Diagnostic & Imaging | 9 |
| Endocrine, Pituitary & Bone | 9 |
| Longevity, Mitochondrial & Cosmetic | 7 |
| Cognition, Sleep & Mood | 7 |
| Reproductive Health & Fertility | 6 |
| Cardiovascular & Critical Care | 5 |
| Neurology, Pain & CNS | 4 |
| Gastrointestinal | 4 |
| Dermatology & Sexual Health | 3 |
| Rare & Genetic Disease | 3 |
| Renal & Urologic | 2 |
| Tissue Repair & Recovery | 2 |

## Import and curation rules
1. Treat workbook FDA status and approval dates as **source claims**, not independently verified regulatory facts.
2. Preserve all three worksheets and all original row fields during ingestion.
3. Resolve each row to a canonical substance/entity before attaching sequence, mechanism, chemistry, clinical evidence, or regulatory records.
4. Distinguish peptide drugs from peptide-derived conjugates, radiopharmaceuticals, peptide mixtures, cyclic/lipopeptide antibiotics, peptide/protein boundary cases, and non-peptide entries.
5. Do not infer that an ingredient, brand, salt, conjugate, or research-name synonym has the same approval status as another formulation or product.
6. Populate dossier sections only with traceable evidence. Record claim-level citations (source title, issuing body/database, stable URL, DOI/PMID/registry identifier, locator, evidence type, access date).
7. Mark unknown or unsupported fields as **Not reported** or **Not yet curated**. Do not invent sequence, molecular formula, mechanism, pharmacokinetics, safety, clinical outcomes, or images.
8. Use source-attributed scientific imagery only: PubChem depictions, RCSB PDB experimental structures, AlphaFold predictions clearly labelled as predictions, or properly licensed publication images.

## Current completion boundary
This file records a structural audit of the uploaded workbook. It does **not** claim that 128 dossiers have been scientifically researched, that regulatory claims have been verified, or that records have been imported into a deployed database. Those steps require the actual workbook import execution and evidence-backed curation.
