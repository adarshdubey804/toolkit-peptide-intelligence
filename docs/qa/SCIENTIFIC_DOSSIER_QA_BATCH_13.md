# Scientific Dossier QA — Batch 13

**Scope:** 10 additional dossier READMEs screened on PR #155.  
**Files reviewed:** terlipressin, tesamorelin, thymosin alpha-1, tirzepatide, triptorelin, trofinetide, vancomycin, vasopressin, voclosporin, and vosoritide.  
**Method:** structured text-level review of identity, molecular class, sequence/modifications, mechanism, product boundaries, evidence grading, regulatory wording and provenance gaps. This is not independent claim-by-claim verification against live regulator databases or primary literature.

## Executive findings

1. This batch contains peptide hormones and analogues, a tripeptide-derived neuroactive medicine, a cyclic undecapeptide immunosuppressant and complex glycopeptide antibiotics. The repository must retain a broad peptide-related ontology and not force all records into the same linear-sequence schema.
2. The most important product boundaries are the multiple tesamorelin presentations, tirzepatide products, triptorelin depot formulations, intravenous versus oral vancomycin, and product-/jurisdiction-specific vasopressin and thymalfasin records.
3. Terlipressin's README is still a generic dossier scaffold and requires substantial molecule-specific completion. Trofinetide's precise clinical mechanism also remains incompletely established and should not be overstated.
4. A malformed AURORA 2 registry identifier in the voclosporin reference list was corrected from an invalid string to NCT03597448 in this branch.

## Dossier-level findings and actions

### 1. Terlipressin
- The current dossier correctly identifies terlipressin as a vasopressin prodrug analogue converted to lysine-vasopressin, with V1-mediated splanchnic vasoconstriction as the principal pharmacological rationale in hepatorenal syndrome.
- The README remains largely a generic scaffold: exact residue modifications, sequence, prodrug cleavage, active metabolite identity, formula/mass, label-specific PK, pivotal clinical results and source locators are missing.
- Build a molecule-specific structure record that distinguishes terlipressin from lysine-vasopressin and native vasopressin. Do not infer the prodrug structure from the active metabolite.
- Extract the current TERLIVAZ label's boxed warning for serious/fatal respiratory failure, contraindications, oxygenation/volume status requirements and ischemic complications with exact wording and locators.
- Capture CONFIRM trial population, primary endpoint, response definition, renal-reversal results, transplant-free survival and mortality outcomes separately. Do not equate renal function improvement with a proven overall survival benefit.
- Verify the workbook's 2022 US approval date against the FDA NDA/action record and keep other jurisdictions separate.

### 2. Tesamorelin
- Correctly identifies tesamorelin as a 44-residue GHRH analogue with N-terminal trans-3-hexenoyl modification, C-terminal amidation and acetate salt.
- Preserve Egrifta, Egrifta SV and Egrifta WR as distinct products/presentations with separate vial strengths, reconstitution, excipients, devices and label versions.
- Do not generalise the narrow indication (reduction of excess abdominal fat in HIV-infected adults with lipodystrophy) to common obesity or general weight-loss management.
- The full 44-residue sequence string is not a complete chemical structure without the covalent N-terminal hexenoyl modification and salt basis; verify stereochemistry and structural graph against the FDA diagram.
- Extract current formulation-specific PK, immunogenicity, IGF-1, glucose homeostasis, contraindications and safety tables. Do not transfer bioavailability or stability between presentations without comparability evidence.
- Capture the relevant clinical programme and effect estimates with exact population, endpoints and follow-up; distinguish VAT reduction from total body-weight loss.

### 3. Thymosin alpha-1 (thymalfasin)
- Correctly identifies thymalfasin as an N-terminally acetylated 28-residue fragment of prothymosin alpha, distinct from full-length prothymosin alpha and historical thymosin fractions.
- Preserve the N-terminal acetylation and product-specific salt/counterion; verify formula/mass against each national medicinal product rather than assuming a universal form.
- The dossier appropriately describes pleiotropic immunomodulatory effects without asserting one validated receptor. TLR, dendritic-cell, cytokine and T-cell findings must be tied to specific experimental models.
- Maintain not FDA-approved status separately from selected-country authorisations. Verify country, product, indication, current registration and label in each official national register.
- Systematically review randomized trials and meta-analyses by indication, background therapy, risk of bias and geography. Separate immunological biomarkers from clinical outcomes such as mortality or virological response.
- Do not describe thymalfasin as a universal immune booster or infer global guideline endorsement from a local authorization.

