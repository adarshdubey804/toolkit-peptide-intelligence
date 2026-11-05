# 053 — Desmopressin (DDAVP and formulation-specific products)

**Curation status:** in_progress  
**Workbook sequence:** 053 (Peptides sheet data row 49; Excel row 51)  
**Entity class:** synthetic modified nonapeptide; vasopressin analogue  
**Evidence cut-off:** 4 November 2026

## 1. Identity and provenance

| Attribute | Curated record |
|---|---|
| Generic name | Desmopressin (desmopressin acetate in many products) |
| Brands / products | DDAVP, Stimate (historical nasal product; verify current status), Nocdurna, Noctiva (historical US product; verify current status), formulation-specific generics |
| Drug class | Vasopressin V2-receptor agonist; antidiuretic |
| Molecular class | Synthetic modified cyclic nonapeptide |
| US first approval | DDAVP injection approved 1978 (verify exact original NDA action date and product history) |
| Routes | IV, subcutaneous, intranasal, oral tablets, oral lyophilisate/sublingual tablet; availability and indications vary by product |
| Core pharmacology | V2 receptor activation in renal collecting duct; increased water reabsorption |
| Workbook indications | Central diabetes insipidus; haemophilia A / von Willebrand disease; nocturnal enuresis |

**Workbook provenance:** the workbook's 053rd entry is desmopressin, listing DDAVP, Stimate and Nocdurna. Those are not interchangeable presentations; the indication, route, dose and fluid restrictions differ by product label.

## 2. Molecular identity and sequence

Desmopressin is a synthetic nonapeptide analogue of arginine vasopressin.

**Sequence:**  
Mpr-Tyr-Phe-Gln-Asn-Cys-Pro-D-Arg-Gly-NH₂

Where **Mpr** denotes 1-mercaptopropionic acid (also called 3-mercaptopropionic acid) replacing the native N-terminal cysteine residue. The Mpr residue forms a disulfide bond with Cys⁶, producing a six-membered cyclic ring; the peptide has a D-Arg at position 8 in place of native L-Arg.

Key structural modifications relative to arginine vasopressin:
- N-terminal deamination / replacement of Cys¹ by 1-mercaptopropionic acid;
- D-Arg at position 8;
- C-terminal amidation;
- intramolecular disulfide linkage between Mpr¹ and Cys⁶.

The acetate is a counterion in many drug substances and should not be conflated with the covalent peptide structure. Confirm formula and molecular mass on a clearly stated free-peptide or acetate-salt basis before populating the canonical chemistry record.

## 3. Structure–activity and receptor selectivity

The substitutions increase antidiuretic activity and duration relative to endogenous vasopressin while reducing vasopressor activity. Desmopressin is predominantly a V2-receptor agonist at therapeutic doses, although selectivity is not absolute under all exposure conditions.

The disulfide-constrained ring and D-Arg substitution contribute to receptor interaction and resistance to enzymatic degradation. The molecule is not a GHRH analogue or a growth-hormone secretagogue.

## 4. Disease biology

### Central diabetes insipidus (central AVP deficiency)
Central diabetes insipidus (also termed arginine vasopressin deficiency in newer nomenclature) results from inadequate synthesis or release of vasopressin. The kidney cannot appropriately concentrate urine, causing polyuria, polydipsia and risk of hypernatraemic dehydration. Desmopressin replaces the missing antidiuretic signal at renal V2 receptors.

### Haemophilia A and von Willebrand disease
Endothelial Weibel–Palade bodies store von Willebrand factor (VWF) and factor VIII-associated material. Desmopressin can trigger release of endogenous VWF and increase circulating factor VIII in responsive patients. It is useful only for selected subtypes and patients with an adequate response.

### Nocturnal polyuria / nocturnal enuresis
Desmopressin reduces renal free-water excretion overnight. Product-specific labels distinguish adult nocturia due to nocturnal polyuria from paediatric primary nocturnal enuresis; the latter indication and available products vary by country and formulation.

## 5. Mechanism of action

