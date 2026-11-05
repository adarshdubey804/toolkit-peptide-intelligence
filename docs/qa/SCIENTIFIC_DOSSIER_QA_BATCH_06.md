# Scientific Dossier QA — Batch 06

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** Glatiramer acetate, Glutathione, Gonadorelin, Goserelin, Hexarelin, HGH fragment 176–191, Histrelin, Humanin, Icatibant, and Icotrokinra.

## Method and limits

This is a structured dossier-text and data-model screen. It is not independent validation against current regulator databases, official labels, primary chemical records or trial publications. Recent approval claims and exact structure statements require primary-source confirmation. All ten dossiers remain `in_progress`.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| Glatiramer acetate | Correctly describes a heterogeneous polypeptide mixture with defined amino-acid composition rather than one uniform sequence. | **Entity-model correction:** represent as a compositionally heterogeneous polymer mixture with distribution/average properties, not a single canonical FASTA, SMILES or molecular mass. Capture product-specific manufacturing, quality and comparability evidence. |
| Glutathione | Identifies endogenous γ-glutamyl-cysteinyl-glycine and distinguishes supplement/cosmetic claims from drug approval. | Represent reduced glutathione (GSH) and oxidized glutathione (GSSG) as distinct chemical species with redox relationship. Distinguish oral supplement, topical, injectable and compounded products; do not infer systemic clinical efficacy from endogenous biology or antioxidant plausibility. |
| Gonadorelin | Correctly highlights that continuous versus pulsatile exposure changes endocrine response and that product status varies. | Separate native-sequence gonadorelin active substance from product/device delivery systems. Verify current/historical Factrel and Lutrepulse records, jurisdictional availability and route-specific labels. Do not generalize continuous and pulsatile pharmacology. |
| Goserelin | Distinguishes 3.6 mg and 10.8 mg depot presentations and identifies sustained GnRH agonist exposure. | Preserve depot strength, polymer/release system and product-specific indication/PK records. Verify country-specific indications; do not infer fertility-related or cancer indications across jurisdictions. |
| Hexarelin | Explicitly warns that hexarelin/examorelin is not GHRP-2 and treats cardiovascular findings as hypothesis-generating. | Keep hexarelin distinct from GHRP-2 and other growth-hormone secretagogues. Verify exact stereochemical sequence and primary human study data; do not present small exploratory cardiovascular studies as outcome evidence. |
| HGH fragment 176–191 | Flags residue-numbering ambiguity and lack of a robust clinical safety database. | **Identity-critical:** map residue numbering to the canonical mature GH1 sequence and precursor sequence; verify actual material structure before assigning a sequence identifier. Do not treat research-use-only products as approved human medicines. |
| Histrelin | Distinguishes current SUPPRELIN LA implant use from historical VANTAS product history and explains continuous-delivery pharmacology. | Preserve formulation-specific records and historical status. Verify current VANTAS marketing status and country-specific authorizations; keep implant release and CMC evidence distinct from other histrelin formulations. |
| Humanin | Identifies a mitochondrial-derived research peptide and explicitly states that exogenous human safety/efficacy are unestablished. | Verify canonical sequence and distinguish endogenous mitochondrial translation evidence from administered synthetic peptide/analogue evidence. Do not infer therapeutic efficacy from cell or animal neuroprotection studies. |
| Icatibant | Correctly identifies a modified decapeptide bradykinin B2 receptor antagonist and retains chemistry/label extraction as open. | Verify stereochemistry, hydroxyproline/noncanonical residues, acetate/salt form and exact product label. Distinguish approved acute HAE treatment from prophylaxis or other unapproved uses. |
| Icotrokinra | Identifies an oral IL-23 receptor antagonist peptide and records product-level presentation. | **High-priority regulatory check:** independently verify the stated 2026 FDA approval, brand name, exact indication, age range, label and initial action date in Drugs@FDA/current USPI before production use. Verify full structure, oral formulation and trial-level evidence; do not infer class-wide effects from injectable IL-23 biologics. |

## Cross-cutting findings

1. **Mixtures and polymers:** glatiramer acetate is not a single molecule and should not be forced into single-sequence fields.
2. **Chemical-state relationships:** GSH/GSSG require redox-state-aware identity records rather than aliasing.
3. **Delivery system is part of product identity:** gonadorelin pump delivery and goserelin/histrelin depot implants materially shape exposure and should be represented at product level.
4. **Sequence numbering must be explicit:** GH fragments require reference-sequence version and mature-protein versus precursor numbering conventions.
5. **Endogenous peptide is not equivalent to therapeutic administration:** Humanin and glutathione illustrate the need to distinguish endogenous biology from exogenous product evidence.
6. **Recent regulatory claims need direct confirmation:** Icotrokinra's 2026 approval statement must not be promoted to a verified database fact until an authoritative regulator record is attached.

## Required follow-up

- Add mixture/polymer entity support and composition distributions.
- Add chemical-state relationships such as reduced/oxidized redox pairs.
- Model delivery device/depot formulation and product presentation independently from active substance.
- Store reference-sequence accession/version and residue-numbering convention for fragments.
- Verify all recent approval statements and current label details from primary regulator sources.
- Continue remaining dossier batches and consolidate into a master QA report.

## Completion statement

Batch 06 reviewed **10 additional dossier README files**. The structured QA screen now covers **59 of 133** dossier README files in the PR's changed-file inventory (approximately 44.4%). This is a text-level screen only, not full scientific validation, regulatory confirmation or evidence of a live database import.
