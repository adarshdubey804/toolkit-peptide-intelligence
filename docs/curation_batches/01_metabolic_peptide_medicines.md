# Curation batch 01 — metabolic peptide medicines

**Scope:** workbook rows 1–21 (insulin family, pramlintide, incretin agonists, glucagon analogues, setmelanotide and investigational metabolic peptides).
**Review date:** 2026-11-03.
**Status:** first-pass mechanism and evidence map; not a completed A-to-Z dossier. Exact sequence, stereochemistry, molecular mass, product-specific PK, contraindications and approval chronology must be captured from each current product label and primary development record before a record can be marked curated.

## Evidence hierarchy for this batch

1. Current FDA-approved prescribing information / Drugs@FDA application record for each finished product.
2. FDA review documents for sequence, pharmacology, clinical evidence and development history.
3. Primary peer-reviewed studies for mechanistic detail not fully stated in labels.
4. UniProt/PubChem/ChEBI or primary structural papers for molecular identity and chemistry. Database predictions must be labelled as such.

FDA review documents list insulin analogues, pramlintide, GLP-1 receptor agonists and tirzepatide as distinct therapeutic classes; this is useful class-level evidence, not a substitute for individual labels. [FDA clinical review of insulin aspart/Fiasp](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2026/208751Orig1s011.pdf) and [FDA clinical review of insulin icodec](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2026/761326Orig2s000MedR.pdf).

## Mechanism map — class-level only

| Workbook entries | Mechanism to investigate and document | Key caveat |
|---|---|---|
| Human insulin; lispro; aspart; glargine; glulisine; detemir; degludec | Agonism at the insulin receptor; altered sequence and/or formulation changes absorption, onset and duration | Do not copy one insulin's sequence or PK onto another. Distinguish analogue sequence substitutions from formulation/excipient effects. |
| Pramlintide | Amylin-receptor agonist; slows gastric emptying, suppresses inappropriate post-meal glucagon secretion and promotes satiety | Label-specific use is adjunctive to mealtime insulin; include severe hypoglycaemia warning and product-specific administration restrictions. |
| Exenatide; liraglutide; lixisenatide; dulaglutide; semaglutide | GLP-1 receptor agonism; glucose-dependent insulin secretion, glucagon suppression and delayed gastric emptying; weight effects vary by molecule, dose and indication | Distinguish products, formulations, indications and dose-specific labels. Do not generalize an obesity indication to every brand/formulation. |
| Tirzepatide | Dual GIP and GLP-1 receptor agonism | Do not describe as a GLP-1-only agonist. |
| Glucagon; dasiglucagon | Glucagon receptor agonism, increasing hepatic glucose output during severe hypoglycaemia | Record product formulation and route; emergency rescue use differs from diagnostic glucagon use. |
| Setmelanotide | MC4 receptor agonism in specific genetically defined obesity syndromes | Indication is genotype/diagnosis-specific; do not extrapolate to common obesity. |
| Cagrilintide | Long-acting amylin analogue under clinical investigation | Investigational; CagriSema is a combination candidate (cagrilintide + semaglutide), not a synonym for cagrilintide alone. |
| Retatrutide | Triple agonist at GIP, GLP-1 and glucagon receptors under investigation | Investigational; distinguish from marketed incretin medicines. |
| Survodutide | Dual glucagon/GLP-1 receptor agonist under investigation | Investigational; do not infer FDA approval from trial activity. |
| Mazdutide | Dual GLP-1/glucagon receptor agonist; approval exists in China, not US per workbook source classification | Recheck current Chinese NMPA record and US status independently at review date. |

## Supported source notes

- FDA's current consumer overview identifies several GLP-1 receptor agonists and pramlintide as marketed diabetes medicines and distinguishes them from insulin. [FDA: Diabetes medicines](https://www.fda.gov/consumers/womens-health-topics/women-and-diabetes-diabetes-medicines).
- FDA clinical review materials classify pramlintide as an amylin mimetic, GLP-1 medicines as GLP-1 receptor agonists, insulin analogues as a separate class, and tirzepatide as a GIP/GLP-1 receptor agonist. [FDA review, Fiasp](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2026/208751Orig1s011.pdf); [FDA review, insulin icodec](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2026/761326Orig2s000MedR.pdf).
- The DailyMed Apidra label provides an example of the product-specific evidence needed: insulin glulisine is identified as a rapid-acting human insulin analogue, with initial US approval in 2004 and current indications. [DailyMed: Apidra](https://www.dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e7af6a7a-8046-4fb4-9979-4ec4230b23aa).
- FDA's label repository explains that submitted labels are not necessarily identical to the currently distributed product label or independently verified by FDA; therefore the current official application record and label version must be captured for each dossier. [FDA Online Label Repository](https://labels.fda.gov/).

## Per-record completion checklist

For each of rows 1–21, create an independent dossier and complete:

- [ ] Preferred name, synonyms, active moiety, marketed product(s), salts/esters and combination products
- [ ] Peptide/protein scope class; residue count; sequence with stereochemistry and noncanonical residues
- [ ] Chemical formula, molecular mass, modifications, disulfide bonds, structure depiction and source
- [ ] Target/receptor, binding evidence, signalling pathway and mechanism with primary citations
- [ ] Pharmacodynamics and pharmacokinetics (species, route, formulation, population and study design attached to each value)
- [ ] FDA and non-US regulatory status with application/label IDs, dates, indication and jurisdiction
- [ ] Clinical trials with registry IDs and outcomes; separate preclinical evidence
- [ ] Contraindications, warnings, adverse reactions, interactions, pregnancy/lactation and special populations from label
- [ ] Formulation, excipients, storage/stability, manufacturing and patents where documented
- [ ] Images: sourced molecular depiction or experimental structure, caption, attribution, licence and prediction flag
- [ ] Claim-level references and audit date

**Curation state for this batch remains `in_progress`.** No full dossier is marked complete by this batch-level mechanism map.