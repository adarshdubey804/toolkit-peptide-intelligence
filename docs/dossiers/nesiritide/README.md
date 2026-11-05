# Dossier 063 — Nesiritide (Natrecor)

**Generic name:** Nesiritide  
**Brand:** Natrecor  
**Workbook position:** Peptides sheet, row 63 (Excel row 64)  
**Curation status:** `in_progress` — core identity, receptor mechanism, clinical role, and major trial context curated; current label extraction, exact product analytics, and complete evidence synthesis remain open.  
**Regulatory status:** FDA-approved prescription medicine; indication and use are product-label specific.

> **Clinical safety:** Nesiritide is an intravenous prescription medicine used in monitored acute-care settings. This dossier is educational and is not a treatment or infusion protocol.

## 1. Executive overview

Nesiritide is a recombinant form of human B-type natriuretic peptide (BNP), a 32-amino-acid cardiac hormone. It activates natriuretic peptide receptor-A (NPR-A, also called guanylyl cyclase-A), increasing intracellular cyclic guanosine monophosphate (cGMP). Its pharmacological effects include venous and arterial vasodilation, natriuresis, and suppression of components of the renin–angiotensin–aldosterone and sympathetic systems.

Natrecor was approved in the United States in 2001 for intravenous treatment of patients with acutely decompensated congestive heart failure who have dyspnea at rest or with minimal activity. It is not a routine substitute for established heart-failure therapies and can cause clinically important hypotension.

The large ASCEND-HF trial did not show a significant reduction in death or heart-failure rehospitalization at 30 days. It found a modest improvement in patient-reported dyspnea that did not meet the trial's prespecified threshold for clinical significance, alongside an increased risk of hypotension. These results are important when distinguishing physiological activity from proven outcome benefit.

## 2. Identity and classification

| Field | Curated information |
|---|---|
| Generic name | Nesiritide |
| Brand | Natrecor |
| Molecular class | Recombinant human B-type natriuretic peptide |
| Peptide length | 32 amino acids |
| Endogenous counterpart | Human BNP-32 |
| Primary receptor | NPR-A / GC-A (NPR1) |
| Principal second messenger | cGMP |
| FDA-approved indication | Intravenous treatment of patients with acutely decompensated congestive heart failure who have dyspnea at rest or with minimal activity |
| First US approval | 2001 |
| Workbook category | Cardiovascular & Critical Care |
| Workbook status | FDA-approved |

Nesiritide is a recombinant peptide hormone product, not a small-molecule diuretic and not a natriuretic peptide receptor agonist of a different sequence. It should be distinguished from endogenous atrial natriuretic peptide (ANP), C-type natriuretic peptide (CNP), and newer investigational natriuretic peptide constructs.

## 3. Sequence and chemical structure

**Human BNP-32 / nesiritide sequence:**

`SPKMVQGSGCFGRKMDRISSSSGLGCKVLRRH`

The 32-residue peptide contains an intramolecular disulfide bond between Cys¹⁰ and Cys²⁶, forming the characteristic ring important for natriuretic peptide receptor activity.

| Property | Curated information |
|---|---|
| Length | 32 amino-acid residues |
| Sequence | SPKMVQGSGCFGRKMDRISSSSGLGCKVLRRH |
| Disulfide bond | Cys¹⁰–Cys²⁶ |
| Molecular form | Recombinant human BNP-32 |
| Molecular formula / exact mass | Not asserted in this revision; verify against the approved product chemistry record |
| Terminal chemistry | Confirm from the current product specification before recording formula or mass |
| Expression / production | Recombinant production; consult official product CMC information for details |

Sequence numbering is given from the mature 32-residue BNP peptide. The disulfide bond should be represented explicitly in structure files; a linear sequence string alone does not capture the mature peptide's connectivity.

## 4. Mechanism of action (MoA)

Nesiritide binds natriuretic peptide receptor-A (NPR-A/GC-A), a membrane receptor with intrinsic particulate guanylyl cyclase activity.

1. Nesiritide binds the extracellular ligand-binding domain of NPR-A.
2. Receptor activation stimulates intracellular guanylyl cyclase activity.
3. GTP is converted to cyclic GMP (cGMP).
4. cGMP-dependent protein kinase and other cGMP effectors alter vascular smooth-muscle tone, renal tubular handling, and neurohormonal signalling.
5. Vascular smooth muscle relaxes, reducing preload and afterload.
6. Renal and neurohormonal effects can promote natriuresis and reduce sodium-retaining signals.

