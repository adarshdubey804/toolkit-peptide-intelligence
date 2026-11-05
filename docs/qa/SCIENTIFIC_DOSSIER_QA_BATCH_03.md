# Scientific Dossier QA — Batch 03

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** Albiglutide, Bremelanotide, Bulevirtide, Salmon calcitonin, Carbetocin, Caspofungin, Cerebrolysin, Cetrorelix, Colistin/colistimethate, and Copper Cu 64 dotatate.

## Method and limits

This is a structured screen of dossier text and scientific-data architecture. It is not independent confirmation of current regulator databases, product labels or primary publications. Regulatory dates and status statements—especially recent approvals—must be rechecked against the relevant regulator's live record. All dossiers remain `in_progress`.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| Albiglutide | Explicitly identifies a recombinant GLP-1–human serum albumin fusion protein and separates US/EU product histories. | **Ontology correction:** classify as a recombinant fusion protein/biologic containing peptide domains, not a short peptide. Preserve full-length sequence, domain boundaries, fusion junction and product-specific records. Historical authorisation does not establish current market availability or Indian approval. |
| Bremelanotide | Restricts the FDA indication to acquired, generalized HSDD in premenopausal women and notes that the precise therapeutic mechanism is unknown. | Verify exact cyclic structure, stereochemistry and connectivity from authoritative chemistry/label sources. Avoid presenting central MC4R hypotheses as a fully established clinical mechanism. |
| Bulevirtide | Describes the myristoylated preS1-derived lipopeptide and NTCP-targeted HDV entry mechanism; separates surrogate endpoints from clinical outcomes. | Verify the stated 2026 US accelerated-approval date, indication and label directly in Drugs@FDA/current USPI before production use. Maintain separate EU and US dosing/label fields. Do not imply that virological/biochemical response proves improved long-term clinical outcomes. |
| Salmon calcitonin | Provides product/formulation distinctions and warns that intranasal and injectable products are not interchangeable. | Verify exact sequence, disulfide topology, formula and mass. Reconcile the current status of each route and indication by jurisdiction; historical label examples must not become executable prescribing instructions. |
| Carbetocin | Distinguishes WHO recommendation context from US regulatory authorization and flags country-specific labels. | Record each country's authorized brand, route, indication and current label. Extract CHAMPION and other trial endpoints precisely; do not generalize noninferiority on one blood-loss endpoint to all endpoints. |
| Caspofungin | Correctly identifies a semisynthetic cyclic echinocandin lipopeptide and preserves acetate salt/stereochemical concerns. | **Ontology review:** classify as a cyclic lipopeptide/echinocandin antifungal, not a conventional linear peptide. Verify stereochemical structure and acetate salt record. |
| Cerebrolysin | Explicitly identifies a porcine-brain hydrolysate mixture rather than one peptide molecule and states its non-US/non-central-EMA status. | **Entity-model correction:** represent as a complex biological peptide/amino-acid mixture with batch/process-dependent composition, not a single sequence. Do not invent one formula, sequence or molecular weight. Verify each jurisdiction's authorization separately. |
| Cetrorelix | Distinguishes US label from European product information and records specialist IVF context. | Verify current US label, NDA/application and marketed status independently. Keep country-specific product information separate; complete PK and pivotal-study extraction. |
| Colistin/colistimethate | Explicitly distinguishes active colistin A/B mixture from colistimethate sodium prodrug. | **Identity-critical:** create distinct linked substance/product records for colistin and colistimethate sodium. Do not treat prodrug mass, potency units, conversion or PK as interchangeable. Record route and product-specific status separately. |
| Copper Cu 64 dotatate | Clearly classifies DETECTNET as a diagnostic radiopharmaceutical and distinguishes it from other radiolabelled somatostatin analogues and therapeutic radiopharmaceuticals. | **Ontology correction:** model the peptide-chelator conjugate and Cu-64 radiolabelled diagnostic product as linked but distinct entities. Capture radionuclide, chelator, peptide, radiochemical purity, activity calibration and time-dependent expiry. Do not mix diagnostic and therapeutic evidence. |

## Cross-cutting findings

1. **The workbook is a broad peptide-related therapeutic inventory, not a strict list of single peptide molecules.** It includes fusion proteins, peptide mixtures, lipopeptide antibiotics, prodrugs and radiopharmaceutical conjugates. The database needs explicit entity classes and relationship types.
2. **Substance, active moiety, prodrug and finished product must be distinct.** Colistin/colistimethate and copper-64 dotatate illustrate why a single flat peptide record is inadequate.
3. **Mixtures must not be forced into single-sequence fields.** Cerebrolysin and colistin require mixture composition/provenance models.
4. **Regulatory status needs a jurisdiction, product, indication and as-of date.** WHO recommendations, EMA authorization, FDA approval and national availability are not interchangeable.
5. **Diagnostic radiopharmaceuticals need a dedicated data model.** Their value is diagnostic performance and imaging quality, not therapeutic efficacy endpoints.

## Required implementation direction

- Add an entity taxonomy with at least: linear peptide, modified/cyclic peptide, peptide hormone, recombinant fusion protein, lipopeptide, peptide mixture/hydrolysate, peptide prodrug, peptide-chelator conjugate, radiolabelled diagnostic product, and combination product.
- Add linked-entity relationships: `active_moiety_of`, `prodrug_of`, `radiolabelled_form_of`, `fusion_component_of`, `mixture_component_of`, and `combination_component_of`.
- Preserve source-specific jurisdictional regulatory records with effective dates and product identifiers.
- Keep diagnostic performance, therapeutic efficacy and surrogate biomarker outcomes in separate evidence domains.
- Do not mark any dossier complete until claim-level sources and identity records are verified.

## Completion statement

Batch 03 reviewed **10 additional dossier README files**. The structured QA screen now covers **30 of 133** dossier README files in the PR's changed-file inventory. This is a text-level QA screen, not full scientific validation, regulatory verification or evidence of a live database import.
