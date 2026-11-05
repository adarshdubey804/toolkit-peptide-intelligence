# Scientific Dossier QA — Batch 01

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** First ten alphabetically selected dossier READMEs in the PR: Abaloparatide, Abarelix, Afamelanotide, AHK-Cu, Angiotensin II, Anidulafungin, AOD-9604, Aviptadil, Bacitracin, and Bivalirudin.

## Review method and limits

This is a structured editorial and scientific-risk screen of the visible dossier text, not a full primary-source verification. It checks whether core dossier sections are present, whether uncertainty is represented honestly, and whether entity classification or claims need special scrutiny. No clinical label, trial registry, regulatory database, or primary paper was independently re-opened as part of this batch. A heading or reference list is not proof that every underlying claim is verified.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| Abaloparatide | Broad dossier structure includes identity, sequence, MOA, use, PK/PD, clinical evidence, safety, regulatory status and gaps. | Verify current labeler/marketing-authorisation holder, exact sequence/stereochemistry, label wording and all references against current authoritative sources. The README itself flags labeler verification. |
| Abarelix | Distinguishes historical FDA approval from later marketing discontinuation; salt/formulation caution is explicit. | Preserve the distinction between approval, discontinuation and safety withdrawal. Resolve salt-specific formula/mass only from authoritative substance records; the dossier appropriately leaves this open. |
| Afamelanotide | Clearly restricts approved use to EPP and distinguishes it from cosmetic tanning; identifies sequence notation as requiring verification. | Verify sequence, terminal modifications and stereochemistry against the approved product information. Confirm regulatory status by jurisdiction and date; do not treat the Melanotan I alias as proof of identical product/formulation. |
| AHK-Cu | Explicitly separates proposed cosmetic mechanisms from established clinical evidence; states that human PK and a validated target are not established. | Retain the evidence limitation. Clarify peptide ligand versus copper complex/speciation; do not borrow GHK-Cu findings as AHK-Cu evidence. Any efficacy wording needs AHK-Cu-specific primary sources. |
| Angiotensin II | Distinguishes endogenous hormone from the Giapreza product; explains AT1/AT2 context and critical-care scope. | Verify current label, trial endpoints and source-level details. Keep the AT2 counter-regulatory discussion contextual rather than implying equal contribution to the clinical pressor effect. |
| Anidulafungin | Correctly describes a cyclic lipopeptide/echinocandin rather than a linear peptide and includes target/resistance context. | **Taxonomy review required:** classify consistently as a cyclic lipopeptide/echinocandin natural-product-derived antifungal, not as a conventional peptide therapeutic. Confirm the workbook inclusion rationale and ontology category. |
| AOD-9604 | Clearly states unapproved status and leaves exact formula/mass unresolved pending structure confirmation; identifies missing trial-level extraction. | Do not add sequence, formula, molecular mass or efficacy numbers until a specific authoritative chemical identity and primary trial records are reconciled. Distinguish proposed hGH 177–191-derived description from a verified complete structure. |
| Aviptadil | Provides a defined 28-aa amidated sequence and VPAC1/VPAC2 mechanism; appropriately separates biological plausibility from clinical proof. | Verify sequence/terminal amidation against a trusted reference substance source. Separate clinical programmes, formulations and jurisdictions; avoid transferring results between indications or formulations. |
| Bacitracin | Recognises mixture/compositional complexity and distinguishes topical products from historical injectable product status; mechanism is described. | **Taxonomy and regulatory granularity review required:** represent bacitracin as a complex cyclic polypeptide antibiotic mixture, with bacitracin A and zinc/topical product records distinguished. Reconcile each dosage form and jurisdiction separately. |
| Bivalirudin | Good core mechanism, sequence context, PK and landmark-trial structure; warns against treating historic trial context as current label. | Verify current product labels and trial tables, including population, comparator, endpoint and bleeding outcomes. Distinguish bivalirudin substance from formulation/product and avoid implying HIT is a universal labelled indication. |

## Cross-cutting issues

1. **The workbook's “peptide” scope is broader than a strict peptide-drug ontology.** This sample includes a cyclic lipopeptide antifungal and a heterogeneous cyclic polypeptide antibiotic mixture. Adopt explicit entity classes (e.g., linear synthetic peptide, peptide analogue, cyclic peptide, lipopeptide, peptide mixture, endogenous peptide hormone, peptide-derived fragment, metal–peptide complex) and define inclusion rules.
2. **Identity is not just a name or sequence.** Capture stereochemistry, terminal modifications, disulfide/cyclisation, lipidation, salt/counterion, metal stoichiometry, mixture composition and product formulation where applicable. Unknown values should remain explicitly unresolved.
3. **Regulatory status must be product-, indication-, jurisdiction- and date-specific.** Separate approval, marketing status, discontinuation, withdrawal, investigational status and compounding/supplement/cosmetic claims.
4. **Mechanism statements need evidence labels.** Distinguish established receptor/target pharmacology, supported physiological pathway, preclinical hypothesis and marketing claim.
5. **Clinical evidence should be indication-specific.** Record study identifier, design, population, formulation, comparator, endpoint, effect estimate, uncertainty and safety outcomes before making quantitative claims.
6. **Curation status remains `in_progress`.** The presence of comprehensive headings does not mean a dossier is scientifically complete.

## Required follow-up work

- Add a controlled entity-class vocabulary and an inclusion/exclusion rule for the workbook.
- Reconcile anidulafungin and bacitracin classification before counting the workbook as a strict peptide-drug set.
- Run the same QA screen over the remaining dossier folders in bounded batches.
- For each dossier, verify identity and regulatory statements against authoritative substance records and current regulator-approved product information; verify clinical claims against trial registries and primary publications.
- Keep this report as a QA log; do not silently rewrite unresolved fields or mark dossiers complete based on automated checks.

## Completion statement

Batch 01 reviewed **10 of 133 dossier README files** in the PR's changed-file inventory. This is a partial screen only. No production database import, live database integrity check, or complete scientific validation is claimed.
