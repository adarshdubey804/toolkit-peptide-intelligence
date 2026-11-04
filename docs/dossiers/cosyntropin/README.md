# 044 — Cosyntropin (synthetic corticotropin; ACTH 1–24)

**Curation status:** in_progress  
**Workbook sequence:** 044  
**Entity class:** synthetic peptide hormone fragment; diagnostic adrenal secretagogue  
**Evidence cut-off:** 4 November 2026

> **Scope.** Cosyntropin is the synthetic N-terminal 24-amino-acid fragment of human adrenocorticotropic hormone (ACTH). It is used to stimulate adrenal corticosteroid production during diagnostic assessment of adrenal function. It is not replacement therapy for chronic adrenal insufficiency and is not a glucocorticoid.

## 1. Identity and product provenance

| Attribute | Curated record |
|---|---|
| Generic name | Cosyntropin |
| Common description | Tetracosactide; ACTH(1–24) |
| Product names | Cortrosyn; product-specific names vary by jurisdiction |
| Molecular class | Synthetic 24-residue peptide |
| End group | N-terminal free amino group; C-terminal amino acid is amidated in the synthetic peptide |
| Primary receptor | Melanocortin 2 receptor (MC2R) |
| Route | Intravenous or intramuscular, according to product label |
| Clinical role | ACTH stimulation test |
| US regulatory status | FDA-approved product history; confirm current product-specific label and marketing status |

Cosyntropin reproduces the biologically active N-terminal region of endogenous ACTH. The 1–24 fragment retains the principal adrenal steroidogenic activity of the full-length 39-amino-acid hormone.

## 2. Molecular identity and sequence

- **Length:** 24 amino-acid residues.
- **Sequence:** `SYSMEHFRWGKPVGKKRRPVKVYP`.
- **Molecular formula:** C136H210N40O31S.
- **Molecular weight:** approximately 3,093.5 Da (free peptide; salt/product labelling may differ).
- **Chemical identity:** synthetic ACTH(1–24), commonly supplied as cosyntropin acetate.

Sequence is written in one-letter amino-acid notation. The sequence should be cross-checked against the exact salt form and official product specification before using it as a release-quality identity field.

## 3. Physiological background

Endogenous ACTH is a 39-amino-acid peptide produced by cleavage of proopiomelanocortin (POMC) in pituitary corticotrophs. ACTH secretion is regulated by hypothalamic corticotropin-releasing hormone and vasopressin, circadian rhythm, stress and glucocorticoid negative feedback.

ACTH stimulates the adrenal cortex, especially zona fasciculata and zona reticularis, to synthesize and release cortisol and adrenal androgens. Chronic ACTH exposure also has trophic effects on the adrenal cortex. Cosyntropin provides a standardized exogenous stimulus to assess adrenal cortisol reserve.

## 4. Mechanism of action

**MC2R agonism and adrenal steroidogenesis:**

1. Cosyntropin binds the melanocortin 2 receptor (MC2R) on adrenal cortical cells. MC2R function requires the accessory protein MRAP.
2. Receptor activation couples to Gs and stimulates adenylyl cyclase.
3. Intracellular cAMP rises and activates protein kinase A (PKA).
4. PKA signalling increases cholesterol mobilization and delivery to the inner mitochondrial membrane, including regulation of steroidogenic acute regulatory protein (StAR).
5. Cholesterol is converted to pregnenolone by CYP11A1, initiating steroid biosynthesis; downstream enzymes generate cortisol and other adrenal steroids.

The stimulation test measures the adrenal gland's capacity to increase cortisol after ACTH-receptor activation. Cosyntropin does not directly supply cortisol and its test response is not equivalent to measuring basal endogenous ACTH.

## 5. Clinical use and diagnostic testing

The principal use is the ACTH (cosyntropin) stimulation test in evaluation of suspected adrenal insufficiency. Serum cortisol is measured before and at specified times after administration. Depending on protocol, samples may be collected at 30 and/or 60 minutes.

A commonly used standard-dose test administers 250 micrograms of cosyntropin IV or IM. Low-dose protocols (often 1 microgram) are used in some settings but require careful preparation and local validation; they should not be assumed interchangeable with the standard-dose test.

Interpretation depends on:
- assay platform and assay-specific cortisol cutoffs;
- sample timing;
- recent glucocorticoid exposure and medicines affecting steroid synthesis or cortisol binding;
- albumin and cortisol-binding globulin concentrations;
- clinical context and whether primary or central adrenal insufficiency is suspected.

Historical cortisol cutoffs (for example, 18 micrograms/dL) were developed using older assays. Modern specific immunoassays and LC-MS/MS may require lower assay-specific thresholds. Do not hard-code one universal diagnostic cutoff into the database.

## 6. Administration and handling

Cosyntropin is a prescription diagnostic agent administered by a healthcare professional. The exact vial strength, diluent, reconstitution, stability, dose and route must be taken from the current product-specific label.

Typical standard-dose diagnostic practice uses 250 micrograms IV or IM, followed by timed cortisol sampling. Some product labels describe administration of 0.25 mg. Low-dose testing is protocol-dependent and may require dilution steps that introduce dosing-error risk; follow validated institutional procedures.

Do not treat a general diagnostic protocol as a substitute for product labelling or local endocrine laboratory instructions.

## 7. Pharmacology and disposition

