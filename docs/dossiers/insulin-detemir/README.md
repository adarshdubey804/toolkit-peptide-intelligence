# Insulin detemir (Levemir) — dossier 005

**Curation status:** `in_progress`  
**Workbook relationship:** candidate corresponding to the insulin detemir / Levemir entry; retain the original workbook row and its provenance when imported.  
**Entity class:** modified peptide / recombinant insulin analogue  
**Primary source jurisdiction:** United States  
**Evidence policy:** product-label facts below are tied to the cited Levemir label. Do not transfer formulation, indication, or presentation details to other insulin detemir products without checking their own labels.

## 1. Identity and nomenclature

- **INN / active substance:** insulin detemir.
- **Reference brand:** Levemir.
- **Molecule type:** long-acting, acylated human insulin analogue; two-chain peptide hormone analogue.
- **Producer / origin:** recombinant DNA expression in *Saccharomyces cerevisiae*, followed by chemical modification, according to the product label.
- **Biological role:** exogenous insulin analogue used for basal glycaemic control in diabetes mellitus.
- **Identity confidence:** high for the reference Levemir product; workbook synonym and row-level identity should still be reconciled at import.

## 2. Sequence and structural modifications

The official product description states that insulin detemir differs from human insulin by:
1. omission of threonine at position B30; and
2. attachment of a C14 fatty-acid chain to lysine at position B29.

This is a product-label-level description. The complete A- and B-chain residue strings, stereochemistry, disulfide connectivity, and atom-level structure should be independently cross-checked against a curated sequence/structure source before being populated as canonical machine-readable sequence data. Do not infer a full sequence from the modification summary alone.

## 3. Chemical properties

| Property | Verified label value |
|---|---|
| Molecular formula | C267H402N64O76S6 |
| Molecular weight | 5916.9 Da (5.9169 kDa) |
| Fatty-acid modification | C14 chain attached at LysB29 |
| Deleted residue | ThrB30 |

The label describes a neutral, clear, colourless aqueous solution. These are formulation attributes, not intrinsic properties of the isolated peptide.

## 4. Mechanism of action

### 4.1 Primary pharmacological mechanism

Insulin detemir binds insulin receptors. Receptor activation lowers blood glucose by:
- increasing glucose uptake in skeletal muscle and adipose tissue;
- reducing hepatic glucose output;
- inhibiting lipolysis and proteolysis; and
- enhancing protein synthesis.

This is the insulin class mechanism described in the prescribing information.

### 4.2 Why its action is prolonged

The C14 acyl chain supports self-association at the subcutaneous injection site and reversible albumin binding. The label attributes prolonged action to slower systemic absorption associated with self-association and slower distribution to peripheral target tissues associated with albumin binding. More than 98% of circulating insulin detemir is albumin-bound in the cited label.

**Mechanistic distinction:** albumin binding and delayed absorption extend exposure; they do not represent a different receptor target. The pharmacological target remains the insulin receptor.

## 5. Pharmacodynamics

- Classified as a soluble, long-acting basal human insulin analogue.
- The label reports a relatively constant pharmacodynamic profile without a pronounced peak.
- Duration can be up to 24 hours, but is dose-dependent and varies between individuals.
- The label's clinical pharmacology discussion reports a wide observed duration range; do not present 24 hours as a guaranteed duration for every dose or patient.

## 6. Pharmacokinetics

The cited label reports:
- relatively constant serum concentration/time profile over 24 hours after subcutaneous administration;
- time to maximum serum concentration (Cmax): approximately 6–8 hours;
- absolute bioavailability: approximately 60%;
- more than 98% plasma protein binding, primarily albumin;
- apparent volume of distribution: approximately 0.1 L/kg.

The full label should be consulted for the complete elimination and dose-response details. Do not extrapolate these figures to other formulations or routes.

## 7. Manufacturing and formulation

- **Biotechnological production:** recombinant DNA expression in *S. cerevisiae*.
- **Post-expression processing:** chemical modification to attach the C14 fatty-acid chain.
- **Reference formulation:** sterile aqueous solution for subcutaneous use, pH approximately 7.4.
- **Labelled excipients (historical reference formulation):** zinc, m-cresol, glycerol, phenol, disodium phosphate dihydrate, sodium chloride, and water for injection; pH adjustment may use hydrochloric acid and/or sodium hydroxide.

Excipient composition can vary by market, presentation, and label revision. The list above must not be assumed to describe every marketed insulin detemir product.

## 8. Regulatory history and market status

- **United States initial approval:** 16 June 2005 (BLA 021536).
- FDA's Purple Book lists the Levemir presentations under BLA 021536 and currently marks the listed reference product presentations as discontinued.
- FDA's discontinued biologic product list records different dates for individual presentations; for example, the vial presentation was added on 31 December 2024, while FlexTouch and other presentations have earlier discontinued-list dates.
- **Interpretation:** discontinued marketing status is not equivalent to withdrawal for a safety reason and does not erase the original approval history. State the jurisdiction and presentation whenever reporting status.
- **Current status outside the United States:** not established in this dossier; requires country-specific regulatory verification.

