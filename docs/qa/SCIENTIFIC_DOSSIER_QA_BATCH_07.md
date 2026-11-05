# Scientific Dossier QA — Batch 07

**Scope:** 10 additional dossier READMEs screened on PR #155.
**Files reviewed:** Cortagen, corticotropin (ACTH), cosyntropin, cyclosporine, dalbavancin, daptomycin, indium In-111 pentetreotide, insulin aspart, insulin degludec, and insulin detemir.
**Method:** structured text-level review for identity, molecular class, product/formulation boundaries, mechanism, evidence grading, regulatory wording, and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature. No dossier is promoted to complete.

## Executive findings

1. Entity ontology must extend beyond conventional peptides. Dalbavancin is a semisynthetic lipoglycopeptide; daptomycin is a cyclic lipopeptide; indium In-111 pentetreotide is a radiolabelled peptide-chelator complex. Cyclosporine is a cyclic undecapeptide with extensive non-proteinogenic and N-methylated chemistry. These records must not be forced into a linear-sequence-only model.
2. Product identity must be distinct from active-substance identity. ACTH repository gel, purified corticotropin gel, and synthetic ACTH(1–24) are not interchangeable records. Insulin aspart, degludec, and detemir each require product/formulation and jurisdiction-specific label records.
3. Mechanistic plausibility is not proof of clinical benefit for every indication or product.
4. Historical approval dates, current marketed status, indication wording, label revision, and product-specific restrictions need direct regulator-source verification.

## Dossier-level findings and actions

### 1. Cortagen (AEDP)
- Correctly avoids claiming a validated molecular target or established human efficacy.
- Sequence, stereochemistry, terminal chemistry, CAS/PubChem mapping and reported identity require primary-source confirmation before canonical structure lock.
- Replace or augment secondary databases and broad PubMed search links with exact primary analytical and experimental publications.
- Keep preclinical findings explicitly separated from human evidence; jurisdictional register checks are still required for any exhaustive regulatory claim.

### 2. Corticotropin (ACTH; repository and purified gels)
- Strong distinction between human endogenous ACTH(1–39), complex porcine-derived repository corticotropin, and separately manufactured purified corticotropin.
- Create separate product entities for Acthar Gel and Cortrophin Gel, each with its own label, composition, manufacturing provenance, indications, warnings and regulatory history.
- Do not attach the human ACTH sequence as the exact composition of repository corticotropin.
- Verify the historical 1952 date and contemporary indications against FDA application history and current labels. Avoid a single universal ACTH approval date or pooled safety/PK record.

### 3. Cosyntropin (ACTH 1–24)
- Useful separation from full-length ACTH and correct diagnostic role / MC2R–MRAP–Gs–cAMP–PKA pathway framing.
- Verify precise terminal chemistry, including C-terminal amidation, acetate/salt form, sequence, formula and molecular mass against an authoritative product/chemical record.
- Standard-dose and low-dose test protocols belong as clinical-protocol evidence, not product dosing advice; cortisol interpretation must be assay-specific.
- Current product availability, labels, jurisdictional approvals and exact diagnostic instructions remain open.

### 4. Cyclosporine
- Correctly identifies a cyclic undecapeptide and cyclophilin–calcineurin–NFAT immunosuppressive mechanism.
- Do not model the macrocycle as a simple linear peptide; capture residue stereochemistry, N-methylation, noncanonical residues and ring connectivity.
- Split systemic oral/IV products from ophthalmic formulations. Sandimmune, Neoral, Gengraf and Restasis must not share PK, indications, formulation or safety fields indiscriminately.
- Extract product-specific label data, therapeutic drug monitoring context and formulation bioavailability evidence.

### 5. Dalbavancin
- Correctly classified as a semisynthetic lipoglycopeptide antibiotic rather than a conventional linear peptide.
- Use a chemical-structure / glycopeptide-component representation, not a single amino-acid sequence.
- Keep labelled ABSSSI evidence distinct from off-label osteomyelitis, bacteremia or endocarditis reports.
- Verify current US label, paediatric restrictions, renal adjustment and trial endpoints directly; long half-life and AUC/MIC statements need study-context provenance.

