# Scientific Dossier QA — Batch 11

**Scope:** 10 additional dossier READMEs screened on PR #155.  
**Files reviewed:** pegcetacoplan, pegulicianine, pinealon, plecanatide, polymyxin B, pramlintide, retatrutide, rezafungin, rusfertide, and secretin.  
**Method:** structured text-level review of identity, molecular class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. The repository includes complex peptide-related products beyond ordinary peptide therapeutics: PEG-peptide conjugates, activatable optical imaging conjugates, peptide mixtures, lipidated lipopeptide antibiotics and long-acting prodrug-like constructs.
2. Product-level separation is essential for pegcetacoplan (systemic versus intravitreal products), pegulicianine (drug-device imaging workflow), polymyxin B (systemic versus topical products), and distinct product forms of pramlintide and secretin.
3. The dossiers correctly flag important identity and evidence limits: PEG polydispersity, peptide mixtures, uncertain structures, unapproved research compounds and species-specific sequence differences.
4. A numbering inconsistency was found in Secretin: its heading still said 042 although its workbook mapping is 038. This has now been corrected in the PR branch; workbook row position and folder slug remain separate identifiers.

## Dossier-level findings and actions

### 1. Pegcetacoplan
- Correctly classified as a PEG-conjugated cyclic peptide inhibitor of C3/C3b rather than a simple sequence-defined peptide.
- Preserve Empaveli (subcutaneous PNH product) and Syfovre (intravitreal geographic-atrophy product) as separate medicinal products with distinct routes, exposure, indications, efficacy and safety.
- PEG distribution and conjugation heterogeneity mean that one exact molecular mass or simple peptide sequence is inadequate without defining the conjugate distribution and analytical basis.
- Extract PEGASUS/PRINCE and OAKS/DERBY outcomes with exact populations, endpoints, effect estimates and confidence intervals.
- Capture current complement-inhibition infection precautions for each product and keep systemic PNH risks distinct from ocular adverse events. Postmarketing retinal vasculitis/vascular occlusion requires current regulator-source review.
- Add exact peptide sequence, PEG molecular-weight distribution, conjugation-site/occupancy and product-specific CMC evidence from FDA reviews.

### 2. Pegulicianine
- Correctly classified as a protease-activatable optical imaging agent with peptide, dye, quencher and PEG components, not an anticancer therapeutic.
- Preserve the drug application and compatible imaging-device authorization as linked but distinct regulatory entities. The approved workflow is population- and device-specific.
- The mechanism should distinguish intact quenched construct from protease-cleaved fluorescent fragments; fluorescence is an adjunctive surgical signal, not a definitive cancer diagnosis.
- Extract current label sensitivity/specificity, false-positive/false-negative performance, trial populations and safety tables with exact source locators.
- Verify heterogeneous PEG architecture, dye/quencher identity, cleavage sites and approximate molecular-weight range against the FDA structural diagram and CMC record.
- Preserve exact product dose/administration details only as label-derived content; do not turn the research dossier into a clinical procedure guide.

### 3. Pinealon
- Correctly treats Pinealon/EDR as a short research peptide and avoids asserting a validated receptor or molecular target.
- Verify sequence, stereochemistry, termini, counterion and analytical identity from primary chemistry sources before canonical structure assignment.
- Proposed neuroprotective, transcriptional and stress-response mechanisms remain predominantly preclinical; tie each statement to the exact cell/animal model and do not convert it into established human efficacy.
- Replace broad PubMed/Europe PMC searches with exact primary papers, trial registry identifiers and claim-level locators.
- No human PK, standardized medicinal formulation or approved safety profile should be inferred from research-vendor material.
- Maintain not FDA-approved / no verified marketing authorisation status unless a jurisdiction-specific official record is found.

### 4. Plecanatide
- Correctly identifies a 16-residue uroguanylin analogue with two disulfide bonds and GC-C–cGMP–CFTR secretory signalling.
- The label sequence graphic should remain the preferred transcription source, as the dossier itself notes awkward chemical-name formatting. Validate sequence orientation and both disulfide pairings before machine-readable structure import.
- Keep CIC and IBS-C registration endpoints separate; extract current responder definitions and trial-specific rates rather than reporting one pooled efficacy figure.
- Verify current paediatric age restrictions, dehydration warning and obstruction contraindication against the latest label. Do not transfer adult safety rates to paediatric populations.
- Preserve the distinction between intracellular cGMP-mediated secretion and the less established clinical contribution of extracellular cGMP to visceral pain modulation.
- Confirm active-metabolite identity and degradation products with primary/label evidence.

### 5. Polymyxin B
- Correctly classified as a mixture of related cyclic cationic lipopeptide antibiotics, principally polymyxin B1 and B2, rather than one sequence-defined molecule.
- Preserve congener composition and product-specific quality information; do not force one exact sequence or molecular mass onto all polymyxin B materials.
- Correctly distinguishes polymyxin B (administered active drug) from polymyxin E/colistin and colistimethate sodium (a prodrug). Do not transfer CMS conversion factors or units to polymyxin B.
- Separate systemic injectable products from topical ophthalmic/otic formulations because exposure, indications and safety differ.
- Add current product-specific labels, component ratios, PK in critical illness, nephrotoxicity/neurotoxicity frequencies and susceptibility/resistance evidence.
- Keep salvage-use evidence distinct from contemporary preferred therapies; do not imply equivalence to newer active agents.

