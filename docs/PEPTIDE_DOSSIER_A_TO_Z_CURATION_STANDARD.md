# A-to-Z peptide dossier curation standard

## Purpose and scope

This standard governs every independent peptide dossier imported from a user catalogue. A dossier is a navigable, independently editable record keyed by a stable canonical UUID after identity review. Before identity review, each workbook row is an independent discovery folder. The source workbook is retained as a verbatim source observation and is never treated as proof of scientific or regulatory facts.

A dossier is not considered scientifically complete merely because all fields exist. Each populated factual assertion must have an attached source, a source locator and an evidence classification. Empty fields must be displayed as **Not yet curated** or **Not reported in reviewed sources**, never silently inferred.

## Required A-to-Z sections

1. **Identity and nomenclature** — preferred name, INN/USAN, synonyms, development codes, brand names, source identifiers, peptide/protein/conjugate classification, identity confidence and ambiguity notes.
2. **Amino-acid sequence** — one-letter and three-letter sequence, residue count, sequence source, residue stereochemistry, noncanonical residues, terminal chemistry, cyclization, disulfide bonds, post-translational modifications and conjugation. Do not infer a sequence from a name.
3. **Chemical identity** — molecular formula, average and monoisotopic mass, SMILES, InChI, InChIKey, charge, pKa, isoelectric point, counterions, salts, conjugates, calculation method and exact chemical form.
4. **Structure and conformation** — experimental or predicted 2D/3D structures, PDB/AlphaFold identifiers, model version, chain/residue mapping, confidence metrics, method, resolution and limitations.
5. **Mechanism of action** — primary and secondary targets, target action, binding/interaction, potency/affinity and assay, receptor occupancy where reported, downstream signalling, pathways, cell/tissue context, species/population and evidence grade.
6. **Pharmacodynamics** — dose/exposure-response, efficacy biomarkers, duration, pharmacological effects and relevant assay context.
7. **Pharmacokinetics** — absorption, bioavailability, distribution, metabolism, clearance, elimination, half-life, protein binding, route and population differences.
8. **Clinical development** — trial registry IDs, phase, status, sponsor, protocol, design, sample size, population, intervention, comparator, endpoints, results, adverse events, publication and limitations.
9. **Preclinical evidence** — model, species, cell type, dose/exposure as reported, route, duration, endpoints, results, assay methods, reproducibility and translational limitations.
10. **Regulatory status** — product-level and jurisdiction-level authorization, authority, exact product/active ingredient, application/authorization number, indication, formulation, strength, route, approval/effective/withdrawal dates, label version and official source. FDA status must never be generalized from one product, salt, indication or dosage form to every form of the molecule.
11. **Indications and use** — approved indications separately from investigated, off-label, historical, traditional, marketing and research uses.
12. **Dosage forms and administration** — approved/researched formulations, route, device, release characteristics and product-specific label information. Do not provide unsupported dosing recommendations.
13. **Safety and tolerability** — adverse events, serious risks, contraindications, warnings, interactions, immunogenicity, toxicology, overdose information and population-specific cautions, all linked to exact evidence.
14. **Drug interactions** — pharmacodynamic and pharmacokinetic interactions, interaction mechanism, clinical significance and evidence source.
15. **Formulation composition** — excipients, buffers, stabilizers, surfactants, tonicity agents, container closure, device and product-specific formulation references.
16. **Stability and storage** — label storage, in-use stability, freeze/thaw, light sensitivity, agitation, degradation pathways, aggregation, oxidation, deamidation and evidence conditions.
17. **Manufacturing and process** — recombinant, solid-phase synthesis, liquid-phase synthesis, fermentation, extraction or other verified production route; process overview, critical quality attributes and source.
18. **Purification and impurity profile** — purification steps, related substances, truncations, deletion sequences, residual solvents/reagents, host-cell impurities, endotoxin and validated limits where public evidence exists.
19. **Analytical characterization** — identity, purity, potency, content, aggregation, charge variants, mass spectrometry, chromatography, electrophoresis, spectroscopy, bioassays, method validation and applicable standards.
20. **Quality and specifications** — pharmacopeial monographs, release/stability specifications, batch-specific certificates and source; never fabricate acceptance criteria.
21. **Bioinformatics and computational analysis** — sequence alignments, motif/domain analysis, predicted structure, docking, target prediction and computational limitations. Predictions are not experimentally verified facts.
22. **Pathways and systems biology** — pathway identifiers, gene/protein links, interaction networks, tissue context and evidence type.
23. **Patents and intellectual property** — publication number, family, priority/filing/grant dates, applicant, claims relevant to the peptide and legal status source.
24. **Literature and references** — complete citation, authors, title, journal, year, DOI, PMID/PMCID, trial registry, official label/authority, source URL, access date, source locator and evidence appraisal.
25. **Images and visual assets** — image type, caption, peptide/form association, source URL, provider identifier, attribution, licence/terms, retrieval date, content hash, alt text and review status.
26. **Commercial/product landscape** — approved brands, authorization holder, manufacturer, product strengths and exact source. Do not conflate approved commercial products with research-grade vendor materials.
27. **Knowledge gaps and conflicting evidence** — missing fields, contradictory findings, disputed identity, outdated sources, confidence and next curation action.
28. **Editorial and audit history** — author, reviewer, timestamps, section revision, reason for change, prior value and source provenance.
29. **Safety/regulatory disclaimer** — research database context, not personal medical advice, prescribing, quality certification or regulatory legal opinion.