### Physiological effects
- **Vasodilation:** venous and arterial dilation can reduce cardiac filling pressures and vascular resistance.
- **Natriuresis:** increased renal sodium excretion is part of the natriuretic peptide response.
- **Diuresis:** changes in renal haemodynamics and tubular sodium handling can increase urine output.
- **Neurohormonal modulation:** BNP signalling counter-regulates RAAS and sympathetic activation.

Nesiritide does not act through the same mechanism as loop diuretics, ACE inhibitors, or angiotensin receptor blockers. Its clinical effects and risks must be assessed in the context of acute haemodynamic status.

## 5. Pharmacodynamics

- **cGMP generation:** receptor activation increases cGMP.
- **Vascular response:** venous and arterial vasodilation can lower filling pressures and systemic vascular resistance.
- **Renal response:** natriuretic peptide signalling can increase sodium excretion and influence urine output.
- **Neurohormonal response:** BNP signalling counteracts some RAAS and sympathetic effects.
- **Blood pressure:** hypotension is a clinically important consequence and can limit use.

A pharmacodynamic response, such as lower filling pressure or improved dyspnea score, is not equivalent to a demonstrated reduction in mortality or rehospitalization.

## 6. Pharmacokinetics

Nesiritide is an intravenously administered peptide with a relatively short plasma half-life. It is cleared through natriuretic peptide receptor-mediated uptake and enzymatic degradation by peptidases, including neprilysin. Product-specific PK parameters must be taken from the current prescribing information and primary pharmacology sources.

The following require exact label-level extraction before being recorded as definitive:
- Distribution volume.
- Clearance and terminal half-life.
- Contribution of receptor-mediated clearance versus enzymatic degradation.
- Exposure changes in renal or hepatic impairment.
- Relationship between exposure, cGMP response, and hypotension.

Do not transfer PK values from endogenous BNP measurements or from other natriuretic peptide analogues.

## 7. Clinical evidence

### FDA-approved clinical context

Natrecor is labelled for intravenous treatment of patients with acutely decompensated congestive heart failure who have dyspnea at rest or with minimal activity. The label and clinical judgement govern patient selection and use. It should not be represented as chronic disease-modifying therapy.

### ASCEND-HF

The ASCEND-HF trial evaluated nesiritide in patients hospitalized with acute decompensated heart failure.

- Study design: randomized, double-blind, placebo-controlled trial.
- Population: 7,141 patients hospitalized with acute heart failure.
- Co-primary endpoints: patient-reported dyspnea and the composite of death or heart-failure rehospitalization at 30 days.
- Main outcome: nesiritide did not significantly reduce death or heart-failure rehospitalization at 30 days.
- Dyspnea: improvement was statistically modest and did not meet the prespecified threshold for clinical significance.
- Safety: hypotension occurred more frequently with nesiritide.

**Interpretation:** ASCEND-HF did not establish a mortality or rehospitalization benefit. The result should be presented accurately and not reduced to a claim that nesiritide improves major clinical outcomes.

### Evidence limitations
- Acute haemodynamic effects do not guarantee improved long-term outcomes.
- Results from hospitalized acute heart-failure populations should not be generalized to stable chronic heart failure.
- Patient selection and blood-pressure status are important.
- Guideline positioning may evolve; consult current heart-failure guidelines and local product labeling.

## 8. Safety and warnings

Hypotension is a major safety concern with nesiritide. The current FDA-approved prescribing information must be consulted for the full contraindication and warning list.

Important risk domains include:
- **Symptomatic hypotension:** vasodilation can cause clinically significant blood-pressure reduction.
- **Renal function:** haemodynamic changes and blood-pressure reduction may affect renal perfusion and renal function.
- **Volume status:** excessive haemodynamic or diuretic effects can be poorly tolerated in vulnerable patients.
- **Electrolytes:** changes in renal sodium and water handling require clinical assessment.
- **Hypersensitivity:** evaluate according to the approved product label.
- **Concurrent vasoactive medicines:** additive blood-pressure effects may occur.

Do not infer a universal adverse-event frequency from a single trial; rates depend on population, comparator, exposure, and event definition.

## 9. Drug interactions and clinical context