## 9. Indications and administration

The cited US prescribing information indicates Levemir to improve glycaemic control in adults and paediatric patients with diabetes mellitus. It is not recommended for treatment of diabetic ketoacidosis. The reference label specifies subcutaneous administration and individualized dosing; consult the current local product information for exact age ranges, device instructions, and dosing guidance.

This dossier is scientific documentation, not a dosing recommendation.

## 10. Safety and precautions

Important risks described in insulin detemir prescribing information include:
- hypoglycaemia, including severe hypoglycaemia;
- hypersensitivity reactions;
- hypokalaemia;
- medication errors and accidental mix-ups with other insulin products;
- injection-site reactions, lipodystrophy, and localized cutaneous amyloidosis;
- fluid retention and heart failure risk when used with thiazolidinediones.

The complete adverse-reaction frequencies, contraindications, warnings, pregnancy/lactation information, paediatric evidence, and post-marketing reports remain to be extracted and reconciled from the applicable current label(s).

## 11. Drug interactions

The label warns that several classes can affect glucose-lowering response and hypoglycaemia risk. A complete interaction table has not yet been curated here. Add each interaction only with a cited label or authoritative interaction source, distinguishing pharmacodynamic effects from pharmacokinetic interactions.

## 12. Clinical evidence

The regulatory label is the starting point for approved-use evidence, not a complete clinical-trial bibliography. The following still require structured extraction:
- pivotal efficacy and safety trials;
- comparator insulin trials;
- paediatric studies;
- special-population studies;
- systematic reviews and meta-analyses;
- trial registry identifiers and publication links.

No unsupported efficacy superiority claim is made in this dossier.

## 13. Structure, images, and visual assets

- FDA/DailyMed label contains a structural formula figure for insulin detemir.
- **Image status:** no image file has been copied into this dossier. The label figure is linked as a source reference only; reuse permissions and a suitable downloadable asset must be checked before local redistribution.
- A canonical 3D structure, coordinate file, rendering, and chain-level annotated structure remain pending.

## 14. Bioinformatics and systems biology

Pending curation:
- canonical chain sequence with residue numbering;
- disulfide-bond map;
- post-translational / chemical modification annotation;
- structure accession and structure-quality assessment;
- insulin receptor interaction evidence;
- pathway mapping (insulin receptor signalling, PI3K–AKT, glucose transport, hepatic glucose metabolism);
- relevant gene/protein identifiers and controlled vocabularies.

Do not treat general insulin pathway knowledge as detemir-specific experimental evidence.

## 15. Intellectual property and commercial landscape

Patent-family, exclusivity, biosimilar, regional market, and manufacturer information have not yet been exhaustively researched. Record each patent by publication number, jurisdiction, priority date, legal status, and source before drawing conclusions.

## 16. Evidence and references

1. **DailyMed — LEVEMIR (insulin detemir) prescribing information.** Includes recombinant production, the B30 deletion and B29 C14 acylation, formula, molecular weight, formulation, mechanism, pharmacodynamics, and pharmacokinetics.  
   https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=eae6fcac-02a9-4d7c-8445-03a647b6b59b
2. **FDA — LEVEMIR 2022 prescribing information (BLA 021536).** Initial US approval, indications, dosage/administration and safety information.  
   https://www.accessdata.fda.gov/drugsatfda_docs/label/2022/021536s060lbl.pdf
3. **FDA Purple Book — Product details for BLA 021536 (Levemir).** Original approval date and presentation-level marketing status.  
   https://purplebooksearch.fda.gov/index.cfm?blaNo=021536&event=productdetails
4. **FDA — CDER Discontinued Biologic Product List.** Presentation-specific discontinued-list dates for Levemir products.  
   https://www.fda.gov/media/186099/download

## 17. Outstanding curation checklist

- [ ] Reconcile exact workbook row, aliases, and imported provenance.
- [ ] Verify complete canonical A- and B-chain sequences and residue numbering.
- [ ] Add curated molecular structure and validated structure accession.
- [ ] Extract complete label sections: contraindications, warnings, adverse reactions, special populations, overdose, storage, and handling.
- [ ] Build cited interaction matrix.
- [ ] Add pivotal clinical trials and registry records.
- [ ] Add comparative systematic reviews without overstating superiority.
- [ ] Verify regulatory status in each relevant jurisdiction.
- [ ] Verify patent families and current legal status.
- [ ] Add image/structure assets with attribution and reuse licence.
- [ ] Complete pathway and target-evidence annotations.
- [ ] Independent scientific review and final source audit.

**Completion rule:** this file is an evidence-backed working dossier, not a completed A-to-Z monograph. Keep status as `in_progress` until all applicable checklist items are completed and independently reviewed.
