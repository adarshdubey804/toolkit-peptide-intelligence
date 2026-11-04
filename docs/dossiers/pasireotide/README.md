# 052 — Pasireotide (SIGNIFOR / SIGNIFOR LAR)

**Curation status:** in_progress  
**Workbook sequence:** 052 (Peptides sheet data row 48; Excel row 50)  
**Entity class:** synthetic cyclic hexapeptide somatostatin analogue  
**Evidence cut-off:** 4 November 2026

## 1. Identity and provenance

| Attribute | Curated record |
|---|---|
| Generic name | Pasireotide |
| Brands | SIGNIFOR (immediate-release); SIGNIFOR LAR (long-acting release) |
| Development code | SOM230 |
| US applications | NDA 200677 (Signifor); NDA 203255 (Signifor LAR) |
| First US approval | 2012 |
| Drug class | Multireceptor somatostatin analogue |
| Main receptor targets | SSTR1, SSTR2, SSTR3 and SSTR5; particularly high affinity for SSTR5 |
| US indications | Cushing's disease in adults for Signifor; acromegaly in adults inadequately controlled by surgery and/or for whom surgery is not an option for Signifor LAR |
| Routes | Subcutaneous (Signifor); deep intramuscular (Signifor LAR) |

**Workbook provenance:** row 052 lists pasireotide / Signifor and Signifor LAR, for Cushing's disease and acromegaly, FDA-approved, first US approval 2012. Indications are formulation-specific; do not imply both formulations have identical approved uses.

## 2. Molecular identity and sequence

Pasireotide is a synthetic cyclic hexapeptide somatostatin analogue with noncanonical amino-acid residues.

**Sequence (one-letter / residue form):**  
H-D-Phe-Cys-Phe-D-Trp-Lys-Thr-Cys-Tyr-NH₂

The mature peptide is commonly described as a cyclic hexapeptide pharmacophore with a disulfide bridge; sequence notation and residue count can differ between chemical descriptions because of the specific side-chain and backbone representation. **Do not use the provisional sequence line above as a validated primary sequence:** authoritative chemistry documentation must be used to resolve the complete residue connectivity and numbering before depositing a machine-readable sequence.

- Contains D-Phe and D-Trp.
- Contains a disulfide-linked cysteine pair in the cyclic scaffold.
- C-terminal amidation.
- Molecular formula and molecular weight: intentionally withheld pending verification against FDA chemistry review and the correct marketed salt/formulation basis.
- Commercial products contain pasireotide as the relevant salt in formulation-specific presentations; verify the exact salt and excipient composition from each current label.

**Identity caution:** pasireotide is not octreotide or lanreotide. Do not copy their sequences, molecular formulae, residue counts or receptor-affinity tables.

## 3. Disease biology

### Cushing's disease
Cushing's disease is caused by an ACTH-secreting pituitary corticotroph adenoma. Excess ACTH stimulates adrenal cortisol production, resulting in hypercortisolism and metabolic, cardiovascular, skeletal, immune and neuropsychiatric complications. Somatostatin receptor expression, including SSTR5, in corticotroph adenomas provides a therapeutic target in selected patients.

### Acromegaly
Acromegaly is most commonly caused by a GH-secreting pituitary adenoma. Excess GH increases hepatic and peripheral IGF-1, leading to tissue overgrowth and systemic complications. Somatostatin receptor activation suppresses GH secretion in responsive tumours.

## 4. Mechanism of action

Pasireotide binds multiple somatostatin receptor subtypes (SSTR1, SSTR2, SSTR3 and SSTR5), with a receptor-affinity profile distinct from first-generation analogues and particularly strong affinity for SSTR5.

1. Receptor binding activates Gi/o-coupled signalling.
2. Adenylyl cyclase activity and intracellular cAMP are reduced.
3. Calcium-dependent hormone secretion and secretory-granule exocytosis are inhibited.
4. In corticotroph adenomas, ACTH secretion is reduced, which can lower circulating cortisol.
5. In somatotroph adenomas, GH secretion is suppressed, potentially reducing IGF-1.

