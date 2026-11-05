# Scientific Dossier QA — Batch 04

**Repository:** `adarshdubey804/toolkit-peptide-intelligence`  
**Reviewed ref:** `pr-155-128-peptide-dossiers-evidence-media`  
**Review date:** 5 November 2026  
**Scope:** Degarelix, Desmopressin, Difelikefalin, Dihexa, Dulaglutide, Ecallantide, Efpeglenatide, Elamipretide, Eloralintide, and Enfuvirtide.

## Method and limits

This is a structured editorial and ontology screen of the dossier text. It is not independent validation of current regulatory status, product labels, primary chemistry records or trial publications. Recent approval statements and all sequence claims require authoritative-source verification. All reviewed dossiers remain `in_progress`.

## Batch findings

| Dossier | Observed strengths | QA finding / action |
|---|---|---|
| Degarelix | Identifies a highly modified linear decapeptide and separates approval, label and commercial status. | Verify exact sequence, stereochemistry, salt and depot formulation against current FIRMAGON product information. Keep product-specific PK and clinical evidence linked to formulation. |
| Desmopressin | Strongly separates indications and formulations and highlights hyponatraemia as a critical safety risk. | Model each formulation/product separately (oral, sublingual, intranasal, injectable). Verify historical/current brand marketing status and original approval dates; distinguish free peptide from acetate salt in chemistry records. |
| Difelikefalin | Identifies peripheral kappa-opioid receptor agonism and dialysis-associated pruritus context. | Verify exact stereochemical structure and current product labels by jurisdiction. Extract KALM trial data and current-label PK without mixing IV and other formulations or indications. |
| Dihexa | Clearly identifies an experimental angiotensin-IV-derived peptidomimetic and states human safety/efficacy are not established. | **Identity-critical:** do not assign sequence, SMILES or InChI from secondary shorthand. Resolve covalent connectivity and chemical identity from original patent/primary analytical sources first. Keep HGF/c-Met claims at hypothesis/preclinical evidence level unless directly supported. |
| Dulaglutide | Correctly classifies as a glycosylated, disulfide-linked peptide–Fc fusion biologic and warns against concatenating chain strings. | **Ontology correction:** classify as recombinant fusion protein/biologic, not short peptide. Preserve chain boundaries, Fc sequence, glycosylation, disulfide connectivity and product presentation as separate structured attributes. Verify sequence revision and label version. |
| Ecallantide | Explicitly identifies a recombinant 60-aa Kunitz-domain protein rather than a small peptide and maps workbook cross-reference. | **Ontology correction:** classify as recombinant protein therapeutic. Verify current labeler, marketed status, jurisdictional authorizations and label-specific PK. |
| Efpeglenatide | Correctly classifies as a peptide–Fc fusion and leaves exact mature sequence/linker unresolved rather than inventing it. | **Ontology correction:** model as a fusion conjugate with separate peptide, linker and Fc components. Keep clinical development distinct from marketing authorization; verify sponsor/rights holder by trial and jurisdiction. |
| Elamipretide | Distinguishes approved product from unapproved online SS-31 material and flags stereochemical notation for verification. | **High-priority regulatory check:** independently verify the stated 19 September 2025 FDA accelerated approval, exact indication/population and current FORZINITY label in Drugs@FDA. Verify D-amino-acid and dimethyltyrosine notation before canonical structure registration. |
| Eloralintide | Explicitly corrects a potential development-code alias error and avoids inventing a sequence or structure. | Keep LY3841136 as the dossier's stated development code pending sponsor/registry confirmation. Verify trial identifiers and current regulatory status; do not create a canonical structure until the full stereochemical structure is sourced. |
| Enfuvirtide | Identifies the 36-aa HIV-1 gp41 HR2-derived fusion inhibitor and retains salt/label chemistry as open work. | Verify exact sequence, stereochemistry, salt form and current label. Keep resistance evidence, treatment-experienced population and combination-therapy context explicit; avoid broadening the indication. |

## Cross-cutting findings

1. **Fusion proteins are not short peptides.** Dulaglutide and efpeglenatide, like albiglutide in Batch 03, require a biologic/fusion-protein entity model with component and post-translational-modification annotations.
2. **Recombinant protein therapeutics need their own class.** Ecallantide and other larger protein drugs should not be forced into a small-peptide sequence schema.
3. **Formulation can materially change the product record.** Desmopressin's route-specific products and degarelix's depot formulation require distinct product-level records.
4. **Peptidomimetics require structure-first curation.** Dihexa should remain unresolved until exact connectivity is established; a guessed linear sequence is not acceptable.
5. **Regulatory claims need explicit provenance.** Recent approval statements must be checked against current regulator records and product labels before publication or app display.

## Required follow-up

- Extend the entity taxonomy to distinguish peptide, peptidomimetic, recombinant protein, fusion protein, peptide–Fc conjugate and finished product.
- Add component/chain/linker/post-translational-modification records for fusion biologics.
- Preserve route/formulation-specific regulatory and PK records.
- Verify all approval statements and sequence claims with primary regulator, sponsor or curated chemical records.
- Continue the remaining dossier review batches and then consolidate findings into a master report.

## Completion statement

Batch 04 reviewed **10 additional dossier README files**. The structured QA screen now covers **40 of 133** dossier README files in the PR's changed-file inventory. This is a text-level review only, not complete scientific validation, regulatory confirmation or evidence of a live database import.