- **Pharmacodynamics:** MC2R-mediated adrenal steroidogenesis; increases cortisol and may increase other adrenal steroids.
- **Onset:** adrenal response can be measured within tens of minutes after administration.
- **Pharmacokinetics:** a complete, contemporary human PK profile is not asserted here; consult the current product label and primary studies.
- **Test limitation:** a normal response to standard-dose cosyntropin may not exclude very recent-onset central adrenal insufficiency before adrenal atrophy has developed.

## 8. Safety and precautions

Cosyntropin is generally used as a single diagnostic dose, but hypersensitivity reactions and other adverse effects can occur. Review the exact current product label for contraindications, warnings, adverse-event frequencies and excipients.

Clinical considerations include:
- hypersensitivity to cosyntropin or formulation components;
- potential allergic reactions, including rare serious reactions;
- transient changes in blood pressure, heart rate or symptoms related to steroid response;
- interpretation confounding from glucocorticoids and medicines that inhibit or induce steroidogenesis;
- pregnancy and lactation: use current product information and clinical risk assessment.

The test should be performed in a setting able to recognize and manage acute hypersensitivity. Do not infer safety from the fact that the dose is diagnostic and usually administered once.

## 9. Regulatory status

| Jurisdiction | Status |
|---|---|
| United States | Cortrosyn/cosyntropin has FDA-approved product history; confirm current NDC, label and marketing status for the exact presentation |
| European Union | Tetracosactide products have been marketed in some countries; current country-specific authorization and availability not verified here |
| United Kingdom | Tetracosactide (Synacthen) has a distinct product history; current label/status requires current MHRA verification |
| India (CDSCO) | Not independently verified |
| Other jurisdictions | Not independently verified |

Cosyntropin (ACTH 1–24) and full-length corticotropin (ACTH 1–39) are not identical products. Tetracosactide is the international name commonly used for the synthetic 1–24 fragment. Do not merge their labels, formulations or regulatory histories.

## 10. Formulation and quality

Cosyntropin is a synthetic peptide supplied as a sterile parenteral formulation, commonly a lyophilized powder for reconstitution. Quality attributes include identity, peptide-related impurities, potency, counterion/salt form, residual solvents/reagents, sterility, endotoxin and reconstituted-solution stability. Exact excipients, vial strength and storage conditions are product-specific and must be transcribed from the current label.

## 11. Bioinformatics and structured annotation

- entity_type: synthetic peptide hormone fragment
- peptide_parent: ACTH / POMC-derived hormone
- sequence: SYSMEHFRWGKPVGKKRRPVKVYP
- length_aa: 24
- receptor: MC2R (requires MRAP)
- signalling: Gs–adenylyl cyclase–cAMP–PKA
- primary_effect: adrenal steroidogenesis; cortisol response
- clinical_role: diagnostic ACTH stimulation agent
- route: IV or IM, product-label dependent

Do not classify cosyntropin as a glucocorticoid, mineralocorticoid, corticosteroid replacement, or full-length ACTH(1–39).

## 12. Evidence gaps and completion tasks

- Confirm workbook source row, exact brand names and status detail against the source spreadsheet.
- Retrieve current Cortrosyn FDA label and verify current marketing status, NDA number, formulation, excipients, vial strength, storage and administration instructions.
- Verify the current Synacthen/tetracosactide regulatory status country by country, including CDSCO.
- Add authoritative sequence accession and exact chemical identity for the commercial salt form.
- Curate assay-specific cortisol thresholds from current endocrine society guidance and assay validation studies; do not publish a single universal threshold.
- Add primary references for MC2R/MRAP signalling, StAR regulation and diagnostic test limitations.
- Add claim-level source locators and licensed, attributable peptide structure or mechanism imagery.

**Completion decision:** sequence, biological role, MC2R mechanism and standard diagnostic context are curated at a general scientific level. Current product-specific label details, exact regulatory history and assay-specific interpretation guidance remain to be verified. Status: **in_progress**.

## References

1. US FDA. **Drugs@FDA database** — search Cortrosyn/cosyntropin for current application history and approved labelling: https://www.accessdata.fda.gov/scripts/cder/daf/
2. DailyMed. **Cortrosyn (cosyntropin) prescribing information** — retrieve current label and confirm product-specific formulation and directions: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=Cortrosyn
3. NCBI PubChem. **Cosyntropin** chemical identity record; verify sequence and formula against official product documentation: https://pubchem.ncbi.nlm.nih.gov/#query=cosyntropin
4. Bornstein SR, et al. Diagnosis and treatment of primary adrenal insufficiency: an Endocrine Society Clinical Practice Guideline. *J Clin Endocrinol Metab*. 2016;101(2):364–389. https://doi.org/10.1210/jc.2015-1710
5. El-Farhan N, et al. Method-specific serum cortisol responses to the short Synacthen (cosyntropin) test. Consult current assay-comparison literature when selecting a threshold; avoid extrapolating legacy cutoffs across assays.
6. National Library of Medicine. **ACTH receptor (MC2R) and MRAP signalling literature** — primary mechanistic papers should be attached as claim-level citations during final evidence review: https://pubmed.ncbi.nlm.nih.gov/?term=MC2R+MRAP+ACTH+signalling

---
*Educational and research curation only. Not medical advice or a substitute for current product labelling, endocrine specialist assessment, or validated laboratory protocols.*
