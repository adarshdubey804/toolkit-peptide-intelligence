# Scientific Dossier QA — Batch 14

**Scope:** final five dossier READMEs screened on PR #155.  
**Files reviewed:** MGF / PEG-MGF, romidepsin, Selank, ziconotide, and zilucoplan.  
**Method:** structured text-level review of identity, molecular class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. The final batch contains several difficult entity-resolution cases: endogenous IGF-1 splice-variant biology versus synthetic MGF fragments and PEG conjugates; romidepsin as a bicyclic depsipeptide; and Selank as a regional investigational/registered peptide with limited independent evidence.
2. The approved products ziconotide and zilucoplan require strict product-specific safety and route boundaries. Ziconotide is an intrathecal CaV2.2 blocker with a boxed warning; zilucoplan is a subcutaneous C5 inhibitor with a boxed meningococcal-infection warning.
3. All five dossiers appropriately remain in_progress. This batch completes the text-level screening of all 133 dossier README files in the PR #155 changed-file inventory, but does not establish claim-by-claim primary-source verification or scientific completion.

## Dossier-level findings and actions

### 1. MGF / PEG-MGF
- Correctly identifies the workbook label as chemically under-specified and distinguishes human IGF-1Ec terminology from rodent IGF-1Eb terminology.
- Preserve separate entities for endogenous IGF-1 splice-variant transcript/protein, isolated synthetic E-peptide fragments, commercial products marketed as MGF, and PEG-conjugated MGF products. Do not merge them under one canonical peptide identity.
- No definitive synthetic sequence, PEG size/distribution, conjugation site, linker, salt or validated reference standard is established in the dossier. Keep these fields unresolved rather than importing vendor catalogue strings.
- Mature IGF-1R–IRS/PI3K/AKT and RAS/RAF/MEK/ERK pathways must not be automatically attributed to synthetic MGF fragments as proven direct receptor agonism.
- Separate endogenous gene-expression studies, isolated peptide experiments, animal models and controlled human trials. Exercise-associated IGF1 splice-variant expression is not evidence that injected MGF improves muscle or tendon healing.
- Maintain no FDA-approved MGF/PEG-MGF product status; no human PK, efficacy, dose or safe-use claim should be inferred.

### 2. Romidepsin
- Correctly classified as a sulfur-containing bicyclic depsipeptide natural-product-derived HDAC inhibitor, not a conventional peptide hormone or linear peptide.
- Preserve the macrocyclic ester/amide framework and disulfide-containing structural motif; a standard one-letter sequence is not an adequate identity representation.
- Current US labelled indication is CTCL in adults after at least one prior systemic therapy. The historical PTCL indication was removed from the US label in July 2021; do not list PTCL as a currently approved US indication.
- Extract current generic and originator product labels separately where presentations/excipients differ. Keep IV infusion route and product-specific preparation instructions distinct.
- Capture current CYP3A4 interactions, hepatic-impairment adjustment, myelosuppression, infection/reactivation, QT/electrolyte and tumour-lysis risks with exact label locators.
- Clinical evidence from historical PTCL trials, CTCL studies and investigational HIV latency work must remain separate; trial-specific safety rates cannot be transferred between populations.

### 3. Selank
- Correctly identifies Selank as a tuftsin-related heptapeptide with a Pro-Gly-Pro extension and distinguishes it from Semax despite their shared motif.
- Verify exact sequence, stereochemistry, terminal chemistry, salt and product formulation from primary analytical records and the current Russian state register before asserting a specific authorized product.
- The proposed enkephalin-metabolism, GABAergic and serotonergic mechanisms remain incompletely validated; do not present a direct receptor target or benzodiazepine-like mechanism as established.
- Regional clinical reports should be assessed for randomization, blinding, sample size, endpoints, adverse-event capture and independent replication. Cognitive-enhancement and neuroprotection claims remain very low certainty.
- FDA compounding concerns about aggregation and peptide-related impurities are not an approval or a quantified clinical risk estimate. Preserve the exact source and scope.
- Maintain not FDA-approved and not centrally EMA-authorized status. Do not infer global authorization from secondary literature or online product availability.

### 4. Ziconotide
- Correctly identifies ziconotide as a 25-residue synthetic conopeptide based on omega-conotoxin MVIIA, with three disulfide bonds and an intrathecal-only clinical product.
- Validate the full stereochemical sequence and all three disulfide pairings against the current Prialt structural record before canonical structure import.
- The CaV2.2 N-type voltage-gated calcium-channel blockade and reduced release of pronociceptive neurotransmitters are appropriately distinguished from opioid-receptor pharmacology.
- Keep intrathecal CSF distribution and pump/catheter exposure distinct from plasma PK. Extract quantitative CSF PK only with sampling method, infusion conditions and study population.
- Preserve the current severe chronic pain indication boundary and the boxed warning for severe psychiatric symptoms and neurological impairment; history of psychosis is a critical contraindication.
- Capture device-associated meningitis, altered consciousness, hallucinations, cognitive/gait effects and discontinuation rates with exact label/trial locators. Do not generalize benefit or tolerability across all intrathecal patients.

### 5. Zilucoplan
- Correctly classifies zilucoplan as a synthetic macrocyclic, lipidated peptide inhibitor of complement C5, not a linear peptide or monoclonal antibody.
- Preserve the full stereochemical macrocycle, non-proteinogenic residues and lipid/albumin-binding architecture; exact sequence, formula and structure must be sourced from FDA chemistry records.
- Keep the adult anti-AChR antibody-positive generalized myasthenia gravis indication restricted to the labelled population. Do not generalize to seronegative disease, ocular-only MG or other complement disorders.
- Extract RAISE (NCT04115293) MG-ADL primary endpoint, effect estimate, confidence interval, analysis population and QMG/supportive outcomes.
- Preserve the boxed warning for serious meningococcal infections and exact vaccination/antimicrobial precautions from the current label. Vaccination does not eliminate infection risk.
- Keep the subcutaneous prefilled-syringe product distinct from IV monoclonal C5 inhibitors; extract route-specific PK, immunogenicity and postmarketing safety.

## Cross-cutting implementation requirements

- Support endogenous splice-variant biology, synthetic peptide fragments, PEG conjugates, bicyclic depsipeptides, conopeptides and lipidated macrocyclic complement inhibitors.
- Model biological precursor/transcript, active substance, synthetic fragment, conjugate, salt, finished product, formulation, route, indication, jurisdiction and authorisation as separate linked entities.
- Do not assign canonical sequences or structures to under-specified mixtures/conjugates or to entities whose active moiety is unresolved.
- Require claim-level citations and exact source locators for identity, mechanism, PK/PD, clinical outcomes, safety and regulatory assertions.
- Keep product-specific boxed warnings, contraindications, route restrictions and historical indication withdrawals explicit.
- Preserve in_progress until official records, primary evidence, claim-level citations and independent scientific review are complete.

## Progress accounting

Batch 13 recorded **128/133** unique dossier README files screened. This final batch adds the five remaining unique files, bringing cumulative text-level QA coverage to **133/133 (100%)**.

This is 100% coverage of the README files in the PR #155 changed-file inventory for structured text-level screening. It is not 100% scientific validation, claim-level source verification, completed A-to-Z dossier curation, deployed database import, or overall project completion.

## Status

All five dossiers remain in_progress. The full 133-file text-level screen is complete, but live regulator verification, primary-source claim validation, production database import and independent scientific sign-off remain separate required workstreams.
