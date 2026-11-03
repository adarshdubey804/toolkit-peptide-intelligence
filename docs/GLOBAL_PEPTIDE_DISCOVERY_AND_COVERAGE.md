# Global peptide discovery registry and coverage policy

## Purpose

The global catalogue is not limited to approved medicines. It must discover and distinguish:
- marketed/approved therapeutic peptide products;
- investigational clinical candidates;
- preclinical and laboratory research peptides;
- endogenous peptides and peptide hormones;
- peptide antibiotics, toxins, fragments and conjugates where relevant to the scientific scope;
- withdrawn, discontinued, rejected, suspended or otherwise inactive development records;
- candidates whose status is unknown or not reported by the source.

A source search result is a discovery observation, not a verified peptide identity, regulatory determination or mechanism-of-action claim.

## Canonical peptide versus discovery candidate

The canonical `peptides` table represents the curated peptide identity. The `peptide_discovery_candidates` table stores source-level observations before entity resolution. Candidates preserve:
- source and source entity identifier;
- source URL, source-reported name and type;
- source-reported development status and jurisdiction;
- reported sequence, chemical form, target and mechanism hints;
- identity-match state, rationale and optional canonical peptide link;
- first/last seen timestamps and raw source metadata.

Name similarity alone must never auto-link two entities. Sequence identity, stereochemistry, terminal chemistry, cyclization, conjugation, salts and other chemical-form dimensions must be considered before merging candidates into a canonical dossier.

## Source observations and change history

Each changed source payload is stored as a content-addressed immutable observation. Re-fetching the same payload does not create duplicate observations. A source update appends a new observation; it never silently overwrites historical data.

Curation decisions are append-only. A reviewer may accept a candidate as an existing peptide, accept it as a new peptide, mark it duplicate/rejected, or request more evidence. Corrections are represented by a new decision, preserving the original decision trail.

## Regulatory and development status

Never collapse these distinct concepts into one status:
- **FDA product authorization:** exact product/application, dosage form, route, strength, application/submission history and jurisdiction.
- **Current marketed availability:** may differ from historical approval; source-specific and time-sensitive.
- **Clinical development:** phase, trial status, sponsor and dates from a clinical-trial source.
- **Preclinical research:** model, species, assay and publication date.
- **Research-only / source assertion:** preserve as reported and attribute it to the source.
- **Unknown / not found:** only means no conclusion was established in the sources and scope checked.

A failed or empty Drugs@FDA query is not evidence that a peptide is not FDA approved. Drugs@FDA does not cover every CBER-regulated biological product or non-approved research entity. DailyMed SPL presence is not proof of FDA approval. The Purple Book and other regulator datasets must be integrated as separate sources with their own coverage and status semantics.

## Initial United States discovery sources

| Source | What it contributes | What it does not prove |
|---|---|---|
| FDA Drugs@FDA via openFDA | NDA/BLA application, product, strength/form/route, submission and approval-action observations | Complete coverage of every biologic, current marketing availability, or peptide identity without review |
| NLM DailyMed | Structured Product Label (SPL) identifiers, label versions and published label metadata | That an SPL is the exact last FDA-approved label or proof of approval |
| ClinicalTrials.gov | Registered interventional/observational study records and status | That a study result is positive, that a peptide is approved, or that a record is necessarily a unique peptide entity |
| PubMed | Scientific literature and abstracts | That a paper's statements are established facts or that the peptide is a therapeutic product |
| ChEMBL | Explicit peptide HELM biotherapeutic records, source molecule IDs, and source-reported approved-drug mechanism records | That a HELM record is a marketed product, that all biotherapeutics are peptides, or that ChEMBL coverage is exhaustive |

Future jurisdictional adapters should include regulator-specific datasets and label repositories (for example EMA, MHRA, Health Canada, TGA, PMDA and other national authorities) only after each source's coverage, licensing, identifiers and update policy are documented. Do not infer global regulatory status from FDA-only sources.

## Mechanism of action