## Claim-level reference requirements

- Every mechanism, sequence, chemical property, PK/PD, clinical, preclinical, safety, manufacturing, formulation and regulatory claim must cite one or more source records.
- Store exact DOI, PMID, NCT/EudraCT/CTIS identifier, FDA application/NDA/BLA number, EMA/other authorization number, PDB accession or provider record identifier where available.
- Capture a page, table, figure, section, label subsection, trial outcome measure or database field locator.
- Record publication type and evidence level: official label/regulatory record, human mechanistic study, clinical trial, observational human study, animal in-vivo, in-vitro, ex-vivo, computational, review or secondary assertion.
- A review article can guide discovery but must not be represented as primary evidence when a primary source is available.
- AI-extracted text is a candidate assertion only. It cannot be automatically marked verified.
- Preserve conflicting results and limitations. Do not average contradictory results into a synthetic conclusion.
- Cite the original workbook only for the fact that a particular value appeared in that workbook. It is not a source for the truth of the value.

## Preferred reference sources

Use source classes according to the claim being supported:

- Regulatory/product status: FDA Drugs@FDA, FDA Purple Book where relevant, FDA-approved prescribing information / DailyMed, EMA EPAR and Union Register, MHRA, Health Canada DPD and other national regulator databases.
- Clinical trials: ClinicalTrials.gov, CTIS and WHO ICTRP; then the linked registry results and publications.
- Literature: PubMed/MEDLINE, PubMed Central, Crossref and the publisher's original article.
- Sequence/protein: UniProt, NCBI Protein, reviewed primary publications and authoritative product labels.
- Chemical identifiers: PubChem, ChEBI, DrugBank (licence permitting), ChEMBL and original characterization papers. Verify exact salt/conjugate/form before linking.
- Structure: RCSB PDB for experimental structures; AlphaFold DB for predictions; PubChem 2D depictions for chemical structures. State whether a model is experimental or predicted.
- Targets/pharmacology: IUPHAR/BPS Guide to PHARMACOLOGY, ChEMBL, UniProt and primary binding/functional assay publications.
- Pathways: Reactome, KEGG (subject to terms), WikiPathways and primary studies.
- Antimicrobial peptides: DBAASP and DRAMP, with original assay publications.
- Patents: WIPO PATENTSCOPE, Espacenet, USPTO and national patent offices.

## Image sourcing and display rules

- Prefer provider-hosted structure images or accession-linked renderings over unverified image search results.
- For a 2D chemical depiction, retain the PubChem CID or exact compound identifier and link to the corresponding record/image endpoint.
- For experimental 3D structures, retain PDB accession, chain, method, resolution and the RCSB source page.
- For predicted structures, retain the AlphaFold DB accession/model version and confidence metadata; label them as predictions.
- For microscopy, gels, chromatograms, pathway figures and mechanism diagrams, use only figures with clear publication/source provenance and reuse rights. Do not scrape or redistribute publisher figures without permission.
- Every image must have alt text, caption, source URL, attribution and licence/terms. If reuse rights are unclear, show a link/thumbnail preview from the provider rather than storing a copy.
- Never present an illustrative image as evidence for a mechanism, efficacy or safety claim.

## Import and curation workflow

1. Import workbook rows as immutable source observations.
2. Create one independently navigable discovery folder for each row.
3. Resolve whether the item is actually a peptide, peptide-derived molecule, peptide conjugate, peptide antibiotic, protein/biologic, radiopharmaceutical or a non-peptide entry. Preserve original rows even when classification is disputed.
4. Resolve synonyms, salts, fragments, conjugates and brand names without merging distinct chemical entities by string similarity alone.
5. Enrich each field from the preferred source classes above and attach claim-level citations.
6. Curate MOA and sequence only when supported by exact source evidence.
7. Add structures and images with source/licence metadata.
8. Review regulatory status at product/form/indication/jurisdiction level.
9. Submit each section for expert review. Only reviewed claims become public verified facts.
10. Keep revisions and source refreshes append-only or versioned.

## Completion definition

A peptide dossier is **curation-complete** only when each applicable section is populated or explicitly marked not reported/not applicable, all factual claims have references and locators, visual assets have provenance and reuse status, regulatory status is checked against current official sources, conflicts and evidence limitations are documented, and the required reviewer has approved the dossier. A populated template or a source search result is not completion.