### 6. Pramlintide
- Correctly records the 37-residue human-amylin analogue, three substitutions, Cys2–Cys7 disulfide and C-terminal amidation.
- Preserve the free peptide and variable-acetate salt as separate chemical forms; the label's free-peptide mass must not be represented as the invariant mass of all acetate/hydrate material.
- The amylin-receptor mechanism and complementary role with mealtime insulin are appropriately described. Do not present pramlintide as an insulin replacement.
- Extract current label contraindications, severe hypoglycaemia rates, nausea, gastric-emptying effects, oral-drug interaction timing and product-specific presentation information.
- Keep Symlin vial and pen presentations, concentrations, excipients and availability distinct by label version.
- Complete pivotal type 1/type 2 diabetes trial tables with sample sizes, HbA1c/postprandial endpoints, weight effects and severe hypoglycaemia outcomes.

### 7. Retatrutide
- Correctly identifies retatrutide as an investigational single-molecule GIPR/GLP-1R/GCGR triagonist and distinguishes it from administration of three separate hormones.
- Preserve Aib and alpha-methyl-L-leucine substitutions, Lys17 lipidation, gamma-glutamyl/AEEA linker, C20 fatty diacid and C-terminal serinamide; the plain 39-residue string is not a complete chemical structure.
- The dossier's stated investigational status is date-bounded (3 November 2026). Recheck official regulator and sponsor records at every release; a planned BLA filing is not a submission or approval.
- Keep trial endpoints and outcomes separated by indication, population, dose arm, estimand and follow-up. Sponsor topline announcements must not substitute for peer-reviewed full datasets or regulator review.
- Do not infer PK, commercial formulation, storage, shelf life, approved dosing or manufacturing specifications from online research-vendor products.
- Add primary receptor pharmacology, clinical PK, immunogenicity and trial-level source locators; preserve uncertainty in potency comparisons across assay systems.

### 8. Rezafungin
- Correctly classified as a semisynthetic cyclic hexapeptide-like echinocandin lipopeptide, not a conventional linear peptide.
- The beta-(1,3)-D-glucan synthase mechanism and FKS resistance context are appropriate; preserve species-specific susceptibility and assay conditions.
- Keep the FDA indication restricted to adults with candidemia/invasive candidiasis who have limited or no alternative options; do not present it as unrestricted first-line replacement for all echinocandins.
- Extract ReSTORE day-14 global-cure endpoint, noninferiority margin, analysis population, confidence intervals and safety results from the primary publication and label.
- Verify the complete stereochemical macrocycle, side chain, salt form, degradation and current product label details.
- The approximately 133-hour terminal half-life must remain label/study-specific and must not be transferred to other echinocandins.

### 9. Rusfertide
- Correctly updated to MIMRYLO and the reported FDA approval on 28 August 2026 for erythrocytosis in adults with polycythemia vera; this supersedes earlier investigational status in the dossier.
- Correctly classified as a modified cyclic disulfide hepcidin mimetic that inhibits ferroportin-mediated iron export, rather than a direct JAK2 inhibitor or cytoreductive chemotherapy.
- Preserve the N-terminal isovaleryl cap, lipidated lysine side chain, Cys-linked disulfide, C-terminal amide and variable-acetate salt stoichiometry.
- Keep free-base formula/mass distinct from the variable acetate salt; do not assign one invariant salt mass.
- Verify the current FDA label, NDA 220605, exact indication, dose-expression basis, safety, PK and postmarketing updates. Label-derived population PK predictions must not be treated as individual exposure targets.
- Extract VERIFY (NCT05210790) endpoints, analysis population, effect estimates, confidence intervals and iron-related safety data with exact locators.

### 10. Secretin
- Correctly distinguishes human and porcine 27-residue C-terminally amidated secretin forms, their sequences and their separate historical/product regulatory records.
- The human sequence and formula should not be copied to porcine secretin; the porcine sequence remains an explicit curation gap.
- The mechanism correctly links SCTR–Gs–adenylyl cyclase–cAMP–CFTR signalling to bicarbonate-rich pancreatic secretion and distinguishes diagnostic stimulation from antitumour therapy.
- Preserve human ChiRhoStim and porcine SecreFlo as separate products, and verify current label/marketing status independently. Historical biologically derived porcine product status must not be conflated with the synthetic product.
- Add exact current label/approval locators for pancreatic exocrine testing, gastrinoma testing and ERCP papilla identification; retain their distinct endpoints and product-specific evidence.
- **Numbering correction made in this batch:** changed the README heading from 042 to 038 to agree with the documented Peptides worksheet position 038 / Excel row 39. This corrects the dossier heading only; it does not change the canonical folder slug or biological identity.

## Cross-cutting implementation requirements

- Support PEG-peptide conjugates, peptide-dye/quencher imaging agents, peptide mixtures, lipidated analogues, endogenous-derived peptides and peptide-like cyclic lipopeptide antibiotics.
- Model active moiety, chemical form/salt, PEG/linker/conjugate, released active fragment, finished product, device, formulation, route, indication, jurisdiction and authorisation as separate linked records.
- Store sequence, noncanonical residues, stereochemistry, disulfide/cyclisation, side-chain conjugation, mixture composition and polymer distribution where relevant.
- Require claim-level source locators for identity, mechanism, PK/PD, clinical outcomes, safety and regulatory assertions.
- Preserve source conflicts, current label versions, as-of dates and product-level status; do not silently normalise different products or jurisdictions.
- Keep dossiers in_progress until official records, primary evidence, claim-level citations and independent review are complete.

## Progress accounting

Batch 10 recorded **98/133** unique dossier README files screened. This batch adds 10 additional unique files, bringing cumulative text-level QA coverage to **108/133 (81.2%)**, with **25 README files remaining**.

The denominator is the 133 dossier README files in the PR #155 changed-file inventory. This is only text-level screening coverage. It is not a percentage of scientifically verified claims, completed A-to-Z dossiers, deployed database import, or overall project completion.

## Status

All 10 dossiers remain in_progress. This batch does not establish live regulator verification, production database import, claim-by-claim source validation, or independent scientific sign-off.