Source-reported mechanism text in discovery candidates is only a retrieval hint. A curated mechanism must be created separately in `peptide_mechanisms` with a source locator, evidence level, chemical-form context, limitations and review status. AI-extracted or computational mechanisms remain unverified hypotheses until reviewed.

## Folder-like peptide dossiers

Each canonical peptide has one stable profile route keyed by its immutable UUID. The profile is the dossier landing page and should link to the scientific sections: identity/chemical forms, regulatory products, mechanism of action, targets/pathways, publications/trials, safety, formulation/stability, analytical methods, vendors and research history. Do not create separate physical copies of the same peptide's information in multiple folders; link normalized records to the canonical peptide to prevent inconsistent duplicates.

## Completion criteria for global coverage

Global peptide coverage is an ongoing data-acquisition objective, not a one-time claim that every peptide in the world has been captured. Measure it through:
- source inventory and jurisdiction coverage;
- last successful source poll and source-specific pagination completeness;
- number of unique source observations and canonical identities;
- unresolved/ambiguous candidate backlog;
- duplicate and false-match rates;
- percentage of dossiers with reviewed identity, regulatory, MOA and evidence sections;
- explicit source outages, rate limits, licensing restrictions and known blind spots.

The interface must display these limitations and the last checked timestamp. Never label the database “complete” unless a defined source scope and measurable completeness criteria are met.

### ChEMBL peptide scope
The ChEMBL adapter searches molecule records and retains only linked biotherapeutic entries whose HELM notation explicitly begins with `PEPTIDE1{`. ChEMBL also contains antibodies and recombinant proteins; these are excluded from this peptide-specific adapter unless separately curated under a different entity scope. HELM notation is preserved verbatim and must not be flattened into an unmodified amino-acid sequence. ChEMBL mechanism records are source-reported observations and are not automatically promoted into the canonical peptide mechanism table.

## Specialist peptide research resources and reuse limits

| Source | Scientific contribution | Current access and limitations |
|---|---|---|
| PeptideAtlas | Multi-organism peptide evidence from tandem mass-spectrometry proteomics, build-specific peptide identifications, spectra and FDR processing | Link-out only. Data products are CC BY-NC 4.0; commercial reuse requires separate permission. Do not bulk-ingest into commercial deployments without permission |
| CancerPPD 2.0 | Manually curated anticancer peptide/protein sequences, chemical modifications, structures, cancer cell-line assays, tissues and selected clinical-trial links | Link-out only. The database includes both peptides and proteins; a clear redistribution licence has not been validated for this platform. Do not copy or bulk-ingest until terms are confirmed |
| ProPepBA | Experimentally measured protein–peptide binding affinities, assay conditions, target/peptide sequences, structures and chemically modified peptide entries | Link-out only. This is a specialist binding-affinity resource, not a global peptide inventory; redistribution and automated extraction terms require confirmation |


| TPDB (Therapeutic Peptide Database) | Aggregated peptide records, source-level activity annotations, assay context, standard/modified sequence notation, structural links and noncanonical amino-acid references; public API supports ID, sequence, activity and source queries | Link-out only pending reuse/licence review. TPDB combines many upstream sources and explicitly notes that source labels do not imply a uniform experimental criterion; retain the original source and evidence context |
| TTPdb (Targeted Therapeutic Peptide Database) | Targeted therapeutic peptide candidates across approved, clinical and preclinical/investigational stages, with sequence, target/disease links, chemical modifications, structures and mechanism annotations | Link-out only. Recently published secondary research database; verify approval against official regulators. API and redistribution licence must be assessed before ingestion |
| ThPDB2 | Secondary curated profiles of FDA-approved therapeutic peptides and proteins, including sequence, mechanism, formulation, route, indication and safety fields | Link-out only. Includes non-peptide proteins/antibodies and is not an FDA authority record; verify exact product and label in official FDA sources. Redistribution terms require review |

These sources are displayed in the source coverage catalogue for direct researcher consultation. A public website or REST API does not, by itself, grant permission to mirror or redistribute its data.
