# 043 — Sincalide (Kinevac)

**Curation status:** in_progress  
**Entity class:** synthetic, modified CCK-related octapeptide; diagnostic secretagogue  
**Workbook sequence:** 043  
**Evidence cut-off:** 4 November 2026

> Sincalide is a synthetic peptide analogue of the biologically active C-terminal region of cholecystokinin (CCK). It is used as a diagnostic stimulus, especially in hepatobiliary scintigraphy and selected pancreatic-function testing. It is not a treatment for gallbladder disease.

## 1. Identity

| Attribute | Record |
|---|---|
| Generic name | Sincalide |
| Brand | Kinevac |
| Class | CCK analogue; diagnostic agent |
| Length | 8 amino-acid residues |
| Route | Intravenous |
| Molecular architecture | Linear synthetic octapeptide |
| Modifications | O-sulfated tyrosine; C-terminal amidation |
| US regulatory history | Historical FDA-approved product record; current marketing/label status needs confirmation |

## 2. Sequence and chemistry

Commonly reported sequence:

`Asp-Tyr(O-sulfate)-Met-Gly-Trp-Met-Asp-Phe-NH2`

Modified one-letter representation: `DY(SO3H)MGWMDF-NH2`.

The sulfate modification on tyrosine and amidated C-terminus are integral to biological activity. Confirm the exact salt form, formula, molecular weight, vial composition and current product specification against the current official label before treating those as definitive database values.

## 3. Physiological role

Endogenous CCK is released from enteroendocrine I cells in the proximal small intestine in response to nutrients, particularly fats and proteins. It coordinates gallbladder contraction, sphincter of Oddi relaxation, pancreatic enzyme secretion, and modulation of gastric emptying and satiety. Sincalide reproduces selected CCK actions to provoke a measurable response during diagnostic testing.

## 4. Mechanism of action

**Primary mechanism: CCK1 (CCK-A) receptor agonism.**

1. Sincalide binds CCK1 receptors on gallbladder smooth muscle and other responsive tissues.
2. CCK1 is a class A GPCR that signals predominantly through Gq/11.
3. Receptor activation stimulates phospholipase C, generating IP3 and DAG and increasing intracellular calcium.
4. Increased intracellular calcium promotes gallbladder smooth-muscle contraction.
5. CCK signalling also stimulates pancreatic acinar enzyme secretion and contributes to sphincter of Oddi relaxation.

The response depends on dose and infusion rate. Rapid administration can cause cramping and nonphysiological gallbladder emptying; standardized slow infusion protocols improve test reproducibility.

## 5. Diagnostic applications

### 5.1 Hepatobiliary scintigraphy

Sincalide can be administered during hepatobiliary scintigraphy to contract the gallbladder and measure gallbladder ejection fraction (GBEF). The result can assist evaluation of functional gallbladder disorders when interpreted with symptoms, imaging and exclusion of structural disease.

A commonly used standardized nuclear-medicine protocol is 0.02 microgram/kg infused over 60 minutes, with GBEF measured using a validated acquisition and analysis method. This is a protocol reference, not a substitute for the current product label or local procedure. Reference ranges depend on infusion duration and methodology; results from different protocols should not be treated as interchangeable.

### 5.2 Pancreatic function

Sincalide stimulates pancreatic enzyme secretion and may be used in selected diagnostic tests, often with secretin. Secretin predominantly stimulates bicarbonate-rich ductal fluid secretion, while CCK/sincalide stimulates acinar enzyme secretion. They assess related but distinct components of exocrine pancreatic function.

## 6. Administration and handling

Sincalide is administered intravenously in a controlled clinical setting. Exact labelled dose, dilution, infusion duration, vial strength, reconstitution and stability must be verified from the current official Kinevac prescribing information before populating definitive product fields.

For GBEF scintigraphy, slow infusion is important because rapid bolus administration can cause abdominal cramping, nausea and nonphysiological gallbladder emptying. Use the locally validated nuclear-medicine protocol and its matching reference range. This dossier is not an administration instruction.

## 7. Pharmacology and disposition

