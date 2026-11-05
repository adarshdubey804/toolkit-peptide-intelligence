# Scientific Dossier QA — Batch 05

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** Eptifibatide, Etelcalcetide, Exenatide extended-release, Exenatide immediate-release, FOXO4-DRI, Gallium Ga-68 dotatate, Gallium Ga-68 edotreotide (DOTATOC), Ganirelix, and GHK-Cu. Epitalon was also re-opened as a consistency check, but was already counted in Batch 02 and is not counted again.

## Method and limits

This is a structured screen of dossier content and data-model risks, not independent confirmation of current product labels, regulator databases, chemical records or primary clinical publications. The dossiers remain `in_progress`; no scientific-completion claim is made.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| Eptifibatide | Identifies cyclic heptapeptide chemistry and explicitly warns that a linear FASTA string is insufficient for its disulfide/mercaptopropionyl structure. | Preserve cyclic topology, noncanonical residue, disulfide connectivity and salt/formulation in a structure-aware representation. Verify current label revision and complete clinical endpoint tables. |
| Etelcalcetide | Identifies a modified disulfide-linked oligopeptide calcimimetic and records jurisdiction-specific open tasks. | Verify exact molecular architecture, disulfide linkage and product identity; keep US/EU/India authorization separate. Capture trial endpoints and product-label PK with source/version. |
| Exenatide extended-release | Correctly describes PLGA microsphere depot formulation and distinguishes it from immediate-release product. | Model active substance separately from each finished product/formulation. Preserve microsphere polymer, excipients, release profile and product-specific label data; do not transfer BCise excipients to the original kit. |
| Exenatide immediate-release | Correctly identifies 39-aa exendin-4 analogue and distinguishes Byetta from extended-release presentations. | Avoid duplicate active-substance records: link immediate- and extended-release products to one canonical exenatide active substance while maintaining separate product, PK and administration records. |
| FOXO4-DRI | Explicitly identifies a preclinical D-retro-inverso cell-penetrating research peptide and states that it is not an approved medicine. | Verify exact retro-inverso sequence, stereochemistry and cell-penetrating segment from primary analytical/patent sources. Do not infer clinical senolytic efficacy or safety from preclinical models. |
| Gallium Ga-68 dotatate | Identifies NETSPOT as a radiolabelled cyclic somatostatin analogue used diagnostically and distinguishes imaging from therapy. | Model the peptide-chelator precursor, radiolabelled active imaging agent and finished radiopharmaceutical as linked entities. Store radionuclide, activity, radiochemical purity, expiry/time and product-specific diagnostic evidence. |
| Gallium Ga-68 edotreotide (DOTATOC) | Separates DOTATOC from DOTATATE and identifies diagnostic-performance data as an open task. | Do not collapse DOTATOC and DOTATATE into aliases: they are distinct peptide ligands/chemical entities. Preserve distinct sequences, chelator conjugates, receptor-binding evidence and product authorizations. |
| Ganirelix | Provides GnRH antagonist and IVF context and keeps current label/PK extraction open. | Verify acetate stoichiometry, exact structure, label and approval history. Keep product brand and jurisdiction-specific authorizations separate. |
| GHK-Cu | Explicitly distinguishes copper-bound GHK from an approved medicine and notes cosmetic use. | Model GHK peptide ligand and copper complex/speciation as related but distinct chemical entities. Do not use GHK-Cu cosmetic or in-vitro claims as proof of systemic human efficacy or PK. |

## Cross-cutting findings

1. **Same active substance, different product:** exenatide immediate- and extended-release products should share the active-substance identity but not the formulation, PK, excipient or administration records.
2. **Distinct radioligands must remain distinct:** DOTATATE and DOTATOC are not interchangeable aliases. Each radiopharmaceutical needs its own peptide/chelator/radionuclide identity and diagnostic evidence.
3. **Structure-aware chemistry is essential:** cyclic topology, noncanonical residues, retro-inverso stereochemistry, disulfide bonds and metal coordination cannot be reliably represented by a simple amino-acid string alone.
4. **Diagnostic versus therapeutic outcomes:** PET diagnostic performance should not be mixed with therapeutic efficacy measures.
5. **Regulatory evidence must be product- and jurisdiction-specific:** approval history, active marketing and current availability are different fields.

## Required follow-up

- Implement active-substance/product separation and explicit formulation links.
- Add structured covalent topology and noncanonical-residue annotations.
- Add radiopharmaceutical entity relationships and radiochemical quality fields.
- Keep DOTATATE and DOTATOC distinct and ensure aliases do not collapse chemically distinct entities.
- Continue bounded dossier review, then consolidate into a master QA report.

## Completion statement

Batch 05 reviewed **9 new dossier README files**. The structured QA screen now covers **49 of 133** dossier README files in the PR's changed-file inventory (approximately 36.8%). Epitalon was checked again but not double-counted. This is a text-level screen only, not full scientific validation, regulatory confirmation or evidence of a live database import.
