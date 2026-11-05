# Scientific Dossier QA — Batch 09

**Scope:** 10 additional dossier READMEs screened on PR #155.  
**Files reviewed:** linaclotide, liraglutide, lixisenatide, LL-37, lutetium Lu-177 dotatate, macupatide, mazdutide, melanotan II, melphalan flufenamide, and micafungin.  
**Method:** structured text-level review of identity, chemical class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. The batch reinforces that the repository must support a broad peptide-related ontology, not only conventional linear peptides. It includes locally acting cyclic peptides, lipidated peptide analogues, antimicrobial host-defence peptides, radiometal-chelator-peptide complexes, peptide-conjugated prodrugs and cyclic lipopeptide antifungals.
2. Active-substance identity and medicinal-product identity must remain separate. Liraglutide's Victoza and Saxenda labels, lixisenatide's Adlyxin/Lyxumia and fixed-ratio combinations, and radiopharmaceutical presentations cannot share product-specific indications, strengths, devices, PK or regulatory status by default.
3. Regulatory statements need an as-of date and exact jurisdiction/product scope. China approval of mazdutide does not imply FDA approval; FDA withdrawal of melflufen does not erase the separate EU authorisation; and a historic EU authorisation withdrawal for commercial reasons must not be misclassified as a safety withdrawal.
4. Mechanistic descriptions are generally cautious, but quantitative chemistry, PK, clinical endpoints and current labels remain incomplete. All records stay `in_progress`.

## Dossier-level findings and actions

### 1. Linaclotide
- The dossier correctly describes a 14-residue cyclic peptide with three disulfide bonds and the GC-C–cGMP–CFTR secretory mechanism.
- Preserve the active metabolite as a distinct source-supported pharmacological feature; the clinical contribution of extracellular cGMP to pain modulation should remain qualified as less established.
- Extract the current label's indication-specific adult and paediatric age bands, strengths, responder definitions, efficacy tables and adverse-event frequencies. The paediatric dehydration warning/contraindication and obstruction contraindication require exact label wording and scope.
- Keep CIC and IBS-C trial endpoints separate; do not combine bowel-movement and abdominal-pain outcomes into one generic response measure.
- Validate the sequence, disulfide connectivity and formula against the current label/primary chemical record before canonical structure lock.

### 2. Liraglutide
- The dossier appropriately distinguishes Victoza from Saxenda despite their shared active substance; preserve separate product, indication, device, age, label-version and clinical-evidence records.
- The Lys34-to-Arg substitution and Lys26–γ-Glu–C16 lipid side-chain must be represented as explicit structural modifications; a 31-character sequence alone is not the complete chemical entity.
- Verify formula, mass, sequence numbering, acylation and stereochemistry against an authoritative structural source before importing a canonical structure.
- Extract current product-specific label tables for PK, safety, contraindications, paediatric populations, interactions and pregnancy/lactation. The two labels must not be treated as interchangeable.
- Complete trial-level evidence separately for glycaemic control, cardiovascular outcomes and chronic weight management; disclose population, endpoint, follow-up and comparator.

### 3. Lixisenatide
- Correctly identified as an exendin-4-derived, C-terminally amidated 44-residue GLP-1 receptor agonist with a hexalysine extension.
- Preserve Adlyxin, Lyxumia and insulin-glargine/lixisenatide fixed-ratio combination products as distinct medicinal products. Do not transfer the combination product's formulation or insulin-related safety/PK to lixisenatide monotherapy.
- The dossier's reported EU marketing-authorisation withdrawal on 18 December 2025 is described as a holder-requested commercial withdrawal; verify against the current Union Register and do not label it a safety/effectiveness withdrawal.
- Reconcile the exact sequence, residue count, C-terminal amidation and source-specific leading histidine convention before canonical import.
- Verify current US product marketing status separately from original 2016 approval; approval history does not establish current commercial availability.

### 4. LL-37
- Correctly distinguishes mature 37-residue LL-37 from its hCAP18 precursor and shorter derived fragments; the CAMP gene relationship is useful provenance.
- The membrane-disruptive antimicrobial mechanism and immunomodulatory effects are appropriately presented as context-dependent rather than one validated therapeutic mechanism.
- Add exact primary human-study references and separate in-vitro, animal, exploratory topical human and registered-trial evidence.
- Do not translate in-vitro MIC values into clinical efficacy. Ionic strength, serum proteins, proteolysis, species and cytotoxicity materially affect interpretation.
- Maintain research-only / not FDA-approved status unless a jurisdiction-specific authorised product is independently established. No approved dosing, safety profile or clinical PK should be inferred.

### 5. Lutetium Lu-177 dotatate
- Correctly classified as a radiopharmaceutical peptide conjugate comprising a TATE targeting vector, DOTA chelator and Lu-177 radionuclide—not as a peptide-only drug.
- Model precursor peptide, chelator, radionuclide, radiolabelled active complex and finished medicinal product as linked but distinct entities.
- Keep LUTATHERA and BEXLUTRY product presentations and their label versions separate; verify each product's current indication, age range, concentration, calibration activity and handling instructions from its own official label.
- Distinguish peptide receptor binding/internalisation from the therapeutic mechanism of beta-particle radiation and from gamma-emission imaging/dosimetry.
- Clinical evidence must retain NETTER-1's specific midgut population and endpoint context; do not generalise its results to every GEP-NET subtype or treatment line.
- Extract organ dosimetry, renal protection, marrow exposure, delayed MDS/AML, fertility and radiation-safety requirements with exact source locators. Physical half-life of Lu-177 is not the biological half-life of the conjugate.