### 4. Tirzepatide
- Correctly identifies tirzepatide as a 39-residue modified GIP-based peptide with dual GIPR/GLP-1R agonism, Aib substitutions, Lys20 linker/lipid conjugation and C-terminal amidation.
- Preserve Mounjaro and Zepbound as separate product/label records with indication, presentation, device, strength, safety and regulatory history differences.
- The plain sequence string is not the complete drug-substance identity; encode Aib stereochemistry, Lys20 side-chain conjugation, linker connectivity and C-terminal chemistry explicitly.
- Verify current product labels for indication expansions, age ranges, contraindications, warnings, dose instructions, pregnancy/lactation and interactions; do not transfer trial outcomes between diabetes and obesity populations.
- Extract SURPASS and SURMOUNT programme endpoints separately, with registry identifiers, populations, estimands, treatment duration and confidence intervals.
- Keep formula/mass tied to the exact active substance and distinguish salt/counterion and finished-product formulation.

### 5. Triptorelin
- The dossier requires strict separation of triptorelin active peptide, pamoate salt and depot medicinal products. Immediate-release and long-acting depot presentations are not interchangeable.
- Preserve the GnRH agonist biphasic mechanism: initial LH/FSH flare followed by pituitary receptor desensitisation/downregulation during sustained exposure.
- Verify the exact decapeptide sequence, D-Trp6 substitution, pyroglutamyl N-terminus, C-terminal glycinamide and pamoate stoichiometry from authoritative label/chemistry sources.
- Keep product-specific indications, routes, depot technology, release characteristics, age limits and regulatory status separate by brand and jurisdiction.
- Extract trial and label evidence for prostate cancer, central precocious puberty and other product-specific indications without generalising one depot product's approval to another.
- Capture flare-related risks, sex-steroid suppression, bone effects, metabolic effects, QT considerations and paediatric monitoring with exact label locators.

### 6. Trofinetide
- Correctly classify trofinetide as a synthetic analogue of the N-terminal tripeptide Gly-Pro-Glu (GPE), with a narrow Rett syndrome indication rather than a conventional peptide-hormone agonist.
- The precise clinical mechanism is not fully established. Proposed effects on synaptic function, neuroinflammation and neurotrophic signalling should remain hypotheses unless supported by direct target/assay evidence.
- Verify exact chemical identity, stereochemistry, terminal chemistry, salt form and identifiers from the current DAYBUE label and FDA chemistry review.
- Extract the pivotal LAVENDER trial design, Rett syndrome population, RSBQ and CGI-I outcomes, effect estimates, confidence intervals and missing-data methods.
- Capture the current label's diarrhoea, vomiting, weight loss, hydration, renal impairment and drug-interaction information; keep adult and paediatric safety context clear.
- Do not extrapolate the indication to other neurodevelopmental disorders or claim disease modification beyond the evidence.

### 7. Vancomycin
- Correctly classifies vancomycin as a complex fermentation-derived glycopeptide antibiotic with a rigid, glycosylated scaffold, not a sequence-defined peptide drug.
- Preserve oral and intravenous products as separate formulations and clinical records. Oral intestinal exposure for C. difficile infection is not equivalent to IV systemic treatment.
- The D-Ala-D-Ala binding mechanism and D-Ala-D-Lac/D-Ala-D-Ser resistance distinction are appropriate; add organism- and assay-specific susceptibility evidence.
- Reconcile the workbook's historical 1958 date against exact FDA product/application history. The oral capsule label's 1986 initial-approval date must not be presented as the first-ever vancomycin approval.
- Add current AUC-guided therapeutic monitoring evidence and avoid presenting trough-only targets as universal contemporary practice.
- Capture renal toxicity, infusion reactions, ototoxicity, cytopenias, hypersensitivity and systemic absorption from oral formulations in the relevant label/population context.

