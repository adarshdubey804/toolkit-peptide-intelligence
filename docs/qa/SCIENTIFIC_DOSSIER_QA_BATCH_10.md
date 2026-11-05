# Scientific Dossier QA — Batch 10

**Scope:** 10 additional dossier READMEs screened on PR #155.  
**Files reviewed:** motixafortide, MOTS-c, nafarelin, navepegritide, nesiritide, octreotide, oritavancin, oxytocin, palopegteriparatide, and pasireotide.  
**Method:** structured text-level review of identity, molecular class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. This batch includes modified cyclic peptides, endogenous/mitochondrial-derived peptides, peptide hormone analogues, a long-acting prodrug conjugate and a lipoglycopeptide antibiotic. The data model must represent peptide-derived and peptide-related entities without forcing every entry into a linear amino-acid sequence.
2. Product and formulation separation is essential. Octreotide immediate-release, LAR, oral delayed-release and pen products have distinct labels; pasireotide SC and LAR products have different indications; and product-specific instructions for motixafortide, nesiritide and palopegteriparatide must not be inferred from class biology.
3. Regulatory status must be tied to the exact product, indication, jurisdiction and verification date. Accelerated approval (navepegritide), a drug substance registration (UNII), historical workbook status and sponsor announcements are different evidence categories.
4. Several dossiers contain good mechanism summaries but still need exact source locators, current label extraction, quantitative clinical tables and independent identity review. All remain `in_progress`.

## Dossier-level findings and actions

### 1. Motixafortide
- Correctly classified as a modified cyclic CXCR4 antagonist used with filgrastim for hematopoietic stem-cell mobilization, not as a direct antimyeloma cytotoxic agent.
- Preserve the N-terminal 4-fluorobenzoyl cap, noncanonical residues (Nal, Cit and D-Lys), C-terminal amide and Cys-linked disulfide in the molecular representation.
- Keep the free active moiety and variable-acetate product form distinct; do not assign one fixed salt molecular weight to material with variable acetate content.
- Separate the approximately 2-hour plasma half-life from longer receptor occupancy observations; these are different measurements and evidence contexts.
- Extract exact label safety, premedication, apheresis endpoint and GENESIS trial tables. Collection success is not a demonstrated survival benefit.
- Verify current FDA label/GSRS identifiers and product-specific regulatory status from official sources before marking chemistry or authorization fields final.

### 2. MOTS-c
- Correctly identifies MOTS-c as a 16-residue mitochondria-derived peptide associated with the mitochondrial 12S rRNA region and distinguishes endogenous peptide biology from exogenously administered synthetic material.
- Verify translation under the mitochondrial genetic code, sequence, stereochemistry, termini and any reported cell-penetrating segment against the original sequence/analytical publication.
- Proposed AMPK-associated and one-carbon-metabolism effects should be tied to the specific experimental model and source; do not present a definitive receptor or target where none is established.
- Separate observational biomarker studies, cell experiments, animal experiments and administered-product human studies. Endogenous circulating concentrations do not establish exogenous product PK.
- Maintain not FDA-approved / investigational status unless an exact jurisdictional marketing authorisation is independently documented. No clinical safety profile or dose should be inferred.

### 3. Nafarelin
- Correctly distinguishes nafarelin from other GnRH analogues and records the pyroglutamyl N-terminus, D-2-naphthylalanine substitution and C-terminal glycinamide.
- Preserve free peptide and acetate/hydrate product forms separately; variable acetate and water content mean a single salt mass should not be applied to every material lot.
- The biphasic mechanism is appropriately described: initial GnRH-receptor stimulation followed by desensitisation/downregulation under continuous exposure. Do not describe it as an immediate antagonist.
- Keep central precocious puberty and endometriosis label sections, populations and regimens distinct. Verify current product label and marketed availability separately from historical approval.
- PK values must retain route, dose, population, sampling and assay conditions; radiolabelled subcutaneous recovery data must not be represented as intranasal human mass-balance data.
- Extract current safety, contraindication, interaction and special-population tables with exact label locators.

