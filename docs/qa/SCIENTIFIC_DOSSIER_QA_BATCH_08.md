# Scientific Dossier QA — Batch 08

**Scope:** 10 additional dossier READMEs screened on PR #155.
**Files reviewed:** insulin glargine, insulin glulisine, recombinant human insulin, insulin lispro, ipamorelin, kisspeptin-10, KPV, lanreotide, larazotide, and leuprolide.
**Method:** text-level structured review of identity, chemistry, mechanism, evidence grading, product boundaries and regulatory claims. This is not independent verification of every claim against current primary sources or regulator databases.

## Executive findings

- The insulin records correctly distinguish several analogues and products, but full chain sequences, disulfide maps and product-specific label extraction remain incomplete.
- Ipamorelin is a strong example of evidence-aware curation: investigational status, a non-significant primary endpoint in a small phase 2 study, and FDA compounding safety concerns are clearly distinguished from online promotional claims.
- Kisspeptin-10, KPV and larazotide are appropriately treated as investigational/research entities, with target or efficacy uncertainty stated rather than overstated.
- Lanreotide and leuprolide require product-level modelling because depot technologies, routes, indications and labels differ across brands and presentations.
- Continue treating all dossiers as in_progress.

## Dossier-level findings and actions

### 1. Insulin glargine
- Correctly records A21G substitution and addition of ArgB31/ArgB32, plus the acidic Lantus solution / subcutaneous microprecipitation mechanism.
- Full A/B-chain sequence and disulfide connectivity still need authoritative validation.
- Lantus, Toujeo, Basaglar and Semglee must be distinct medicinal-product records; concentration, formulation, device, PK, excipients and approval history must not be copied across brands.
- Extract complete current label safety, interaction, special-population, storage and trial evidence.

### 2. Insulin glulisine
- Correctly records AsnB3Lys and LysB29Glu substitutions and insulin-receptor mechanism.
- Verify full chain sequence and disulfide map before structured sequence import.
- Apidra device, pump compatibility, presentation, excipients and PK must be label-version-specific.
- Complete quantitative PK with study conditions, safety frequencies, interaction matrix and pivotal trial references.

### 3. Recombinant human insulin
- Correctly treats the workbook row as a class-level active-substance entry and distinguishes it from individual insulin analogues.
- Do not attach Humulin R product-specific formula, excipients, PK or 1982 approval date to every recombinant insulin product.
- Model human insulin as two chains with explicit inter- and intra-chain disulfides; separate regular insulin, NPH, premixes, concentrations and devices at product/formulation level.
- Add product-specific records for brands and presentations represented in the workbook.

### 4. Insulin lispro
- Correctly identifies the B28/B29 residue exchange and insulin-receptor mechanism.
- Validate complete chain sequences and disulfide connectivity from an authoritative record.
- Humalog, Admelog and Lyumjev are not interchangeable product records; formulation-dependent onset, administration timing, concentration and devices require separate labels.
- Complete current label PK, safety, interaction, special-population and clinical trial evidence.

### 5. Ipamorelin
- Strong evidence discipline: GHSR1a agonism and GH release are distinguished from unproven bodybuilding, fat-loss and anti-ageing claims.
- The phase 2 postoperative-ileus study is correctly described as proof-of-concept with a non-statistically significant primary endpoint; verify the full publication, registry history and safety tables before final curation.
- FDA compounding concerns must be tied to the exact current Category 2 / PCAC source and date. Do not imply FDA approval or that every reported serious event was causally attributable to ipamorelin.
- Preserve Aib, D-residues, D-2-Nal and C-terminal lysinamide in a stereochemistry-aware residue model; a conventional one-letter sequence is inadequate.
- Keep free peptide and acetate salt as distinct chemical forms.

### 6. Kisspeptin-10
- Correctly distinguishes KP-10 from KP-54 and longer endogenous kisspeptins; the C-terminal amide and KISS1R/GPR54 pathway are important identity features.
- Verify exact sequence, stereochemistry and terminal amidation from primary chemistry sources.
- Separate human pharmacodynamic LH/FSH responses from fertility outcomes such as pregnancy and live birth.
- Human PK and safety evidence remain heterogeneous; do not transfer KP-54 values to KP-10.

### 7. KPV
- Correctly identifies KPV as the C-terminal tripeptide motif of alpha-MSH, not full-length alpha-MSH.
- Proposed anti-inflammatory activity is appropriately qualified as predominantly preclinical with no validated target or established human efficacy.
- Curate primary in-vitro and in-vivo studies separately; verify any registered human studies rather than inferring them from search-term matches.
- No approved product label exists from which to derive clinical safety or PK.

### 8. Lanreotide
- Correctly records cyclic octapeptide architecture, D-beta-Nal/D-Trp residues, disulfide bond and C-terminal amide.
- Keep Somatuline Depot and Somatuline Autogel product records separate; do not transfer formulation, route, release characteristics or jurisdictional indications.
- The dossier includes a useful mechanism and indication overview, but current label dosing, PK, safety and interaction statements require exact source/version extraction.
- Add pivotal acromegaly and CLARINET/GEP-NET trial data with denominators, endpoints and effect estimates.

### 9. Larazotide
- Correctly states investigational status and does not present it as a substitute for a gluten-free diet.
- Proposed tight-junction / zonulin-associated mechanism remains incompletely established; do not encode a definitive molecular target.
- Verify exact sequence, stereochemistry, termini and acetate salt from primary patent/CMC sources.
- Reconcile all phase 1–3 trial records, endpoint definitions and the phase 3 development outcome against registry records and primary publications. Separate symptoms, permeability biomarkers, serology and histology.

### 10. Leuprolide
- Correctly identifies a modified nonapeptide GnRH agonist and explains initial flare followed by receptor desensitisation/downregulation under continuous exposure.
- Preserve pyroglutamate, D-Leu6 and C-terminal N-ethylamide; distinguish free peptide from acetate salt.
- Lupron Depot, Lupron Depot-PED, Eligard, Fensolvi and Camcevi require separate product records with distinct depot technology, route, indications, age limits, PK and approval history.
- Extract product-specific labels, clinical evidence, safety frequencies, depot release data and country-specific regulatory status. Do not treat a depot product's duration as the peptide's plasma half-life.

## Cross-cutting implementation requirements

- Represent insulin as a disulfide-linked two-chain polypeptide with residue-level substitutions and chain-specific numbering.
- Preserve noncanonical residues, D/L stereochemistry, terminal modifications, salts and conjugates as typed chemical features.
- Distinguish active substance from medicinal product, formulation, presentation, route, indication and jurisdiction.
- Support multiple product labels and label versions per active substance.
- Store trial outcomes with registry identifier, population, sample size, endpoint, estimate, uncertainty and source.
- Attach evidence to individual claims; do not treat a dossier-level reference list as claim-level validation.

## Progress accounting

Batch 07 corrected the prior duplicate count to 68 unique dossier READMEs reviewed. This batch adds 10 new unique dossiers: **78/133 (58.6%) reviewed**, with **55 README files remaining**. This is text-level screening coverage only, not scientific validation or overall project completion.

## Status

All 10 dossiers remain in_progress. No production database import, live regulator verification or independent scientific sign-off is claimed.
