# Peptide mechanism-of-action evidence standard

## Purpose

Every peptide dossier should provide a dedicated mechanism-of-action (MOA) section. MOA records describe source-supported molecular events; they must not collapse target binding, pathway modulation, pharmacodynamic effects and clinical outcomes into one claim.

## Required record dimensions

Each MOA record is linked to a canonical peptide identity and, when justified, an exact chemical form. It captures:
- mechanism title and concise, testable mechanism statement;
- mechanism class (for example receptor agonism, antagonism, enzyme inhibition, ligand binding or transporter modulation);
- molecular target, stable target identifier, target action and binding/interaction evidence;
- downstream signalling, pathway context and biological effect;
- tissue/cell context and species/population;
- evidence level and evidence type;
- confidence assessment, limitations and applicability caveats;
- source record, exact locator/section, quoted excerpt where licensing permits, retrieval provenance and review status.

## Evidence levels

| Evidence level | Meaning | Presentation rule |
|---|---|---|
| regulatory_label | Mechanism stated in an official regulator product label | Attribute to the exact product and label version |
| human_mechanistic | Direct human mechanistic or target-engagement evidence | Describe population, assay and endpoint |
| human_clinical | Mechanistic interpretation from human clinical observations | Do not confuse outcome with direct target engagement |
| in_vivo_animal | Animal evidence | Label species and model |
| in_vitro / ex_vivo | Cell, biochemical or tissue experiment | Include assay and experimental context |
| computational | Simulation, docking, network or other model | Hypothesis only; disclose model and validation |
| source_asserted | Source makes a statement without primary mechanistic evidence in the record | Attribute, do not upgrade to established |
| ai_extracted | AI-extracted candidate assertion | Keep unverified until source and extraction are reviewed |
| curator_interpreted | Curator synthesis across sources | Preserve rationale and all supporting/contradicting evidence |
| unknown | No defensible mechanism has been curated | Display as unknown/not yet established in this dossier |

The evidence level is not a numeric ranking of biological truth. Multiple independent records may describe different parts of the same proposed mechanism.

## Distinguish mechanism from pharmacology and outcomes

- **Target interaction:** what molecule the peptide binds or modulates and the nature of that interaction.
- **Mechanism/signalling:** the intracellular or extracellular sequence of events following interaction.
- **Pharmacodynamics:** measurable physiological or biochemical effects.
- **Pharmacokinetics:** absorption, distribution, metabolism and elimination.
- **Clinical outcome:** endpoints observed in a defined clinical study or approved indication.

A pathway association is not necessarily a direct target. A downstream biomarker change is not proof of direct binding. Do not infer a target from a phenotype alone.

## Curation and display policy

1. Every record must cite a retrievable source and exact locator where available.
2. Regulatory-label mechanisms must point to the exact product label, jurisdiction and version; labels can differ by product, formulation and date.
3. Keep in-vitro, animal, human, computational, AI-extracted and curator-interpreted evidence separate.
4. Do not use an unsupported generic MOA for every product sharing a peptide name; chemical modifications and formulation can change pharmacology.
5. Contradictory mechanisms remain visible as separate claims with context rather than being silently reconciled.
6. Unknown is a valid state. Never fabricate a mechanism to fill a blank dossier section.
7. Only curator-verified records appear as authoritative public MOA assertions. Draft and in-review records remain in the governed review workflow.
8. Any AI-generated mechanism must include model/version, prompt or extraction provenance, source passage and human review status.
9. A mechanism record is not proof of efficacy, safety, clinical benefit or suitability for an individual.

## Primary-source examples for ingestion tests and curation training

- Tirzepatide (Mounjaro) DailyMed label, section 12.1: GIP and GLP-1 receptor agonism; the label also describes albumin binding as a half-life-prolonging feature. Do not misclassify albumin binding as its pharmacological receptor mechanism. https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d2d7da5d-ad07-4228-955f-c7e355c8cc0
- Exenatide DailyMed label, section 12.1: GLP-1 receptor agonism and glucose-dependent insulin secretion, glucagon suppression and delayed gastric emptying. https://www.dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e6cb5c8f-e97f-4a6a-95a4-939fd2393949
- Eptifibatide DailyMed label, section 12.1: reversible inhibition of platelet aggregation through interference with fibrinogen, von Willebrand factor and other adhesive ligands binding GP IIb/IIIa. https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c0781dae-3ef6-4cab-b084-01d2e45f3764
- FDA labeling resources identify section 12.1 as Mechanism of Action, 12.2 as Pharmacodynamics and 12.3 as Pharmacokinetics. https://www.fda.gov/media/165785/download

These examples are references for source extraction and data modelling, not a pre-curated claim that should be copied to other peptides.

## API and dossier presentation

