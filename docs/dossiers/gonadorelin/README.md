# 045 — Gonadorelin (synthetic GnRH)

**Curation status:** in_progress  
**Workbook sequence:** 045  
**Entity class:** synthetic decapeptide; hypothalamic gonadotropin-releasing hormone analogue  
**Evidence cut-off:** 4 November 2026

> **Scope.** Gonadorelin is synthetic gonadotropin-releasing hormone (GnRH), identical in amino-acid sequence to endogenous human hypothalamic GnRH. Its effect depends on exposure pattern: a single or pulsatile stimulus promotes pituitary gonadotropin release, whereas sustained receptor stimulation can desensitize/downregulate the axis. Products and indications differ by jurisdiction and formulation.

## 1. Identity and provenance

| Attribute | Curated record |
|---|---|
| Generic name | Gonadorelin |
| Other names | Gonadorelin acetate; GnRH; LHRH |
| Class | Hypothalamic releasing hormone; GnRH receptor agonist |
| Length | 10 amino acids |
| Route | Product-dependent; IV, SC or infusion systems in historical/current labels |
| US product history | Factrel (diagnostic IV product) and Lutrepulse (pulsatile infusion product) have historical US application records |
| Current US marketing status | Must be verified by exact product and presentation; historical approval does not prove current availability |

## 2. Molecular identity and sequence

- **Sequence:** `pGlu-His-Trp-Ser-Tyr-Gly-Leu-Arg-Pro-Gly-NH2`.
- **Length:** 10 residues (decapeptide).
- **Modifications:** N-terminal pyroglutamate (cyclized glutamate) and C-terminal glycinamide.
- **Molecular formula:** C55H75N17O13.
- **Molecular weight:** approximately 1,182.3 Da for the free peptide; acetate salt/product values differ.
- **Chemical class:** linear GnRH decapeptide with terminal modifications.

The peptide sequence is conserved between human endogenous GnRH and synthetic gonadorelin. Gonadorelin acetate is a salt form; salt mass must not be confused with peptide molecular mass.

## 3. Physiological role

Endogenous GnRH is secreted in pulses by hypothalamic neurons into the hypophyseal portal circulation. It binds GnRH receptors on anterior pituitary gonadotrophs and regulates synthesis and secretion of luteinizing hormone (LH) and follicle-stimulating hormone (FSH). Pulse frequency and amplitude influence the relative gonadotropin response. Sex steroids and inhibin provide feedback regulation.

## 4. Mechanism of action

**GnRH receptor agonism:**

1. Gonadorelin binds the pituitary GnRH receptor (GnRHR), a class A GPCR.
2. Receptor signalling couples predominantly to Gq/11 and activates phospholipase C-beta.
3. PLC generates IP3 and DAG; IP3 increases intracellular calcium and DAG activates protein kinase C.
4. Calcium- and PKC-dependent signalling promotes synthesis and secretion of LH and FSH.
5. With physiological intermittent exposure, pituitary gonadotroph responsiveness is maintained. Sustained continuous exposure initially stimulates gonadotropin release but subsequently causes receptor desensitization/downregulation and suppression of LH/FSH and gonadal steroid production.

Thus, gonadorelin is not intrinsically “fertility stimulating” or “suppressive” in every regimen; its biological outcome depends critically on dosing pattern.

## 5. Clinical and diagnostic uses

Historical and jurisdiction-specific uses include:
- **Diagnostic assessment of pituitary gonadotroph function:** a controlled GnRH challenge may assess LH/FSH response in selected endocrine evaluations.
- **Pulsatile replacement:** intermittent delivery has been used to restore GnRH signalling in hypothalamic GnRH deficiency and induce gonadotropin-dependent gonadal function.
- **Reproductive medicine:** pulsatile GnRH regimens have been used in selected patients with hypothalamic amenorrhoea or hypogonadotropic hypogonadism.

Do not extrapolate these uses to every gonadorelin product. Specific indications and dosing must be linked to the exact approved product label and jurisdiction. It is not interchangeable with long-acting depot GnRH agonists such as leuprolide, goserelin or triptorelin.

## 6. Administration and formulation

Gonadorelin has been supplied as an injectable acetate salt and in dedicated pulsatile infusion systems. Administration route and preparation depend on the product:
- diagnostic challenge products use a discrete IV dose under supervision;
- pulsatile replacement uses a programmed pump delivering small intermittent doses, commonly by subcutaneous or intravenous route depending on the system and label.

Exact current vial strength, dose, infusion pulse interval, reconstitution solvent, stability and device instructions require product-specific label verification. Do not use one regimen as a universal gonadorelin dose.

## 7. Pharmacology and disposition

