# Scientific Dossier QA — Batch 12

**Scope:** 10 additional dossier READMEs screened on PR #155.  
**Files reviewed:** semaglutide, Semax, sermorelin, setmelanotide, sincalide, survodutide, TB-500, teduglutide, telavancin, and teriparatide.  
**Method:** structured text-level review of identity, molecular class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. This batch contains multiple modified peptide medicines, investigational peptides, a diagnostic secretagogue and a semisynthetic lipoglycopeptide antibiotic. Product-level and entity-level distinctions remain essential.
2. Semaglutide products and formulations, setmelanotide's genotype-defined indications, sermorelin's historical products, and teriparatide's current label must not be collapsed into generic class records.
3. Survodutide and TB-500 illustrate why unresolved identity and research-only status must be explicit. Vendor strings and parent-protein biology are not substitutes for a verified drug-substance structure or clinical evidence.
4. Two text-quality issues were corrected during this batch: Teriparatide's molecular-weight sentence contained an obvious stray “GOT” typo; it now reads as an approximate value with an explicit verification qualifier.

## Dossier-level findings and actions

### 1. Semaglutide
- Correctly identifies semaglutide as a 31-residue GLP-1 analogue with Aib at position 8, Lys26 lipidation through a hydrophilic spacer/C18 fatty diacid, and Lys34Arg substitution.
- Preserve Ozempic, Rybelsus and Wegovy as distinct products with different dosage forms, indications, strengths, administration instructions, label versions and regulatory histories.
- The plain sequence string is not a complete structure because Aib and the covalent Lys26 lipid/linker must be represented explicitly. Verify residue numbering and atom-level structure before canonical import.
- Extract current product-specific PK/PD, safety, contraindications, trial outcomes, age bands and interactions; do not transfer outcome values between oral and injectable products or between diabetes and weight-management populations.
- Distinguish GLP-1R mechanism from proposed causal explanations for cardiovascular or renal outcomes; do not overstate pathways that are not fully established.
- Keep label-derived molecular formula/mass tied to the active substance and distinguish it from formulated tablets or injections.

### 2. Semax
- Correctly identifies Semax as an ACTH(4–7)-derived heptapeptide and does not assert a validated direct receptor target.
- Preserve the exact chemical form, terminal chemistry, acetylation/salt and stereochemistry of each specific registered product; a generic sequence alone is insufficient.
- Reported Russian clinical use must be verified against the current Russian state register and product-specific approved information. Literature reports and secondary regulatory summaries are not sufficient to assert current registration or indication.
- Preclinical BDNF/NGF/Trk transcript changes must remain model-specific and must not be presented as proof of a direct target or clinical mechanism.
- Human efficacy evidence is limited by study design/reporting and independent replication; do not claim nootropic benefit in healthy people.
- FDA compounding safety concerns are not an approval or a quantified clinical risk estimate; preserve the exact FDA source scope.

### 3. Sermorelin
- Correctly distinguishes the 29-residue GHRH(1–29) amide from full-length 44-residue GHRH and tesamorelin.
- The GHRHR–Gs–adenylyl cyclase–cAMP mechanism is appropriate, with dependence on functional pituitary somatotroph tissue.
- Preserve historical GEREF diagnostic and therapeutic product/label contexts separately. Historical approval and commercial discontinuation must not be presented as current marketed approval or as evidence that compounded products are FDA-approved.
- Verify sequence, terminal amide, acetate form, formula/mass and historical NDA action dates from primary chemistry and FDA sources.
- The dossier's removal of the erroneous 055 sequence heading is correct; retain workbook row position and canonical folder slug as distinct identifiers.
- Complete historical clinical studies, label safety, current jurisdictional status and claim-level references before curation completion.

### 4. Setmelanotide
- Correctly classified as a cyclic heptapeptide MC4R agonist with N-terminal acetylation, D-Ala/D-Phe stereochemistry, disulfide cyclisation and C-terminal amidation.
- Verify exact residue order, ring connectivity and chemical identifiers against the current official structural formula before canonical import.
- Keep approved populations separate: POMC/PCSK1 deficiency, LEPR deficiency and Bardet–Biedl syndrome, plus any later label-expanded indications only after official verification.
- Do not generalise approval to common obesity or all genetic obesity. Exact gene variants, testing requirements, age thresholds and indication language are label-version- and jurisdiction-specific.
- Extract current label PK, titration, safety and clinical outcomes by genetic cohort; do not pool distinct rare-disease populations into one efficacy estimate.
- Quantitative receptor selectivity/potency claims require primary assay evidence and cannot be inferred from MC4R classification alone.

### 5. Sincalide
- Correctly classified as a modified CCK-related octapeptide diagnostic secretagogue, not a treatment for gallbladder disease.
- Preserve O-sulfated tyrosine and C-terminal amidation as integral chemical modifications; verify exact salt, formula, mass and product specification from official records.
- The CCK1–Gq/11–PLC–IP3/DAG–calcium mechanism is appropriate for gallbladder contraction and pancreatic acinar secretion.
- Keep hepatobiliary scintigraphy and pancreatic-function testing as separate diagnostic applications with their own validated protocols, endpoints and reference ranges.
- The dossier appropriately flags historical FDA product status as distinct from current marketing/label status. Verify Kinevac availability and current label before asserting present commercial status.
- Add exact label and primary nuclear-medicine protocol citations; do not treat gallbladder ejection fraction as a stand-alone diagnosis or transfer reference ranges across infusion protocols.

