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