### Renal antidiuretic action
1. Desmopressin binds V2 receptors (AVPR2) on the basolateral membrane of collecting-duct principal cells.
2. V2 couples to Gs, activating adenylyl cyclase and increasing intracellular cAMP.
3. PKA signalling promotes trafficking and insertion of aquaporin-2 (AQP2) water channels into the apical membrane.
4. Collecting-duct water permeability rises, increasing water reabsorption and concentrating urine.

### Haemostatic action
Desmopressin stimulates release of endogenous VWF and increases plasma factor VIII activity in responsive individuals. It does not supply factor VIII or VWF directly and is not appropriate for every haemophilia A or von Willebrand disease subtype.

## 6. Indications: do not merge product labels

Desmopressin has multiple indications, but **each is formulation- and product-specific**.

- **Central diabetes insipidus:** selected injectable, intranasal and oral products are labelled for central DI; nephrogenic DI is not treated by desmopressin in the same way.
- **Haemophilia A / von Willebrand disease:** certain injectable or intranasal formulations are labelled to raise endogenous factor VIII and VWF in responsive patients. Confirm subtype, baseline level and documented response.
- **Adult nocturia due to nocturnal polyuria:** Nocdurna sublingual tablets have a specific adult indication and sex-specific labelled doses. This is not equivalent to paediatric enuresis treatment.
- **Primary nocturnal enuresis:** some oral or intranasal product labels in certain jurisdictions have included this use; current US product availability and label status must be verified before assigning it.

Stimate and Noctiva have had market discontinuation / availability changes. A historic brand name in the workbook does not prove that the product is currently marketed.

## 7. Administration and dose principles

There is no single universal desmopressin dose. Dose depends on route, indication, product concentration, age, sex, renal function, fluid intake and response.

- Injectable, intranasal, oral tablet and sublingual products have markedly different bioavailability and dose units.
- Nocdurna uses sex-specific low-dose sublingual regimens for adult nocturia because women are more sensitive to the antidiuretic effect and hyponatraemia risk.
- Haemostatic use requires assessment of response and repeat-dose limitations; tachyphylaxis can occur with repeated administration.
- Fluid intake must be restricted according to the exact product label and indication, especially around nocturia treatment.

**Do not convert doses between routes or brands using simple arithmetic.** Use the current product-specific label and specialist protocol.

## 8. Pharmacodynamics and pharmacokinetics

- Antidiuretic effect is mediated primarily through renal V2 receptors and AQP2 trafficking.
- Haemostatic response includes increases in VWF and factor VIII in responsive patients.
- Onset and duration depend strongly on route and formulation.
- Desmopressin is a peptide with limited oral bioavailability; oral and sublingual formulations use product-specific delivery strategies.
- Renal impairment can prolong exposure and increase hyponatraemia risk; product labels contain important renal-function restrictions.
- Exact half-life, exposure and bioavailability should be transcribed separately for each route and product, not combined into one value.

## 9. Safety: hyponatraemia is the critical class risk

**Severe hyponatraemia and water intoxication can cause seizures, coma, respiratory arrest and death.** This is the central safety issue across antidiuretic uses.

Risk controls:
- assess serum sodium before initiation when required by the product label;
- restrict fluid intake according to product-specific instructions;
- monitor serum sodium at label-specified intervals, especially after initiation or dose changes;
- avoid or use extreme caution in patients with conditions or medicines that increase water retention or hyponatraemia risk;
- observe renal-function contraindications and dose restrictions;
- interrupt treatment during acute illnesses or circumstances that disturb fluid/electrolyte balance when required by the label.

Other risks include headache, nausea, abdominal symptoms, blood-pressure effects and, for haemostatic use, thrombotic risk in susceptible patients. Injectable products may cause local reactions.

Nocdurna carries particularly prominent hyponatraemia warnings and requires sodium monitoring. Do not copy its monitoring schedule to other formulations without checking their labels.

## 10. Contraindications and interaction considerations

Contraindications vary by formulation. Product labels may include current or prior hyponatraemia, polydipsia, moderate-to-severe renal impairment, SIADH, loop diuretic use, systemic or inhaled glucocorticoids (for certain products), and acute illnesses associated with fluid/electrolyte imbalance.

