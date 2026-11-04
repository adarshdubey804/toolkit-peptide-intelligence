# 049 — Etelcalcetide (PARSABIV)

**Curation status:** in_progress  
**Workbook sequence:** 049 (Peptides sheet data row 45; Excel row 47)  
**Entity class:** synthetic disulfide-linked modified oligopeptide calcimimetic  
**Evidence checked:** 4 November 2026

## 1. Identity and provenance

| Attribute | Curated value |
|---|---|
| Generic name | Etelcalcetide |
| Brand | PARSABIV |
| Development code | KAI-4169 |
| US application | NDA 208325 |
| US approval | 2017 (exact FDA action date to be verified against approval letter) |
| EU authorisation | 11 November 2016 |
| Sponsor | Amgen |
| Drug class | Calcimimetic; CaSR allosteric modulator |
| Indication | Secondary hyperparathyroidism in adults with CKD receiving haemodialysis |
| Route | Intravenous, at the end of haemodialysis |

**Workbook provenance:** the supplied workbook lists etelcalcetide / Parsabiv under “Endocrine, Pituitary & Bone”, for secondary hyperparathyroidism in haemodialysis, FDA-approved, first US approval 2017. Workbook labels are provenance, not independent regulatory evidence.

## 2. Molecular identity and structure

Etelcalcetide is a synthetic peptide comprising seven D-amino acids, with its N-terminal D-cysteine linked through a disulfide bond to an additional L-cysteine.

**D-peptide segment:** Ac-D-Cys-D-Ala-D-Arg-D-Arg-D-Arg-D-Ala-D-Arg-NH₂  
**Additional partner:** L-cysteine, disulfide-linked to the D-Cys residue.

Compact representation: **Ac-dC-dA-dR-dR-dR-dA-dR-NH₂ linked by disulfide to L-Cys**. Lower-case residues denote D stereochemistry; preserve this stereochemistry in any sequence or chemical structure encoding.

- Seven residues in the D-peptide segment, plus the linked L-cysteine.
- N-terminal acetylation; C-terminal amidation.
- One disulfide bond between D-Cys and L-Cys.
- Marketed as hydrochloride salt.
- FDA-described formula: **C₃₈H₇₃N₂₁O₁₀S₂ · xHCl (4 ≤ x ≤ 5)**.
- FDA-described molecular weight: **1047.5 g/mol (monoisotopic, free-base basis)**. Do not confuse this with the variable hydrochloride salt mass or database-calculated average mass.

## 3. Disease biology

In chronic kidney disease, phosphate retention, reduced calcitriol production and disturbed calcium balance contribute to secondary hyperparathyroidism. Parathyroid chief cells sense extracellular calcium through the calcium-sensing receptor (CaSR). CaSR activation normally restrains parathyroid hormone (PTH) synthesis and secretion.

## 4. Mechanism of action

Etelcalcetide is a calcimimetic that **allosterically modulates CaSR**:

1. It binds CaSR on parathyroid chief cells.
2. It enhances receptor activation by extracellular calcium (positive allosteric modulation).
3. Increased CaSR signalling suppresses PTH secretion.
4. Reduced PTH contributes to lower serum calcium and alters phosphate dynamics in haemodialysis patients.

It is not a PTH-receptor antagonist, calcium chelator, phosphate binder or direct calcium substitute. The FDA label reports PTH reduction within 30 minutes after a single IV bolus in the studied setting.

## 5. Approved indication and limitations

US indication: treatment of secondary hyperparathyroidism in **adult patients with CKD on haemodialysis**. The US label says it has not been studied in parathyroid carcinoma, primary hyperparathyroidism, or CKD patients not receiving haemodialysis and is not recommended in those populations.

The EMA product information describes the same core indication. Do not extrapolate this indication to primary HPT or non-dialysis CKD.

## 6. Administration and dose

Current US prescribing information:
- Starting dose: **5 mg IV bolus three times weekly**, at the end of haemodialysis.
- Maintenance dose: individualized by titration based on PTH and corrected serum calcium.
- Label titration range: 2.5–15 mg three times weekly.
- Corrected serum calcium should be at or above the lower limit of normal before initiation, dose increase or re-initiation.
- Administer through the haemodialysis venous line at the end of the session, following current product instructions.

This is a label summary, not patient-specific dosing advice. Follow current prescribing information and specialist direction.

## 7. Pharmacodynamics and pharmacokinetics

- PTH reduction is detectable within 30 minutes after a single IV dose.
- The magnitude and duration of PTH reduction increase with dose in single-dose studies.
- PTH reduction is associated with reductions in serum calcium and attenuation of post-dialytic phosphate elevation.
- With thrice-weekly dosing, the PTH-lowering effect was maintained during the six-month study period.
- FDA label describes linear PK in the studied haemodialysis population.
- Population modelling reports an effective half-life of approximately 3–4 days with thrice-weekly dosing and steady state after several weeks; this estimate is population- and regimen-specific.

## 8. Clinical evidence

