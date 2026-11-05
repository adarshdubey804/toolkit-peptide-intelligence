# Insulin lispro — scientific dossier

<small>Record ID: insulin-lispro | Version: 0.1.0 | Reviewed: 2026-11-03 | Curation state: in_progress</small>

> Research reference only. This dossier is not medical advice and does not provide dosing instructions.

## 1. Identity and nomenclature

- Preferred name: insulin lispro.
- Generic / nonproprietary name: insulin lispro.
- Brand examples in the workbook: Humalog, Admelog, Lyumjev. Brand-specific formulations and labels must be maintained as separate product records.
- Molecular class: recombinant rapid-acting human insulin analogue; two-chain peptide hormone / small protein.
- Scope classification: `modified_peptide` (sequence-modified insulin analogue; preserve its two-chain protein architecture).
- Expression system stated in Humalog label: recombinant DNA technology using a non-pathogenic laboratory strain of *Escherichia coli*.
- Initial US approval: 1996 (Humalog label).
- FDA status: approved product; verify each brand, concentration, delivery system and current label independently.

## 2. Sequence and molecular identity

Insulin lispro differs from human insulin by exchanging the residues at positions B28 and B29:
- Human insulin B28 Pro → insulin lispro B28 Lys.
- Human insulin B29 Lys → insulin lispro B29 Pro.

The FDA-approved Humalog label names this analogue Lys(B28), Pro(B29) human insulin. It reports empirical formula **C₂₅₇H₃₈₃N₆₅O₇₇S₆** and molecular weight **5.808 kDa**, identical to human insulin.

Insulin retains the canonical insulin A and B chains and their disulfide connectivity. Use the structure diagram in the official label or an independently sourced structural record; do not redraw or alter disulfide connectivity without validating it.

**Sequence field status:** substitution identity verified from official label; full residue-by-residue A/B chain sequence should be transcribed from the official label diagram or a curated sequence record in the next curation pass. Do not auto-generate it from the parent human-insulin sequence.

## 3. Mechanism of action

Insulin lispro binds and activates the insulin receptor, a receptor tyrosine kinase. The approved label describes the class pharmacology: increased glucose uptake in skeletal muscle and adipose tissue and reduced hepatic glucose production. Insulin also inhibits lipolysis and proteolysis and promotes protein synthesis.

The B28/B29 exchange reduces self-association relative to regular human insulin, supporting more rapid absorption after subcutaneous administration. This mechanistic explanation should be supported with primary biophysical/pharmacology literature in the next pass; the approved label independently confirms the more rapid onset and shorter duration versus regular human insulin.

## 4. Pharmacodynamics and pharmacokinetics

- Pharmacodynamic class: rapid-acting prandial insulin.
- The label reports molar equipotency to human insulin; one unit has the same glucose-lowering effect as one unit of regular human insulin.
- After subcutaneous administration, onset is faster and duration shorter than regular human insulin.
- Timing varies among and within individuals and is affected by injection site, exercise and other factors.
- Do not place a single onset/peak/duration number in the dossier without recording the study, route, formulation, population and label version.
- IV use is included in the product label; do not extrapolate subcutaneous absorption parameters to IV administration.

## 5. Regulatory and product evidence

- Humalog: initial US approval 1996; current DailyMed label updated June 16, 2026 at the time of this review.
- Humalog label indicates improvement of glycemic control in adult and pediatric patients with diabetes mellitus.
- The workbook also lists Admelog and Lyumjev. They are not interchangeable evidence records: each has its own formulation, label, approval history, administration instructions and product-specific PK profile. Separate product subrecords are required.
- FDA application/label reference for Humalog: BLA 020563 (also see FDA label repository record).

## 6. Formulation and administration facts from Humalog label

Humalog U-100 and U-200 are clear, colourless sterile solutions. The label lists different excipient compositions by concentration. U-100 includes glycerin, dibasic sodium phosphate, metacresol, trace phenol, zinc and water for injection; U-200 includes glycerin, metacresol, trace phenol, tromethamine, zinc and water for injection. Product and concentration must be represented explicitly.

The June 2026 Humalog label describes subcutaneous administration within 15 minutes before a meal or immediately after a meal, and includes IV use. These are product-label statements, not individualized recommendations.

## 7. Safety and interactions — label-derived summary

- Major risk: hypoglycaemia, including severe episodes.
- Other label warnings include hypoglycaemia due to medication errors, hypersensitivity, hypokalaemia, and risks associated with changes in insulin regimen.
- Renal or hepatic impairment may increase hypoglycaemia risk and may require closer monitoring and dose adjustment by the treating clinician.
- Concomitant antidiabetic medicines and several other drug classes can increase hypoglycaemia risk; corticosteroids, some antipsychotics, diuretics, hormones and sympathomimetics may reduce glucose-lowering effect; beta-blockers and certain other agents can mask hypoglycaemia symptoms.
- Extract the complete adverse-reaction frequencies, contraindications, pregnancy/lactation information and full interaction table from the current label in a subsequent safety-specific pass. This summary is not exhaustive.

## 8. Clinical evidence

The regulatory label is the primary source for the approved indication and product use. This dossier does not yet contain a structured clinical-trial table. Add pivotal trial identifiers, design, population, comparator, endpoints, effect estimates and publication references before marking clinical evidence complete.

## 9. Structure, images and data assets

- Official Humalog label contains the two-chain primary-structure diagram and is the preferred initial attributed image source.
- Image asset not yet copied into the repository. The dossier UI should link to the official label diagram with source, caption and access date; verify rights/terms before redistributing a local copy.
- No experimental PDB structure or predicted model is asserted in this record.

## 10. Manufacturing, quality, stability and patents

- Recombinant production in *E. coli* is stated in the label.
- Product-specific manufacturing process, critical quality attributes, impurities, aggregation, stability, storage and device compatibility are not yet curated here.
- Patent landscape is not yet reviewed. Do not infer patent expiry from first approval date.

## 11. Evidence references

1. **Current official Humalog label (DailyMed; updated 2026-06-16).** Identity, B28/B29 substitutions, formula, molecular weight, manufacturing expression host, indications, administration, pharmacology, warnings and interactions. https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c8ecbd7a-0e22-4fc7-a503-faa58c1b6f3f
2. **FDA-approved Humalog prescribing information (2024 label PDF).** Description, primary structure diagram and mechanism of action. https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/020563Orig1s202%2C205747Orig1s028Lbl.pdf
3. **FDA FDALabel application listing.** BLA 020563 and initial approval date metadata. https://nctr-crs.fda.gov/fdalabel/ui/spl-summaries/criteria/379775
4. **DailyMed insulin lispro label (2025).** Generic insulin lispro label and initial US approval. https://www.dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=97d5e596-aae1-42c9-ae89-c3780959c467

## 12. Completion checklist

- [x] Generic identity and analogue substitution verified against official label
- [x] Molecular formula and molecular weight captured
- [x] Label-level mechanism captured
- [x] Initial US approval and current Humalog label source recorded
- [x] Product formulation distinction noted
- [ ] Full A/B chain sequence transcribed and independently cross-checked
- [ ] Receptor binding / self-association mechanism supported by primary literature
- [ ] Product-specific PK tables for Humalog, Admelog and Lyumjev
- [ ] Full label safety and adverse-event extraction
- [ ] Clinical trial registry and pivotal publication table
- [ ] Attributed structure image asset and licence/reuse review
- [ ] Manufacturing, stability, quality and patent review

**Overall status: in_progress.**