### 4. Navepegritide
- Correctly identifies YUVIWEL as a long-acting C-type natriuretic peptide analogue and describes the NPR-B/NPR2–cGMP–PKG pathway in growth-plate biology.
- The dossier states FDA accelerated approval on 27 February 2026 for a narrow paediatric achondroplasia population with open epiphyses. Verify the exact FDA label, approval letter and Drugs@FDA record before presenting this as a current authorised indication.
- Extract exact peptide sequence, linker/conjugate architecture, stereochemistry and active product structure from primary regulatory/CMC records; do not infer the conjugate from native CNP.
- Separate accelerated-approval surrogate evidence (annualized growth velocity) from confirmatory clinical benefit; capture the required postmarketing/confirmatory study and its status.
- Do not extrapolate the indication to other skeletal dysplasias, closed growth plates or nonspecific short stature.
- Add complete current label PK, safety, contraindications and paediatric monitoring with source locators.

### 5. Nesiritide
- Correctly classifies nesiritide as recombinant human BNP-32 with a Cys10–Cys26 disulfide and NPR-A/GC-A–cGMP mechanism.
- Preserve recombinant product identity and mature peptide connectivity; do not infer formula, terminal chemistry or exact manufacturing details without official product/CMC evidence.
- The ASCEND-HF summary appropriately distinguishes physiological/dyspnoea effects from mortality or rehospitalisation benefit. Retain the prespecified endpoint definitions and exact effect estimates, confidence intervals and hypotension findings.
- Verify the current Natrecor label, current US regulatory/marketing status and exact indication wording; original 2001 approval alone does not establish current supply.
- Extract quantitative PK and exposure–hypotension relationships from label or primary pharmacology studies. Do not substitute endogenous BNP measurements or values from other natriuretic peptides.
- Keep this as a monitored acute-care prescription product, not chronic disease-modifying therapy or a general BNP class proxy.

### 6. Octreotide
- Correctly identifies octreotide as a cyclic octapeptide with D-Phe/D-Trp, a disulfide bridge and C-terminal threoninol; the acetate counterion should remain distinct from the active peptide.
- Preserve Sandostatin immediate-release, Sandostatin LAR Depot, Mycapssa and Bynfezia Pen as separate product records with their own route, formulation, strengths, indications, devices and label versions.
- Do not transfer indications or dosing instructions between SC/IV injection, deep-IM depot microspheres and oral delayed-release capsules.
- Verify the sequence, residue connectivity, free peptide formula/mass and salt basis from official chemistry records before canonical import.
- Extract formulation-specific PK, clinical endpoints, glucose/gallbladder effects, interactions and safety tables. Distinguish acromegaly biochemical control from symptom control in functional neuroendocrine tumours.
- The 1988 first-approval date should be tied to the original NDA/action record and not treated as the approval date for every later formulation.

### 7. Oritavancin
- Correctly classified as a semisynthetic lipoglycopeptide antibiotic rather than a conventional peptide. A complete stereochemical chemical representation is more appropriate than a one-letter sequence.
- The three described antibacterial actions—cell-wall precursor binding/transglycosylation inhibition, transpeptidation interference and membrane effects—should be linked to primary mechanistic studies and exact assay conditions.
- Preserve Orbactiv and Kimyrsa as distinct approved products with separate preparation, infusion, label and availability records.
- The long terminal half-life and coagulation-assay interference are important, but exact aPTT/PT/INR/ACT windows and heparin contraindication must be checked against the current label.
- Keep the SOLO I/II evidence limited to labelled ABSSSI populations and endpoints; do not extrapolate to bacteraemia, endocarditis or other deep infections.
- Add full chemical identifiers, salt form, stereochemistry, trial endpoint tables and current interaction data.