The pivotal programme included placebo-controlled phase 3 studies in adults with CKD receiving haemodialysis and secondary HPT. Primary efficacy analyses assessed the proportion of patients achieving a greater than 30% reduction in mean PTH from baseline during the efficacy assessment period; additional outcomes included target PTH achievement and changes in PTH, calcium and phosphate.

**Evidence gap:** import trial names, sample sizes, endpoint windows, effect estimates and confidence intervals directly from the current FDA label and primary publications. Do not merge the pivotal trials into one unsupported response rate.

## 9. Safety and monitoring

Important label risks include:
- **Hypocalcaemia:** may be severe and cause paraesthesia, myalgia, muscle spasm, seizures, QT prolongation and ventricular arrhythmias. Monitor corrected serum calcium.
- **Seizures:** calcium reduction may increase seizure risk, especially with seizure history.
- **Worsening heart failure:** hypocalcaemia-related reduction in myocardial function may contribute.
- **Upper gastrointestinal bleeding:** reported; evaluate patients with risk factors or symptoms.
- **Adynamic bone disease:** excessive PTH suppression may contribute; monitor PTH and avoid oversuppression.
- **Hypersensitivity:** assess for serious allergic reactions.
- Avoid duplicate calcimimetic therapy unless specifically directed by specialist and current label.

Calcium monitoring before initiation and during titration is central to safe use. Consult the current label for exact dose-hold and restart thresholds.

## 10. Formulation and manufacturing

Current US label describes a sterile, preservative-free, ready-to-use clear, colourless solution at **5 mg/mL**. Single-dose vial strengths include 2.5 mg, 5 mg and 10 mg etelcalcetide (corresponding hydrochloride salt masses are higher). Excipients include sodium chloride and succinic acid; pH is adjusted using sodium hydroxide and/or hydrochloric acid.

Etelcalcetide is chemically synthesized, not recombinant. Critical quality attributes include D-amino-acid stereochemistry, N-acetylation, C-terminal amidation, correct disulfide linkage, peptide-related impurities, salt stoichiometry, assay/potency, residual reagents, sterility, endotoxin and particulate matter.

## 11. Bioinformatics annotation

| Field | Annotation |
|---|---|
| Entity type | Synthetic modified oligopeptide |
| D-peptide length | 7 residues |
| Stereochemistry | Seven D-amino acids |
| Modifications | N-acetyl; C-terminal amide; disulfide-linked L-Cys |
| Target | Calcium-sensing receptor (CaSR; CASR) |
| Pharmacology | Positive allosteric modulation / calcimimetic |
| Pathway | CaSR-mediated regulation of PTH secretion |
| Clinical role | Secondary HPT in adult CKD haemodialysis |
| Route | IV bolus after haemodialysis |
| Key monitoring | Corrected serum calcium and PTH |

Do not encode as a simple linear L-amino-acid SMILES: stereochemistry, terminal caps, additional cysteine and disulfide connectivity are essential.

## 12. Regulatory status

| Region | Status |
|---|---|
| United States | FDA-approved; NDA 208325; initial US approval 2017 |
| European Union | Centrally authorised; authorisation issued 11 November 2016; EMA/EPAR EMEA/H/C/003995 |
| India | CDSCO status not independently verified |
| Other regions | Not exhaustively verified |

## 13. Evidence gaps and completion checklist

- Confirm exact FDA action date from the NDA 208325 approval letter.
- Add direct FDA label section locators for dose, safety and PK claims.
- Import pivotal trial-level numerical outcomes with denominators, time windows and confidence intervals.
- Confirm current EU product information and post-authorisation variations.
- Verify CDSCO status rather than extrapolating from US/EU approval.
- Add a stereochemistry- and disulfide-aware structure record, validated against authoritative chemistry documentation.
- Add sourced, reuse-cleared chemical structure and CaSR mechanism imagery.
- Verify current marketed pack sizes and regional availability separately from authorisation.

**Completion decision:** molecular architecture, CaSR mechanism, core US/EU indication, route and key safety issues are documented. Exact FDA action date, trial-level numerical outcomes, Indian status and validated structure asset remain open. **Status: in_progress.**

## References

1. US FDA / DailyMed. **PARSABIV (etelcalcetide) injection, current prescribing information**, revised 8 March 2026: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=cd270093-c6a8-4596-a4ab-e6aa0a2c8a0c
2. US FDA. **NDA 208325, PARSABIV (etelcalcetide), 2017 label**: https://www.accessdata.fda.gov/drugsatfda_docs/label/2017/208325Orig1s000Lbledt.pdf
3. European Medicines Agency. **Parsabiv EPAR**, product details and authorisation history: https://www.ema.europa.eu/en/medicines/human/EPAR/parsabiv
4. US FDA. **PARSABIV 2019 prescribing information**, chemical description: https://www.accessdata.fda.gov/drugsatfda_docs/label/2019/208325s002lbl.pdf
5. PubChem. **Etelcalcetide, CID 71511839** (secondary database; cross-check salt and mass basis): https://pubchem.ncbi.nlm.nih.gov/compound/71511839

---
*Educational and research curation only. Not medical advice or a substitute for current product information or specialist nephrology care.*