### 6. Survodutide
- Correctly distinguishes survodutide as a dual GCGR/GLP-1R agonist from retatrutide's GIPR/GLP-1R/GCGR triagonism.
- The dossier appropriately withholds sequence, formula, mass and identifiers where secondary sources conflict. Do not populate canonical chemical fields from vendor catalogues.
- Resolve complete stereochemistry, noncanonical residues, terminal chemistry, lipid/linker attachment and salt form against USAN/GSRS and primary discovery chemistry before structure registration.
- Preserve investigational status as date-bounded (3 November 2026); Phase 3 participation or sponsor pipeline announcements do not establish approval.
- Separate obesity, type 2 diabetes and MASH/cirrhosis trial populations and outcomes. Do not pool them into a single efficacy claim.
- Extract primary receptor potency/bias, clinical PK, immunogenicity and Phase 3 results with assay/trial context; do not infer half-life, product concentration or storage from structure or research vendors.

### 7. TB-500
- Correctly distinguishes the seven-residue TB-500 fragment from full-length thymosin beta-4 and does not automatically transfer actin-sequestration or cell-migration biology to the fragment.
- Preserve the exact N-terminal acetylation, sequence, termini and salt/derivative identity; the common name has been applied inconsistently to chemically different materials.
- A clinically validated mechanism, human PK profile, controlled efficacy package and standardized safety profile are not established in the dossier.
- FDA compounding review concerns must be tied to the exact bulk-substance entry and not described as approval or a definitive clinical risk quantification.
- Keep not FDA-approved / no verified authorised product status; do not add dosing, recovery or wound-healing efficacy claims from full-length thymosin beta-4 studies.
- Replace broad or weak references with exact FDA documents and primary fragment-specific studies.

### 8. Teduglutide
- Correctly identifies teduglutide as a 33-residue GLP-2 analogue with Ala2 substitution and GLP2R–Gs–cAMP signalling.
- Verify sequence orientation, formula and mass against the current product label; distinguish the active peptide from the finished Gattex product.
- Keep adult and paediatric SBS evidence separate, including the current paediatric age threshold and population dependent on parenteral support.
- The STEPS primary endpoint should retain its exact response definition, sample size, analysis population, effect estimate and confidence interval. Reduced parenteral support is not synonymous with guaranteed independence.
- Extract current malignancy/neoplasia warnings, screening and surveillance, obstruction, biliary/pancreatic risks, fluid overload and oral-drug absorption effects with exact label locators.
- Complete renal impairment PK and dose-adjustment details; do not transfer values across populations without qualification.

### 9. Telavancin
- Correctly classified as a semisynthetic lipoglycopeptide derived from the vancomycin scaffold, not a linear peptide.
- Preserve its two major structural modifications and use a complete chemical representation rather than a peptide sequence.
- Extract current label renal thresholds, dose adjustment, boxed warning and contraindications exactly. The increased mortality signal in patients with pre-existing moderate/severe renal impairment treated for HAP/VAP is a critical product/population-specific benefit-risk boundary.
- Keep complicated skin infection and HAP/VAP indications separate, including the restriction that pneumonia use is for adults when alternative treatments are not suitable.
- Add ATTAIN and skin-infection trial endpoints, renal subgroup analyses, comparator details and confidence intervals.
- Verify current product marketing status and latest label; do not infer telavancin PK or dose adjustment from vancomycin.

### 10. Teriparatide
- Correctly identifies teriparatide as human PTH(1–34), a PTH1R agonist whose net skeletal effect depends on intermittent exposure rather than continuous PTH signalling.
- Preserve the 34-residue sequence and distinguish it from full-length PTH(1–84), palopegteriparatide conjugate and other PTH analogues.
- Current label wording must replace obsolete historical boxed-warning/lifetime-duration text; the dossier appropriately notes the 2020 removal of the US boxed warning and lifetime-use limitation, but current label language should be checked at release.
- Extract current product-specific indications, contraindications, PK, calcium effects, renal impairment, safety and administration-device instructions from current labels.
- Keep FORTEO and other brands/generics as separate product records with their own concentrations, devices, excipients and jurisdictional approvals.
- **Text correction made in this batch:** corrected the molecular-weight sentence's stray “GOT” typo to “approximately 4,118 Da; verify the exact displayed value and counterion/formulation basis against the current product label.” This is a wording correction, not independent validation of the numeric value.

## Cross-cutting implementation requirements

- Support modified peptide hormones, lipidated GLP-1 analogues, cyclic melanocortin peptides, diagnostic secretagogues, peptide fragments, peptide-protein conjugates and semisynthetic lipoglycopeptide antibiotics.
- Model active substance, salt/form, linker/lipid conjugate, finished product, formulation, device, route, indication, jurisdiction and authorisation as separate linked records.
- Store noncanonical residues, stereochemistry, terminal chemistry, disulfide/cyclisation, sulfation, side-chain conjugation and sequence checksums explicitly.
- Require claim-level citations and exact locators for identity, mechanism, PK/PD, clinical outcomes, safety and regulatory assertions.
- Preserve uncertainty and source conflicts; do not infer identity from names, vendor sequences, class pharmacology or parent-protein biology.
- Keep all dossiers in_progress until current official records, primary evidence, claim-level citations and independent review are complete.

## Progress accounting

Batch 11 recorded **108/133** unique dossier README files screened. This batch adds 10 additional unique files, bringing cumulative text-level QA coverage to **118/133 (88.7%)**, with **15 README files remaining**.

The denominator is the 133 dossier README files in the PR #155 changed-file inventory. This is only text-level screening coverage. It is not a percentage of scientifically verified claims, completed A-to-Z dossiers, deployed database import, or overall project completion.

## Status

All 10 dossiers remain in_progress. This batch does not establish live regulator verification, production database import, claim-by-claim source validation, or independent scientific sign-off.