Nesiritide may be used in patients receiving multiple acute-heart-failure therapies. Relevant considerations include:
- Other vasodilators and antihypertensive medicines may increase hypotension risk.
- Diuretics can alter volume status and renal function.
- Other vasoactive medicines may change haemodynamic response.
- Renal impairment and baseline blood pressure influence tolerability.

A complete interaction review should use the current product label and clinical pharmacy references. This dossier does not provide patient-specific treatment advice.

## 10. Regulatory status and product

- **FDA approval:** Natrecor (nesiritide) received US approval in 2001.
- **Indication:** intravenous treatment of patients with acutely decompensated congestive heart failure who have dyspnea at rest or with minimal activity.
- **Product type:** recombinant human BNP-32 peptide for IV use.
- **Label distinction:** approval is specific to the product, route, and labelled indication; it does not support unapproved use for chronic heart failure, bodybuilding, or general wellness.
- **Current status:** verify current marketed availability and latest label in Drugs@FDA and DailyMed before recording present commercial status.

## 11. Manufacturing, formulation, and quality

Nesiritide is a recombinant peptide drug product. Relevant critical quality attributes include:
- Correct 32-residue sequence and amino-acid identity.
- Correct Cys¹⁰–Cys²⁶ disulfide connectivity.
- Peptide content and biological potency.
- Related peptide species and degradation products.
- Control of oxidation, deamidation, and other chemical changes.
- Process-related impurities and residuals.
- Sterility, endotoxin, and particulate control for IV formulation.
- Formulation pH, excipient compatibility, container-closure integrity, and stability.

A generic BNP peptide or research-grade material is not equivalent to the approved Natrecor product. Product-specific manufacturing and formulation claims should be sourced from official CMC or label documentation.

## 12. Bioinformatics and computational research

- Represent the mature BNP-32 sequence and explicitly encode the Cys¹⁰–Cys²⁶ disulfide.
- Map NPR-A/GC-A signalling to NPR1 and downstream cGMP effectors.
- Distinguish BNP from ANP and CNP receptor pharmacology.
- Curate cGMP, vascular tone, natriuresis, renal function, and dyspnea outcomes separately.
- Store acute haemodynamic outcomes separately from 30-day mortality and rehospitalization.
- Keep recombinant product identity and endogenous BNP biomarker records distinct.

## 13. Evidence gaps and curation actions

1. Retrieve the current Natrecor label and extract exact PK, contraindications, warnings, adverse reactions, and formulation information.
2. Link the 2001 FDA approval action and original application record.
3. Extract the full ASCEND-HF publication and registry results, including endpoint estimates and confidence intervals.
4. Review earlier pivotal studies and distinguish haemodynamic surrogates from patient-centred outcomes.
5. Verify current commercial availability and label revision date.
6. Add product-specific analytical and manufacturing attributes only from authoritative records.
7. Keep status `in_progress` until current label and trial data have been checked in full.

## 14. References and source register

1. **FDA Drugs@FDA — Natrecor (nesiritide).** Official approval and label history. https://www.accessdata.fda.gov/scripts/cder/daf/
2. **DailyMed — Natrecor (nesiritide) prescribing information.** Product indication, warnings, and PK. https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=Natrecor
3. **O'Connor CM, et al. (2011).** Effect of nesiritide in patients with acute decompensated heart failure. *New England Journal of Medicine*. DOI: 10.1056/NEJMoa1100171. PMID: 21732835. https://pubmed.ncbi.nlm.nih.gov/21732835/
4. **ClinicalTrials.gov — ASCEND-HF.** Trial record NCT00475852. https://clinicaltrials.gov/study/NCT00475852
5. **UniProt — Natriuretic peptides / BNP precursor.** Sequence and precursor context. https://www.uniprot.org/uniprotkb/P16860/entry
6. **IUPHAR/BPS Guide to Pharmacology — Natriuretic peptide receptors.** NPR-A/GC-A and cGMP receptor pharmacology. https://www.guidetopharmacology.org/

## 15. Change log

- Created as workbook entry 063.
- Added BNP-32 sequence and Cys¹⁰–Cys²⁶ disulfide topology.
- Added NPR-A/GC-A–cGMP mechanism and physiological effects.
- Added Natrecor approval context and ASCEND-HF outcome interpretation.
- Added hypotension and renal/perfusion safety considerations.
- Status remains `in_progress` pending current label and full trial-data extraction.