Medicines that can increase hyponatraemia risk include SSRIs, tricyclic antidepressants, thiazide diuretics, NSAIDs, opioids, carbamazepine, lamotrigine and other agents associated with SIADH or impaired water excretion. This is not a complete interaction list; check the exact label.

## 11. Formulation and manufacturing

Desmopressin is supplied in several distinct dosage forms:
- sterile injectable solution (IV/SC);
- metered intranasal spray or solution;
- oral tablets;
- sublingual/oral lyophilisate tablets.

The peptide active ingredient may be supplied as acetate salt. Product-specific excipients, preservatives, concentrations and delivery devices differ. Critical quality attributes include peptide identity, stereochemical integrity at D-Arg⁸, correct Mpr–Cys disulfide formation, peptide-related impurities, acetate content, assay, stability, sterility (parenteral), spray performance (nasal) and dissolution / disintegration (oral products).

## 12. Bioinformatics annotation

| Field | Annotation |
|---|---|
| Entity type | Synthetic modified nonapeptide |
| Sequence | Mpr-Tyr-Phe-Gln-Asn-Cys-Pro-D-Arg-Gly-NH₂ |
| Length | 9 peptide positions including Mpr |
| Key modifications | Mpr¹ substitution; D-Arg⁸; C-terminal amide |
| Crosslink | Mpr¹–Cys⁶ disulfide |
| Main renal target | V2 receptor (AVPR2) |
| Haemostatic effect | Release of endogenous VWF / increase in factor VIII |
| Renal signalling | Gs–adenylyl cyclase–cAMP–PKA–AQP2 |
| Main clinical contexts | Central DI; responsive haemophilia A / VWD; selected nocturia products |
| Critical safety signal | Hyponatraemia / water intoxication |

## 13. Regulatory status

| Jurisdiction | Status |
|---|---|
| United States | Multiple FDA-approved desmopressin products; first DDAVP injection approval historically dated 1978; individual NDAs and labels differ |
| European Union / EEA | Multiple nationally authorised products; route and indication differ by member state |
| India | CDSCO approval and marketed product status require product-specific verification |
| Other regions | Not exhaustively verified |

A historic approval date for one presentation is not the first approval date for every desmopressin formulation.

## 14. Evidence gaps and completion checklist

- Verify workbook status fields and distinguish active vs discontinued brand presentations.
- Retrieve current FDA labels for DDAVP injection, oral tablets, Nocdurna and any currently marketed nasal products.
- Verify Stimate and Noctiva US marketing/discontinuation status from FDA and manufacturer notices.
- Capture exact product-specific contraindications, sodium monitoring schedules, fluid restrictions and renal cut-offs.
- Add primary clinical evidence for central DI, haemostatic response and adult nocturia separately.
- Verify molecular formula and mass basis for free peptide and acetate salt from authoritative chemistry sources.
- Verify current EU/UK and CDSCO product authorisations.
- Add a validated stereochemistry-aware structure record and reuse-cleared molecular/mechanism imagery.

**Completion decision:** peptide identity, receptor mechanisms, indication families, formulation distinctions and the central hyponatraemia risk are documented. Product-specific current availability, label-level dose/monitoring tables, trial-level data and jurisdictional status remain open. **Status: in_progress.**

## References

1. US FDA / DailyMed. **DDAVP (desmopressin acetate) injection and tablet prescribing information**: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=DDAVP
2. US FDA / DailyMed. **NOCdurna (desmopressin acetate) sublingual tablets prescribing information**: https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=NOCDURNA
3. US FDA. **Drugs@FDA application records and product labels**: https://www.accessdata.fda.gov/scripts/cder/daf/
4. US FDA. **Drug Safety Communications and product status information**: https://www.fda.gov/drugs
5. PubMed. **Desmopressin pharmacology, central diabetes insipidus and haemostatic use**: https://pubmed.ncbi.nlm.nih.gov/?term=desmopressin+central+diabetes+insipidus+von+Willebrand
6. PubMed. **Desmopressin for adult nocturia and hyponatraemia risk**: https://pubmed.ncbi.nlm.nih.gov/?term=desmopressin+nocturia+hyponatremia

---
*Educational and research curation only. Not medical advice or a substitute for current product labelling or specialist endocrine/haematology care.*
