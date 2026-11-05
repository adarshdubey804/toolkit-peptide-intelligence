# Insulin aspart — scientific dossier

> **Record ID:** metabolic-insulin-aspart  
> **Curation status:** in progress — identity and label-backed core facts reviewed; not a completed A-to-Z dossier.  
> **Review date:** 2026-11-03  
> **Source inventory:** `peptides_fda_status_by_treatment.xlsx`, Peptides sheet, row 3. Workbook entry retained as supplied.

## 1. Identity and classification

- **Preferred name:** insulin aspart
- **Brand examples:** NovoLog; Fiasp (formulation-specific product); NovoLog Mix products contain insulin aspart plus protamine-crystallized insulin aspart.
- **Molecular class:** recombinant, rapid-acting insulin analogue; two-chain peptide hormone / small protein.
- **Scope classification:** `modified_peptide` (sequence-defined insulin analogue).
- **Production host in NovoLog label:** recombinant DNA technology using *Saccharomyces cerevisiae*.
- **US initial approval:** 2000 for NovoLog. Do not apply this date automatically to Fiasp or premixed products.

## 2. Sequence and structural chemistry

Insulin aspart is homologous to human insulin except for a single substitution: **Asp replaces Pro at B-chain position 28 (ProB28Asp)**. The 21-residue A chain is unchanged; the 30-residue B chain contains Asp at B28.

**A chain (21 aa; one-letter code):** GIVEQCCTSICSLYQLENYCN  
**B chain (30 aa; one-letter code):** FVNQHLCGSHLVEALYLVCGERGFFYTDKT

The mature molecule contains two chains connected by two interchain disulfide bonds and one intrachain disulfide bond in the A chain. Confirm the bond numbering and sequence against the official label structural figure before importing a machine-readable structure.

- **Empirical formula:** C256H381N65O79S6
- **Molecular mass:** 5,825.8 Da
- **Residue count:** 51 amino-acid residues across two chains.
- **Modification:** ProB28Asp; no claim is made here about additional covalent modifications.
- **Structure image:** the current DailyMed NovoLog label contains a structural formula figure. Prefer linking to the label's image/figure with attribution rather than copying it into the repository without checking reuse terms.

## 3. Mechanism of action

Insulin aspart binds to insulin receptors on muscle and adipose cells. Insulin-receptor signalling increases peripheral glucose uptake and inhibits hepatic glucose production. Insulin also inhibits lipolysis and proteolysis and enhances protein synthesis.

The ProB28Asp substitution reduces self-association compared with regular human insulin, contributing to faster absorption after subcutaneous administration. The pharmacologic effect remains insulin-receptor agonism; it is not a distinct receptor-target mechanism.

## 4. Pharmacodynamics

The NovoLog label reports that after subcutaneous administration, maximum glucose-lowering effect in a study of 22 people with type 1 diabetes occurred between 1 and 3 hours; reported duration was 3–5 hours. These are study- and product-specific reference values, not guaranteed individual response times. Absorption and action vary with injection site, exercise and other factors.

Fiasp is a different formulation of insulin aspart with formulation-related changes to early absorption. Do not transfer NovoLog timing values to Fiasp without consulting its own current label.

## 5. Pharmacokinetics

The current DailyMed label should be used to extract product-specific absorption, distribution, metabolism and elimination data. Do not infer a conventional small-molecule half-life from the pharmacodynamic duration. Values may depend on route, formulation, renal/hepatic status and study population.

**PK curation state:** incomplete; label-specific tables and study conditions still need extraction.

## 6. Regulatory and product scope

- **NovoLog:** FDA-approved; initial US approval 2000. Official current label lists subcutaneous and intravenous use.
- **Fiasp:** separate insulin-aspart formulation and product label; workbook note records US approval in 2017. Verify current label and exact approval date from Drugs@FDA before finalising.
- **NovoLog Mix 70/30 and 50/50:** combination suspensions with protamine-crystallized and soluble insulin aspart; separate product dossiers are appropriate if included in inventory.
- **Approval of one brand/formulation does not establish identical indications, route, storage or administration instructions for another.**