The clinical effect depends on tumour receptor expression and individual response. Pasireotide is not a glucocorticoid receptor antagonist and does not directly inhibit adrenal steroid synthesis.

## 5. Approved indications and formulation boundaries

**SIGNIFOR (SC):** treatment of adults with Cushing's disease for whom pituitary surgery is not an option or has not been curative, subject to current label wording.

**SIGNIFOR LAR (IM):** treatment of adults with acromegaly who have had an inadequate response to surgery and/or are not surgical candidates, subject to current label wording.

The US indication for one formulation must not be assigned to the other. Regulatory status and indications outside the US may differ.

## 6. Administration and dose overview

Dosing is formulation- and indication-specific.

- **Signifor immediate-release:** administered subcutaneously, generally twice daily, with dose adjustment according to cortisol response and tolerability in Cushing's disease.
- **Signifor LAR:** administered by deep intramuscular injection at extended intervals (typically every four weeks) for acromegaly, with dose titration based on GH/IGF-1 response and safety.

This dossier does not provide a patient-specific regimen. Consult the current label for starting dose, titration, dose interruption, hepatic impairment, injection technique and monitoring.

## 7. Pharmacodynamics

- In Cushing's disease, pasireotide reduces ACTH secretion from responsive pituitary corticotroph tumours and can reduce urinary free cortisol.
- In acromegaly, pasireotide reduces GH secretion and may reduce IGF-1.
- Receptor-subtype engagement differs from octreotide and lanreotide and can contribute to a distinct efficacy and adverse-effect profile.
- Hyperglycaemia is a prominent pharmacodynamic and safety issue, associated with effects on insulin and incretin secretion.

Use indication-specific biochemical endpoints: urinary free cortisol / serum cortisol measures for Cushing's disease, and age-adjusted IGF-1 and GH for acromegaly.

## 8. Pharmacokinetics

Immediate-release and LAR formulations have different absorption profiles and must be assessed separately. The SC product has relatively rapid absorption after injection; the LAR product produces prolonged exposure following deep IM administration. Pasireotide is extensively distributed and metabolised, with hepatic pathways contributing to disposition.

Do not transfer numerical PK parameters between Signifor and Signifor LAR. Exact bioavailability, half-life, accumulation, metabolism and hepatic-impairment data should be transcribed from the current formulation-specific FDA label with study context.

## 9. Clinical evidence

### Cushing's disease
The pivotal pasireotide SC programme evaluated biochemical control of hypercortisolism, including urinary free cortisol, alongside clinical measures. Response was incomplete in a substantial subset, and glucose-related adverse events were important.

### Acromegaly
The pasireotide LAR programme evaluated biochemical control in patients inadequately controlled on other somatostatin analogues and in patients not adequately controlled after surgery or not suitable for surgery. Outcomes included GH and IGF-1 control.

**Evidence gap:** add trial names, sample sizes, randomisation, primary endpoint time points, response definitions, effect estimates and confidence intervals from the FDA labels and primary publications. Do not merge results from the two formulations or indications.

## 10. Safety and monitoring

**Major warning: hyperglycaemia and diabetes.** Pasireotide can cause marked increases in blood glucose and HbA1c, sometimes requiring initiation or intensification of antidiabetic therapy. Assess glucose status before treatment and monitor during treatment.

Other important risks include:
- **Bradycardia and conduction abnormalities:** review cardiac history, ECG risk and concomitant rate-limiting drugs.
- **QT prolongation:** correct electrolyte abnormalities and assess concomitant QT-prolonging medicines.
- **Gallbladder disease:** gallstones and complications may occur.
- **Liver enzyme abnormalities:** monitor liver tests according to the applicable label.
- **Adrenal insufficiency / hypocortisolism:** particularly relevant in Cushing's disease when cortisol falls; recognise symptoms and follow label-directed management.
- **Pituitary hormone effects:** monitor relevant pituitary axes when clinically indicated.
- **Injection-site reactions and gastrointestinal effects:** nausea, diarrhoea, abdominal pain and related symptoms may occur.
- **Hypersensitivity:** assess for serious reactions.

