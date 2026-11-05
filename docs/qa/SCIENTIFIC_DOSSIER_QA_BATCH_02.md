# Scientific Dossier QA — Batch 02

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** Ten dossier READMEs: BPC-157, Cagrilintide, CJC-1295, Dasiglucagon, DSIP, Epitalon, GHK-Cu, GHRP-2 (pralmorelin), GHRP-6, and Glucagon.

## Method and limits

This is a structured screen of the dossier text and section architecture. It is not independent primary-source or current-label verification. In particular, regulatory statements and clinical efficacy claims require separate checks against regulator records, product information, trial registries and primary publications. All ten dossiers remain `in_progress`.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| BPC-157 | Uses a consistent dossier framework and explicitly retains claim-level review as an open task. | Treat as investigational/unapproved; do not present proposed tissue-repair mechanisms or online claims as established human efficacy. Verify the exact sequence/chemical identity and every human-evidence claim against primary sources. |
| Cagrilintide | Separates monotherapy development from CagriSema combination evidence and identifies specific phase 2/3 programmes. | Preserve the separation between cagrilintide monotherapy and the cagrilintide–semaglutide combination. Verify trial identifiers, final results, current development/regulatory status and exact modified sequence against primary trial records and sponsor/regulator sources. |
| CJC-1295 | Explicitly warns that DAC and non-DAC/modified GRF(1–29) constructs are not interchangeable and marks extrapolated claims as indirect. | **Identity-critical:** maintain separate entities/construct records for DAC and non-DAC forms. Do not share PK, half-life, clinical outcomes or regulatory conclusions across constructs without direct evidence. |
| Dasiglucagon | Standard sections cover identity, mechanism, PK, clinical evidence, safety and regulatory status. | Verify exact sequence/modifications and product-specific labels. Distinguish dasiglucagon from native glucagon and other glucagon analogues; do not merge their formulation or stability data. |
| DSIP | Standard dossier structure and explicit claim-level review status. | Mechanistic and sleep-efficacy claims require careful evidence grading; do not infer established human sleep benefit from animal or small historical studies. Verify sequence and nomenclature, including the emideltide name, from authoritative substance records. |
| Epitalon | Standard structure and explicit open curation status. | Treat telomerase, longevity and anti-ageing claims as unproven unless supported by robust, independently replicated human evidence. Verify sequence/identity and separate in-vitro, animal and human data. |
| GHK-Cu | Standard dossier structure and explicit claim-level review status. | Distinguish free GHK, copper-bound GHK-Cu, topical cosmetic formulations and other routes. Do not infer systemic PK or clinical efficacy from topical/in-vitro evidence. Specify metal-complex identity/speciation where evidence permits. |
| GHRP-2 (pralmorelin) | Distinguishes diagnostic product history in Japan from non-approved bodybuilding claims and discusses compounding-policy concerns. | Keep jurisdiction- and product-specific status. Verify current Japanese product information and current US FDA compounding-policy source. Separate diagnostic use evidence from claims about muscle gain, fat loss or anti-ageing. |
| GHRP-6 | Separates receptor pharmacology, appetite/metabolic effects, clinical evidence and safety; keeps long-term uncertainty explicit. | Do not transfer quantitative effects from GHRP-2 or other ghrelin-receptor agonists. Verify sequence, human PK and safety claims; clearly distinguish research use from approved product status. |
| Glucagon | Standard dossier structure and explicit open claim-level review. | Verify sequence and product-specific modifications/formulations. Distinguish native glucagon from stable analogues and formulations such as dasiglucagon; use current labels for each marketed product and indication. |

## Cross-cutting risks observed

1. **Analogue and construct conflation:** CJC-1295 DAC/non-DAC, native glucagon/dasiglucagon, and cagrilintide/CagriSema require separate entity and evidence records.
2. **Evidence transfer:** receptor-family or class-level plausibility is not molecule-specific clinical evidence. This is particularly important for GHRP-2/GHRP-6 and copper peptides.
3. **Claims with high hype-to-evidence ratios:** BPC-157, DSIP and Epitalon need conservative wording and explicit separation of preclinical hypotheses from human outcomes.
4. **Sequence and chemical identity:** all modifications, stereochemistry, termini, counterions, complexation and formulation differences must be explicit or marked unresolved.
5. **Regulatory time sensitivity:** product status, compounding policies and development stage must carry jurisdiction and an as-of date.

## Required follow-up

- Preserve distinct canonical entities for molecularly distinct analogues, conjugates and combination products.
- Add explicit evidence-level labels to each mechanism and efficacy claim.
- Verify sequence and modifications from authoritative substance/product sources before asserting canonical structures.
- Extract trial-level data only from registries and primary publications, recording design, population, formulation, endpoints, effect estimates and safety.
- Continue the same bounded QA process across remaining dossiers.

## Completion statement

Batch 02 reviewed **10 additional dossier README files**. Combined with Batch 01, the structured screen covers **20 of 133** dossier README files in the PR's changed-file inventory. This is not complete scientific validation and does not establish a live database import or production database integrity.