## 7. Clinical use

Insulin aspart is used to improve glycaemic control in people with diabetes mellitus. Product labels differ in age indications, administration timing, pump compatibility and intravenous use. Extract these separately for NovoLog and Fiasp from their current official prescribing information.

## 8. Safety profile — label-backed topics

Important label warnings and precautions include:
- Hypoglycaemia, including severe hypoglycaemia.
- Hypokalaemia.
- Medication errors and accidental mix-ups between insulin products.
- Hypersensitivity reactions.
- Fluid retention and heart failure risk when insulin is combined with thiazolidinediones.
- Changes in insulin requirements with illness, changes in physical activity or meal pattern, and renal/hepatic impairment.

Commonly reported adverse reactions include hypoglycaemia, allergic reactions, injection-site reactions, lipodystrophy, rash and pruritus. Use the current label's exact frequency tables and wording for final structured adverse-event data.

## 9. Interactions

Label-relevant interaction categories include medicines that may increase or decrease glucose-lowering effect, agents that may mask hypoglycaemia symptoms (for example, beta-blockers), and thiazolidinediones associated with fluid retention/heart failure when combined with insulin. Capture the exact current label text and examples rather than treating this list as exhaustive.

## 10. Formulation — NovoLog U-100 example

The DailyMed NovoLog label describes a clear, colourless solution containing 100 units/mL insulin aspart. Listed inactive ingredients per mL include disodium hydrogen phosphate dihydrate, glycerin, metacresol, phenol, sodium chloride, zinc and Water for Injection; pH 7.2–7.6. Do not apply this excipient profile to Fiasp or premixed formulations.

## 11. Manufacturing and quality

The label identifies recombinant production in *Saccharomyces cerevisiae*. Detailed cell-bank controls, fermentation, purification, formulation process parameters, release specifications and commercial manufacturing sites are not reproduced here; these require public regulatory assessment reports or manufacturer disclosures. Do not infer proprietary process details.

## 12. Images and structure

- **Available official visual:** structural formula (A and B chains) embedded in the DailyMed NovoLog label.
- **Source:** https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=13891e5a-e57a-46e8-911c-2f680352b52b
- **Attribution:** NovoLog US prescribing information, Figure 1, DailyMed.
- **Reuse status:** verify image-specific copyright/reuse conditions before copying. Linking to the official label is preferred.
- **Experimental 3D structure:** not curated in this record; add only after matching an appropriate RCSB PDB entry to insulin aspart and recording chain/ligand context.

## 13. Evidence references

1. **DailyMed — NOVOLOG (insulin aspart) injection, current label record.** Description, molecular formula/mass, ProB28Asp substitution, formulation, mechanism, pharmacodynamics, warnings and interactions. https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=13891e5a-e57a-46e8-911c-2f680352b52b
2. **FDA label archive — NovoLog (2018).** Structural description, sequence figure and product description. https://www.accessdata.fda.gov/drugsatfda_docs/label/2018/020986s087lbl.pdf
3. **FDA Drugs@FDA.** Verify NDA approval chronology and supplements for NovoLog and Fiasp separately. https://www.accessdata.fda.gov/scripts/cder/daf/

## 14. Outstanding curation checklist

- [ ] Independently verify the A- and B-chain sequences against a curated protein record and official label figure.
- [ ] Verify disulfide bond connectivity and residue numbering from an authoritative structure.
- [ ] Extract full current NovoLog label PK tables with study conditions.
- [ ] Create a separate Fiasp dossier, including its formulation and product-specific PK/PD.
- [ ] Extract exact contraindications, adverse-event frequencies, warnings and interaction wording.
- [ ] Verify all indication, age, route, pump and administration details per product.
- [ ] Add clinical-trial registry identifiers and pivotal study references.
- [ ] Add a licensed/appropriately attributed molecular image or a verified PDB structure.
- [ ] Add source IDs, access dates and claim-level citations to the database.
- [ ] Record reviewer and independent verification status.

**Disclaimer:** This dossier is for scientific and research information, not a prescribing guide. It does not provide dosing or patient-specific treatment advice.