### 6. Daptomycin
- Correctly identifies cyclic lipopeptide architecture, calcium-dependent membrane activity, Gram-positive spectrum and pulmonary surfactant limitation.
- Capture macrocycle stereochemistry, ester linkage, noncanonical residues and decanoyl lipid tail in structured chemistry.
- Labelled skin infection and S. aureus bacteremia/right-sided endocarditis indications must remain distinct from off-label deep infection use; do not infer pneumonia efficacy.
- Verify current label-specific renal adjustment, CPK monitoring and pivotal trial data.

### 7. Indium In-111 pentetreotide (OctreoScan)
- Strong distinction between diagnostic gamma-emitting imaging agent, unlabelled DTPA-pentetreotide precursor, Ga-68 DOTATATE PET tracers and Lu-177 therapeutic agents.
- Model as linked components: peptide ligand + chelator + radionuclide + final radiolabelled product. Do not assign one formula/CAS/UNII across precursor and radiocomplex without confirmation.
- Verify current NDA/label, marketing status, radiochemical preparation, activity, imaging schedule and dosimetry from official documents.
- Diagnostic performance claims require original-study denominators, reference standards and patient-versus-lesion distinction. Do not infer therapeutic antitumour effect from receptor-targeted imaging.

### 8. Insulin aspart
- Correctly identifies ProB28Asp substitution and insulin-receptor agonism; distinguishes NovoLog from Fiasp and premixed products.
- Preserve chain-level sequence and disulfide topology as structured data, independently validated against authoritative product/structure sources.
- Create separate product records for NovoLog, Fiasp and premixed insulin-aspart products; formulation-dependent PK/PD, age indications, routes and pump compatibility must not be copied across products.
- Complete label PK, safety frequencies, interaction details and pivotal trial bibliography.

### 9. Insulin degludec
- Correctly distinguishes B30 deletion and LysB29 γ-Glu/C16 side-chain modification; explains multi-hexamer depot and albumin binding as contributors to prolonged exposure.
- Validate exact chain sequence, disulfide connectivity, chemical identity and formula against the current authoritative label/structure record.
- U-100/U-200 presentation, device, excipients and jurisdiction-specific indications must be represented at product level.
- Current label extraction, trial-level evidence, interactions, special populations and marketed status by jurisdiction remain incomplete.

### 10. Insulin detemir
- Correctly identifies B30 deletion and LysB29 C14 acylation, insulin receptor mechanism and albumin-binding contribution.
- Verify chain sequence, disulfide connectivity and atom-level modification before canonical structure import.
- The dossier usefully distinguishes historical FDA approval from presentation-level discontinued marketing status; verify each presentation and date from the current FDA source before publication.
- Current non-US status, complete label safety/interaction data, pivotal trial records and commercial landscape remain open.

## Cross-cutting implementation requirements

- Add controlled entity classes for cyclic peptide, modified peptide/protein, lipopeptide, lipoglycopeptide, peptide-chelator conjugate, radiopharmaceutical complex, peptide mixture and recombinant fusion/large peptide biologic.
- Support multi-component substance records and explicit precursor-to-final-product relationships.
- Store sequence, chemical structure, stereochemistry, termini, crosslinks, conjugates, radionuclide and salt/counterion as distinct typed fields; never infer sequence for non-sequence-defined mixtures.
- Separate active substance, medicinal product, formulation, presentation, indication, jurisdiction and regulatory status.
- Attach evidence to individual claims with source type, source identifier/URL, access date, population/model, endpoint and evidence level.
- Preserve in_progress until primary-source checks, import validation and independent review are complete.

## Progress accounting correction

The prior running total incorrectly counted GHK-Cu twice because it appeared in both Batch 02 and Batch 05. Unique dossier coverage before this batch was **58/133**, not 59/133. This batch adds 10 new unique dossiers, bringing cumulative unique README review count to **68/133 (51.1%)**, with **65 README files remaining**. The denominator is the 133 dossier README files in the PR changed-file inventory; this is a text-level QA coverage count, not a completion percentage for the database or scientific validation.

## Status

All 10 dossiers remain in_progress. This batch does not establish production database import, current regulatory verification, or scientific dossier completion.