### 8. Oxytocin
- The dossier correctly describes the mature cyclic nonapeptide, Cys1–Cys6 disulfide and oxytocin-receptor Gq/11 signalling leading to intracellular calcium and uterine contraction.
- The current entry is a useful scaffold but remains comparatively generic: it lacks exact label/paper citations and quantitative PK/PD, clinical endpoint and product-specific safety extraction.
- Verify the workbook's 1980 year field against the exact FDA product/NDA record; do not treat a workbook value as independently verified approval chronology.
- Distinguish oxytocin active substance from Pitocin and other national products, formulations, concentrations, routes and excipients.
- Add claim-level sources for sequence, terminal chemistry, disulfide connectivity, receptor pharmacology, labour induction and postpartum haemorrhage evidence.
- Extract uterine tachysystole, foetal effects, water intoxication/hyponatraemia, cardiovascular risks, contraindications and monitoring from current official labels and primary safety evidence.
- Do not populate numerical PK, exact mass or formula until the relevant product specification or authoritative chemistry source is checked.

### 9. Palopegteriparatide
- Correctly classified as a long-acting PTH(1-34) prodrug conjugate rather than unmodified teriparatide; the PEG/linker architecture and release of active PTH fragment are central to identity.
- Model intact conjugate, released PTH(1-34), linker/carrier and finished YORVIPATH product as linked but distinct entities. Do not assign the released fragment's molecular mass to the complete conjugate.
- Preserve the narrow adult hypoparathyroidism indication and the exclusion of acute postsurgical hypoparathyroidism / paediatric populations as label-specific boundaries.
- Extract current label PK, dose-expression basis, full adverse-event frequencies, hypercalcaemia/hypocalcaemia warnings, digoxin interaction and hypersensitivity/orthostatic risks.
- Verify exact conjugate structure, sequence, release chemistry, formulation and product concentration against the current FDA label and assessment/CMC sources.
- Distinguish trial surrogate/biochemical outcomes from longer-term clinical outcomes and retain the Phase 3 registry identifier and endpoint details.

### 10. Pasireotide
- Correctly distinguishes Signifor immediate-release SC from Signifor LAR deep-IM depot and preserves the different US indication boundaries for Cushing's disease and acromegaly.
- The dossier itself flags its provisional sequence as unvalidated. Do not import this sequence or assign a residue count until authoritative chemistry documentation resolves complete connectivity, noncanonical residues, cyclisation and termini.
- Do not transfer octreotide or lanreotide sequences, formulae or receptor-affinity values to pasireotide.
- Extract separate PK, dose/exposure, safety and efficacy tables for Signifor and Signifor LAR; hyperglycaemia is a major safety concern and must be represented with formulation/population context.
- Add trial identifiers, sample sizes, randomisation, endpoints, response definitions and effect estimates for the Cushing's disease and acromegaly programmes.
- Verify each product's current FDA label, application history and jurisdiction-specific authorisation; the first US approval year is not a substitute for current label status.

## Cross-cutting implementation requirements

- Support cyclic and modified peptides, endogenous-derived peptides, recombinant peptide hormones, long-acting prodrug conjugates and lipoglycopeptide antibiotics as distinct entity classes.
- Represent active moiety, chemical form/salt, conjugate/linker, released active fragment, finished product, formulation, route, indication, jurisdiction and authorisation as separate linked records.
- Store noncanonical residues, D/L stereochemistry, terminal modifications, disulfides, cyclisation and carrier/linker architecture explicitly.
- Require claim-level citations with exact source locators for identity, sequence, mechanism, PK/PD, clinical outcomes, safety and regulatory claims.
- Preserve label versions and as-of dates; distinguish approval, accelerated approval, withdrawal, discontinued marketing, trial status and nomenclature registration.
- Keep all dossiers `in_progress` until applicable official records, primary evidence, source locators and independent review are complete.

## Progress accounting

Batch 09 recorded **88/133** unique dossier README files screened. This batch adds 10 additional unique files, bringing the cumulative text-level QA count to **98/133 (73.7%)**, with **35 README files remaining**.

The denominator is the 133 dossier README files in the PR #155 changed-file inventory. This is only text-level screening coverage. It is not a percentage of scientifically verified claims, completed A-to-Z dossiers, deployed database import, or overall project completion.

## Status

All 10 dossiers remain `in_progress`. This batch does not establish live regulator verification, production database import, claim-by-claim source validation, or independent scientific sign-off.