The peptide profile includes `mechanisms_of_action`, an array of curator-verified records. The dossier displays target, action, binding/interaction, downstream signalling, pathway, biological context, evidence level, limitations and source links. An empty array is rendered as “not yet curated”, never as “no mechanism”.


## Automated extraction from DailyMed SPL

The DailyMed connector retrieves the XML for an exact SPL Set ID and extracts only the explicitly coded 12.1 Mechanism of Action section:
- LOINC code `43679-0` (Mechanism of Action);
- a title-based fallback is allowed only when the title explicitly begins with `12.1` and contains “Mechanism of Action”;
- pharmacodynamics (12.2 / LOINC `43681-6`) and pharmacokinetics (12.3 / LOINC `43682-4`) are not substituted for MOA;
- if no explicit MOA section is found, the connector returns “section not present” and does not infer a mechanism.

DailyMed text is stored as a source-reported mechanism hint with `source_asserted` evidence level. DailyMed presence alone does not establish FDA approval; the current SPL may differ from the last FDA-approved label. A curator must verify the exact product, chemical form, jurisdiction, label version and approval record before promoting the text to a `regulatory_label` mechanism record.

Official references:
- FDA section-heading mapping: https://www.fda.gov/industry/structured-product-labeling-resources/section-headings-loinc
- FDA labeling resources: https://www.fda.gov/media/165785/download
- DailyMed web services and SPL Set ID XML resource: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm


## Promotion into an individual peptide dossier

Researchers can submit a DailyMed SPL Set ID against an existing peptide dossier through the enrichment workspace. The system:
1. retrieves the exact SPL XML and extracts the explicit 12.1 section;
2. stores a normalized source record and immutable source-version snapshot;
3. creates a peptide mechanism record with `evidence_level=source_asserted`, `mechanism_class=unknown`, the exact source locator, excerpt, SPL version and explicit limitations;
4. links the record to the selected peptide and optional chemical form;
5. creates an organization-scoped curation review.

The mechanism remains `in_review` and is not shown in the public dossier's verified MOA section until an independent curator verifies it. A reviewer cannot approve their own submission. Verification records reviewer identity and timestamp; corrections create immutable mechanism revisions.

A source record is not automatically classified as a regulatory-label mechanism. Upgrading to `regulatory_label` requires separate verification of the exact product authorization, active ingredient/chemical form, jurisdiction and label version.


## DBAASP activity and combination evidence

DBAASP v4 source records can contribute experimentally reported antimicrobial target activity, antibiofilm activity, hemolytic/cytotoxic measurements and peptide-antibiotic combination observations. The connector preserves the source's values and conditions rather than converting them into a normalized efficacy score.

Combination records are not automatically classified as peptide-peptide synergy. A DBAASP record may describe one peptide combined with an antibiotic; the source's FICI and component activity fields are preserved with the organism/strain and publication reference when available. Any future quantitative analysis must first verify compatible assay design, units, endpoints, concentrations, controls and component identities. A source-reported FICI alone is not evidence for a different pair of peptides or a clinical interaction.

## Importing GtoPdb peptide-target interactions

The enrichment workspace can retrieve an exact peptide ligand by its GtoPdb ligand ID when the registered API key is configured. Each explicit target/action interaction is submitted as a separate mechanism evidence record:
- `evidence_level=source_asserted`, `evidence_type=unknown`, `mechanism_class=unknown`;
- preserve the source interaction payload, exact ligand identifier, target, action, source locator and source version;
- submit each interaction to independent curator review;
- do not infer binding affinity, receptor subtype, downstream signalling, pathway activation, clinical effect or regulatory status when those fields are not explicitly supported.

GtoPdb interaction types such as “agonist” or “antagonist” are source-reported pharmacological interaction labels. They are not, by themselves, a complete molecular mechanism or proof of clinical effect. Verify the exact peptide and chemical form, target subtype, species, assay context, interaction direction and supporting literature before approval.

GtoPdb licensing must be respected: the database is ODbL and its content is CC BY-SA 4.0. Attribution and share-alike obligations must be assessed before redistribution or commercial reuse.

## Promotion of ChEMBL mechanism records into curation

A researcher may submit an exact ChEMBL molecule ID against a canonical peptide dossier. The importer first verifies that ChEMBL returns an explicit `PEPTIDE1{` HELM biotherapeutic record. It then imports only mechanism rows containing both a mechanism statement and a ChEMBL target identifier.

Each mechanism row becomes a separate `source_asserted`, `in_review` record with the exact ChEMBL molecule ID, target ID, source mechanism ID/locator, ChEMBL release and raw source excerpt. It is not automatically classified as a regulatory-label mechanism. ChEMBL's mechanism endpoint is an aggregated drug-mechanism resource; it does not establish authorisation in any specific jurisdiction or exact equivalence to the selected peptide chemical form. An independent curator must verify the molecule/HELM identity, target, action type and supporting references.