The hyperglycaemia risk profile is especially important when comparing pasireotide with other somatostatin analogues.

## 11. Drug interactions

Potential interactions include:
- additive bradycardia with beta-blockers and other heart-rate-lowering drugs;
- increased arrhythmia risk with QT-prolonging drugs;
- interactions with medicines affecting glucose regulation;
- potential effects on CYP3A4 substrate exposure; check the current label for specific interaction studies;
- altered exposure in hepatic impairment.

Use the current formulation-specific label and medication review rather than extrapolating interaction magnitudes from another somatostatin analogue.

## 12. Formulation and manufacturing

Signifor immediate-release is a sterile solution for SC injection. Signifor LAR is a long-acting injectable suspension supplied as a kit for reconstitution and deep IM administration. Their excipients, preparation, storage and administration requirements are not interchangeable.

Critical quality attributes include peptide identity and purity, stereochemical integrity, correct cyclic/disulfide structure, peptide-related impurities, potency at relevant SSTR subtypes, formulation stability, sterility and endotoxin. For LAR, additional attributes include particle characteristics, reconstitution behaviour, suspension uniformity and release kinetics.

## 13. Bioinformatics annotation

| Field | Annotation |
|---|---|
| Entity type | Synthetic cyclic peptide analogue |
| Pharmacological class | Multireceptor somatostatin analogue |
| Targets | SSTR1, SSTR2, SSTR3, SSTR5 |
| Relative profile | Particularly high SSTR5 affinity |
| Signalling | Gi/o; decreased cAMP and secretion |
| Disease contexts | ACTH-secreting corticotroph adenoma; GH-secreting somatotroph adenoma |
| Formulations | SC immediate-release; IM long-acting release |
| Key safety phenotype | Hyperglycaemia / diabetes |

**Sequence/structure validation required:** resolve the authoritative chemical structure and residue nomenclature from regulatory chemistry documentation before assigning a FASTA sequence, SMILES, InChI or exact molecular mass.

## 14. Regulatory status

| Jurisdiction | Status |
|---|---|
| United States | FDA-approved; Signifor NDA 200677 and Signifor LAR NDA 203255; first approval 2012 |
| European Union | Signifor and Signifor LAR centrally authorised; product-specific EPAR information applies |
| India | CDSCO status not independently verified |
| Other regions | Not exhaustively verified |

## 15. Evidence gaps and completion checklist

- Retrieve the FDA chemistry review to validate full molecular structure, residue sequence, stereochemistry, disulfide connectivity, salt, formula and mass.
- Capture current separate FDA labels for Signifor and Signifor LAR, including exact indications and dose/titration tables.
- Import pivotal Cushing's disease and acromegaly trial data separately with endpoints and confidence intervals.
- Add current label-based rates for hyperglycaemia, diabetes, QT prolongation, bradycardia, gallbladder and hepatic events.
- Verify current EMA variations and CDSCO status.
- Add validated structure identifiers and source-attributed molecular/mechanism imagery.

**Completion decision:** receptor pharmacology, disease rationale, formulation-specific indication distinction and major safety profile are outlined. Exact sequence/chemical identity, trial-level numerical evidence, current label tables and jurisdictional status remain open. **Status: in_progress.**

## References

1. US FDA / DailyMed. **SIGNIFOR (pasireotide) injection prescribing information**: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=SIGNIFOR
2. US FDA / DailyMed. **SIGNIFOR LAR (pasireotide) prescribing information**: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=SIGNIFOR%20LAR
3. US FDA. **NDA 200677 and NDA 203255**, approval and review documents: https://www.accessdata.fda.gov/scripts/cder/daf/
4. European Medicines Agency. **Signifor EPAR**: https://www.ema.europa.eu/en/medicines/human/EPAR/signifor
5. PubMed. **Pasireotide Cushing's disease and acromegaly clinical trials**: https://pubmed.ncbi.nlm.nih.gov/?term=pasireotide+Cushing+acromegaly+trial

---
*Educational and research curation only. Not medical advice or a substitute for current product labelling or specialist endocrine care.*