### 8. Vasopressin
- Correctly identifies mature arginine vasopressin as a cyclic nonapeptide with Cys1–Cys6 disulfide and C-terminal glycinamide.
- Preserve AVPR1A/V1a, AVPR1B/V1b and AVPR2/V2 as distinct receptor pathways with Gq/11 versus Gs signalling; do not describe vasopressin as V1a-selective.
- Keep Vasostrict, historical Pitressin and other national products separate by manufacturer, concentration, excipients, route, indication and label version.
- Verify the 2014 date as applying to the current Vasostrict formulation rather than the first historical use or approval of vasopressin.
- Extract current label haemodynamic use, dose-related ischaemia, hyponatraemia/water retention, cardiac effects and monitoring with exact source locators.
- Distinguish pharmaceutical vasopressin from desmopressin and terlipressin; their receptor selectivity, prodrug status, PK and indications differ.

### 9. Voclosporin
- Correctly classifies voclosporin as a semisynthetic cyclic undecapeptide calcineurin inhibitor, not a linear peptide.
- Preserve the modified residue and stereochemical structure relative to cyclosporine A; exact formula, mass and structure must be taken from FDA chemistry sources.
- The cyclophilin–calcineurin–NFAT mechanism is appropriate. The proposed podocyte-stabilising contribution should remain qualified rather than being presented as the sole proven clinical mechanism.
- Keep Lupkynis and its oral formulation distinct from cyclosporine products and other calcineurin inhibitors.
- Extract AURORA 1 and AURORA 2 renal response endpoints, effect estimates, confidence intervals, background immunosuppression and long-term safety.
- Capture CYP3A4/P-glycoprotein interaction restrictions, nephrotoxicity, hypertension, hyperkalaemia, serious infection and malignancy warnings from the current label.
- **Reference correction made in this batch:** repaired the malformed AURORA 2 registry link to NCT03597448. This corrects the identifier string; the registry record and linked primary publication still require curator verification.

### 10. Vosoritide
- Correctly identifies vosoritide as a recombinant 39-residue CNP analogue with an N-terminal Pro-Gly extension and NPR-B/NPR2–cGMP signalling.
- Preserve the exact 39-residue sequence, disulfide connectivity, stereochemistry and recombinant production details from the current official label.
- Keep the achondroplasia indication limited to paediatric patients with open epiphyses; do not claim that vosoritide corrects the underlying FGFR3 mutation or reverses achondroplasia.
- Track the label's age-range expansions and current eligibility wording by date and jurisdiction.
- Extract the pivotal phase 3 annualized growth velocity effect estimate, confidence interval, analysis population and longer-term outcomes.
- Capture transient hypotension, hydration, injection-site reactions and current renal/age/weight limitations from the latest label.
- Distinguish growth-velocity surrogate evidence from patient-centred functional outcomes and any confirmatory postmarketing requirements.

## Cross-cutting implementation requirements

- Support modified peptide hormones, peptide analogues, cyclic immunosuppressants, peptide-derived neuroactive compounds and complex glycopeptide antibiotics.
- Model active substance, salt, prodrug, active metabolite, depot formulation, finished product, route, indication, jurisdiction and authorisation as separate linked entities.
- Store noncanonical residues, stereochemistry, terminal modifications, disulfides, linker/lipid conjugation, glycosylation and fermentation-derived component profiles where relevant.
- Require claim-level citations and exact locators for identity, mechanism, PK/PD, clinical outcomes, safety and regulatory assertions.
- Preserve product-specific labels, current as-of dates, source conflicts and historical approval context; do not merge oral/IV or depot/immediate-release records.
- Keep all dossiers in_progress until official records, primary evidence, claim-level citations and independent review are complete.

## Progress accounting

Batch 12 recorded **118/133** unique dossier README files screened. This batch adds 10 additional unique files, bringing cumulative text-level QA coverage to **128/133 (96.2%)**, with **5 README files remaining**.

The denominator is the 133 dossier README files in the PR #155 changed-file inventory. This is only text-level screening coverage. It is not a percentage of scientifically verified claims, completed A-to-Z dossiers, deployed database import, or overall project completion.

## Status

All 10 dossiers remain in_progress. This batch does not establish live regulator verification, production database import, claim-by-claim source validation, or independent scientific sign-off.