### 6. Macupatide
- Correctly identified as investigational LY3532226 and a long-acting GIPR agonist; the dossier appropriately distinguishes monotherapy from combination studies with dulaglutide or eloralintide.
- Preserve USAN/WHO naming and substance identifiers as nomenclature/identity evidence, not marketing authorisation.
- The 39-residue modified backbone, noncanonical residues, lipidated lysine/linker and C-terminal serinamide require a residue-aware chemical representation. The abbreviated sequence is not a complete conventional one-letter sequence.
- Do not infer numerical PK, receptor potency, weight-loss efficacy or tissue-specific effects from lipidation or receptor class alone. Obtain primary receptor and PK datasets.
- Reconcile ClinicalTrials.gov records and results for each study; sponsor pipeline tables are not substitutes for registry results or peer-reviewed primary publications.
- Disclose sponsor involvement in the Phase 1b publication and keep its clamp-derived outcomes distinct from long-term clinical benefit.

### 7. Mazdutide
- Correctly identified as a dual GLP-1R/GCGR agonist with China-specific approval history and explicit non-equivalence to FDA approval.
- The dossier appropriately flags a material discrepancy between public chemical structure/formula records rather than forcing a single formula or mass. Preserve the FDA GSRS sequence/modification description and keep unresolved chemistry fields unresolved pending structure-level reconciliation.
- Verify the current Chinese product insert and NMPA product record for exact indications, age/BMI criteria, formulation, dose, warnings and authorisation details. Sponsor announcements are not substitutes for the official label.
- Keep obesity and type 2 diabetes trials separate, and distinguish early-phase findings from pivotal Phase 3 outcomes.
- Verify trial identifiers, current registry status, primary publications and complete efficacy/safety tables. Do not infer results from study completion or sponsor pipeline milestones.
- Do not treat a GSRS UNII, USAN or proposed INN as proof of FDA or global approval.

### 8. Melanotan II
- Correctly distinguishes Melanotan II from afamelanotide and bremelanotide; shared melanocortin pharmacology does not imply equivalent identity, indication, efficacy or regulatory status.
- Preserve the cyclic heptapeptide's stereochemistry, lactam connectivity and terminal modifications; validate the exact structure against primary chemistry sources before canonical registration.
- The nonselective melanocortin-receptor mechanism should be tied to exact receptor assays and not converted into a clinically established tanning or sexual-dysfunction claim.
- Replace broad regulator and search links with exact primary studies and jurisdiction-specific regulator records. The dossier currently has insufficient claim-level citations for several safety and human-evidence statements.
- Maintain not FDA-approved / not an authorised tanning medicine status; no use, dose or administration guidance should be added.

### 9. Melphalan flufenamide (melflufen)
- Correctly classified as a peptide-conjugated nitrogen-mustard prodrug rather than a conventional therapeutic peptide. The peptide-like delivery element and released melphalan cytotoxic payload must be represented separately.
- Preserve free-base and hydrochloride chemical forms and their identifiers; do not convert labelled active-equivalent strength using a salt molecular weight without the product specification.
- The US FDA withdrawal effective 23 February 2024 is distinguished from a commercial discontinuation and from the separate EU Pepaxti authorisation. Verify the latest EU SmPC and Union Register status before displaying a current status.
- Retain the confirmatory OCEAN trial's prespecified analysis and FDA benefit-risk conclusion; do not substitute sponsor reanalysis for the regulatory interpretation.
- Complete quantitative PK for parent melflufen and released melphalan separately, and add claim-level locators for efficacy, survival, safety and CMC assertions.
- Do not infer India/CDSCO approval or availability without an official product record.

### 10. Micafungin
- Correctly classified as a semisynthetic echinocandin cyclic lipopeptide, not a conventional linear peptide; represent the macrocycle, lipid side chain and non-proteinogenic residues explicitly.
- The beta-(1,3)-D-glucan synthase mechanism and FKS-mediated resistance context are appropriate.
- Extract current Mycamine label age bands, indications, renal/hepatic considerations, interaction data and adverse-event frequencies. Distinguish invasive candidiasis, esophageal candidiasis and HSCT prophylaxis evidence.
- Add pivotal trial identifiers, population, comparator, endpoints and effect estimates; do not generalise one indication's evidence to all Candida or Aspergillus infections.
- Verify exact salt-specific identifiers, stereochemical structure and current marketed product status.

## Cross-cutting implementation requirements

- Maintain an ontology that supports cyclic peptides, lipidated analogues, antimicrobial peptides, radiopharmaceutical complexes, peptide-conjugated prodrugs and cyclic lipopeptide antibiotics.
- Store active substance, chemical form/salt, conjugate, radionuclide, finished product, formulation, presentation, indication, jurisdiction and authorisation as separate linked entities.
- Represent noncanonical residues, D/L stereochemistry, side-chain modifications, terminal chemistry, disulfides, lactam links, chelators and lipid conjugates explicitly.
- Require claim-level source locators for sequence, chemistry, mechanism, PK/PD, clinical outcomes, safety and regulatory statements.
- Preserve conflicting source values with provenance and review status; do not average or silently overwrite discrepancies.
- Treat trial registry status, sponsor announcements, nomenclature assignments and database identifiers as distinct evidence types.
- Keep all dossiers `in_progress` until current official labels/regulator records, primary evidence, source locators and independent review are complete.

## Progress accounting

Batch 08 recorded **78/133** unique dossier README files screened. This batch adds 10 additional unique files, bringing the cumulative text-level QA count to **88/133 (66.2%)**, with **45 README files remaining**.

The denominator is the 133 dossier README files in the PR #155 changed-file inventory. This is only text-level screening coverage. It is not a percentage of scientifically verified claims, completed A-to-Z dossiers, deployed database import, or overall project completion.

## Status

All 10 dossiers remain `in_progress`. This batch does not establish live regulator verification, production database import, claim-by-claim source validation, or independent scientific sign-off.