- **Pharmacodynamics:** CCK1 receptor-mediated gallbladder contraction and pancreatic enzyme secretion.
- **Dose response:** depends on dose, infusion rate, gallbladder status and concurrent medicines.
- **Pharmacokinetics:** a definitive half-life, clearance and distribution profile is not asserted here; obtain it from the current label or primary human PK study.
- **Interpretation:** GBEF is protocol-dependent and is not a stand-alone diagnosis.

## 8. Safety and precautions

CCK stimulation can be associated with abdominal discomfort or cramping, nausea, flushing and other gastrointestinal symptoms. Rapid administration can intensify these effects.

Before clinical use, consult the current label for contraindications, hypersensitivity precautions, adverse-event frequencies, pregnancy/lactation information, interactions and monitoring requirements. Opioids and other medicines affecting biliary or gallbladder motility can alter test results. Document relevant medicines and follow protocol-specific preparation guidance; this dossier does not prescribe a universal washout interval.

## 9. Regulatory status

| Jurisdiction | Status |
|---|---|
| United States | Historical FDA-approved Kinevac product record; current marketing and label status not confirmed here |
| European Union | Not independently verified |
| United Kingdom | Not independently verified |
| India (CDSCO) | Not independently verified |
| Other regions | Not independently verified |

Do not infer current commercial availability solely from historic approval or an archived label.

## 10. Formulation and quality

Sincalide is a chemically synthesized, modified octapeptide. Relevant quality attributes include peptide identity and sequence, tyrosine sulfation, C-terminal amidation, peptide-related impurities, potency, residual solvents/reagents, sterility and endotoxin control for the parenteral product. The current approved formulation and excipient list require confirmation from the official label and product-quality documents.

## 11. Bioinformatics annotation

- entity_type: synthetic modified octapeptide
- peptide_family: cholecystokinin-related peptide
- sequence: DY(SO3H)MGWMDF-NH2
- modifications: O-sulfated tyrosine; C-terminal amidation
- primary_receptor: CCK1 / CCK-A receptor
- signalling: Gq/11–PLC–IP3/DAG–intracellular calcium
- pharmacology: gallbladder contraction; pancreatic enzyme secretion
- clinical_role: diagnostic secretagogue
- route: intravenous

Do not classify sincalide as a GLP-1 analogue, somatostatin analogue, pancreatic enzyme replacement or gallstone treatment.

## 12. Evidence gaps

- Verify exact workbook row, brand and status against the source workbook during reconciliation.
- Retrieve the current official Kinevac label and confirm dose, vial strength, reconstitution, excipients, stability, contraindications and adverse-event frequencies.
- Verify FDA application number, approval history and current marketing status using Drugs@FDA and the Orange Book.
- Verify EU, UK and CDSCO status.
- Add primary sources for sequence, receptor signalling and human pharmacology.
- Curate protocol-specific GBEF reference ranges without mixing infusion protocols.
- Add claim-level source locators and licensed, attributable structure/mechanism imagery.

**Completion decision:** principal peptide identity, sequence modifications, CCK1 mechanism and diagnostic role are described at a general pharmacology level. Exact current product-label details, regulatory availability and protocol-specific clinical evidence remain to be verified. Status: **in_progress**.

## References

1. US FDA / DailyMed. **Kinevac (sincalide) prescribing information**. Search current label and product record: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=Kinevac
2. US FDA. **Drugs@FDA database** — search Kinevac/sincalide to verify application history and current status: https://www.accessdata.fda.gov/scripts/cder/daf/
3. Society of Nuclear Medicine and Molecular Imaging. **Practice guidance for hepatobiliary scintigraphy**; consult current version: https://snmmi.org/
4. Ziessman HA, et al. Sincalide-stimulated cholescintigraphy: a multicenter investigation to determine optimal infusion methodology and gallbladder ejection fraction normal values. *Journal of Nuclear Medicine*. 2010;51(2):277–281. https://doi.org/10.2967/jnumed.109.069393
5. NCBI PubChem. **Sincalide** chemical identity record; cross-check modifications and salt form against the approved label: https://pubchem.ncbi.nlm.nih.gov/#query=sincalide

---
*Educational and research curation only. Not medical advice or a substitute for the current product label, validated nuclear-medicine protocols or specialist interpretation.*