- **Pharmacodynamics:** pituitary GnRHR activation with LH and FSH release.
- **Exposure pattern:** intermittent/pulsatile versus continuous exposure produces materially different endocrine effects.
- **Half-life and clearance:** rapid peptide clearance is expected; definitive product-specific human PK values should be sourced from the relevant label or primary study before populating numeric fields.
- **Clinical response:** depends on pituitary reserve, prior GnRH exposure, sex, age, pubertal stage, gonadal feedback and sampling time.

## 8. Safety and precautions

Potential adverse effects vary by route, dose and clinical setting. Reported effects with GnRH stimulation or pulsatile use may include transient flushing, headache, nausea, abdominal discomfort and injection/infusion-site reactions. Changes in gonadotropins and sex steroids can affect menstrual or gonadal symptoms.

Review the current product-specific label for hypersensitivity, pregnancy, lactation, contraindications, interactions, device-related risks and adverse-event frequencies. A stimulation test should be performed with appropriate clinical supervision and timed hormone sampling.

## 9. Regulatory status

| Jurisdiction | Status |
|---|---|
| United States | Historical FDA-approved product records include Factrel (diagnostic) and Lutrepulse (pulsatile delivery); current commercial status of each requires verification |
| European Union | Product-specific national authorization/availability not independently verified |
| United Kingdom | Product-specific status not independently verified |
| India (CDSCO) | Not independently verified |
| Other regions | Not independently verified |

Do not treat historical approval of a diagnostic product as proof that a pulsatile delivery product is currently marketed, or vice versa. Gonadorelin acetate, gonadorelin hydrochloride and product/device presentations must be tracked separately.

## 10. Quality and analytical characterization

Relevant quality attributes for synthetic gonadorelin include sequence identity, N-terminal pyroglutamate formation, C-terminal amidation, peptide-related impurities, counterion content, water content, potency, residual solvents/reagents, sterility, endotoxin and formulation stability. For pump-based delivery, device accuracy, pulse timing, adsorption to delivery materials and in-use stability are additional considerations.

## 11. Bioinformatics annotation

- entity_type: synthetic modified decapeptide
- peptide_family: hypothalamic GnRH
- sequence: pGlu-His-Trp-Ser-Tyr-Gly-Leu-Arg-Pro-Gly-NH2
- length_aa: 10
- receptor: GnRHR
- signalling: Gq/11–PLCβ–IP3/DAG–Ca2+/PKC
- primary_effect: pituitary LH and FSH synthesis/secretion
- exposure_dependence: pulsatile stimulation versus continuous desensitization
- clinical_role: diagnostic challenge and, in selected settings, pulsatile hormone replacement

Do not classify gonadorelin as a gonadotropin (LH/FSH), steroid hormone, or long-acting depot GnRH agonist.

## 12. Evidence gaps and completion tasks

- Reconcile exact workbook brand names, treatment categories and row notes.
- Verify current and historical FDA application numbers, labels and marketing status for Factrel and Lutrepulse.
- Verify current national product status in EU/UK and CDSCO India.
- Add sequence accession and authoritative chemical identity record for the acetate salt.
- Curate product-specific dosing and infusion-pump instructions only from official labels.
- Add primary human studies supporting pulsatile versus continuous exposure and diagnostic response interpretation.
- Add claim-level source locators and appropriately licensed molecular/mechanism imagery.

**Completion decision:** molecular sequence, receptor mechanism and exposure-pattern dependence are curated at a general scientific level. Exact product-specific regulatory status, current formulations, dosing and jurisdictional availability require further verification. Status: **in_progress**.

## References

1. NCBI PubChem. **Gonadorelin** chemical identity record; verify terminal modifications and salt form against product documentation: https://pubchem.ncbi.nlm.nih.gov/#query=gonadorelin
2. US FDA. **Drugs@FDA database** — search Factrel, Lutrepulse and gonadorelin for application history and current labelling: https://www.accessdata.fda.gov/scripts/cder/daf/
3. DailyMed. **Gonadorelin / Factrel label search**: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=gonadorelin
4. Conn PM, Crowley WF Jr. Gonadotropin-releasing hormone and its analogues. *N Engl J Med*. 1991;324:93–103. https://doi.org/10.1056/NEJM199101103240205
5. Millar RP, et al. Gonadotropin-releasing hormone receptors. *Endocrine Reviews* and primary GnRHR signalling literature; curated PubMed search: https://pubmed.ncbi.nlm.nih.gov/?term=gonadotropin+releasing+hormone+receptor+Gq+signalling
6. Endotext. **Physiology of the hypothalamic-pituitary-gonadal axis**; use current chapter version for pulsatile regulation: https://www.ncbi.nlm.nih.gov/books/

---
*Educational and research curation only. Not medical advice or a substitute for current product labelling, endocrine specialist assessment or validated diagnostic protocols.*
