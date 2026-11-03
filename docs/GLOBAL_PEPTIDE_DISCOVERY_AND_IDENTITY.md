# Global peptide discovery and identity-resolution workflow

## Purpose and boundary

The global peptide catalogue is built from source observations, not by assuming one database is complete. The discovery registry stores candidate observations from official regulatory labels, clinical-trial registries and scientific/chemical databases. It is deliberately separate from canonical peptide entities and from product-level regulatory authorizations.

A source match is not proof that a record describes a peptide. Search terms can match brands, combination products, non-peptide drugs, proteins, publications about unrelated subjects or records that mention a peptide only in passing. Every candidate begins with unresolved identity.

## Current discovery ingestion API

Authenticated organization members with researcher, curator or reviewer permissions can submit:

`POST /api/v1/enrichment/discover-peptides`

Example request:

```json
{
  "query": "tirzepatide",
  "sources": ["fda_drugsfda", "dailymed", "clinicaltrials", "pubmed"],
  "limit": 20
}
```

The request searches only selected sources and is bounded to 50 records per source. The service stores:
- stable source record identity and URL;
- normalized source snapshot with content hash;
- candidate identity, currently unresolved;
- source-specific status and jurisdiction where supplied;
- raw normalized source payload and search context;
- append-only candidate observations;
- an audit event for the discovery run.

The endpoint is authenticated and rate-limited. It does not create a canonical peptide, sequence, regulatory authorization or mechanism assertion. Repeated discovery runs update the candidate's last-seen timestamp and append a new observation only when source content changes.

## Current connected source families

| Source | What it contributes | Important limitation |
|---|---|---|
| FDA Drugs@FDA via openFDA | Application, product presentation, strength, route, sponsor and submission action observations | Not all CBER biologics or non-approved products; a missing record is not proof of non-approval |
| FDA Purple Book | FDA-licensed CDER/CBER biologics, BLA/product identifiers, strength, dosage form, route, licensure and biosimilar relationships | Includes many non-peptide biologics; a match is not proof that the entity is a peptide |
| NLM DailyMed | Structured Product Label identifiers, versions, titles and publication dates | Current SPL may differ from the last FDA-approved label; label presence is not approval proof |
| Health Canada Drug Product Database | Canadian DIN, ingredient/strength, product class, status, dosage form and route | Includes human and non-human product classes; status is Canadian and source-specific |
| IUPHAR/BPS Guide to PHARMACOLOGY | Expert-curated peptide/endogenous-peptide ligands and source-reported target interactions | Requires registration/API key; not a complete peptide inventory; license and commercial-use terms apply |
| DRAMP 5.0 | Antimicrobial peptide sequences, activity classifications, clinical/stability categories and FASTS sequence/SMILES records | AMP-focused subset, not all peptides; patent exports excluded pending permission; source modifications require careful identity curation |
| ClinicalTrials.gov | Study identifiers, status, phase, sponsor, interventions and summaries | An intervention name does not prove the investigational product is a peptide |
| PubMed | Publication metadata, abstracts and identifiers | A paper may mention a peptide without studying it |

Existing read-only discovery integrations also include PubChem, UniProtKB, RCSB PDB and AlphaFold DB. Their records are useful for chemistry, sequence, protein and structural context but do not alone establish a therapeutic peptide identity or regulatory status.

## Identity resolution

The identity resolver must evaluate, where available:
1. exact name and aliases;
2. amino-acid sequence, sequence type and terminal residues;
3. stereochemistry, noncanonical residues and post-translational modifications;
4. conjugation, cyclization, salts/counterions and other chemical-form dimensions;
5. source identifier and primary source context;
6. target and mechanism evidence only as supporting context, never as identity proof.

A similar name or sequence fragment is not enough to merge entities. A peptide and its modified analogue, conjugate, salt or formulation may require separate chemical-form or product records while sharing a canonical parent only when the scientific identity rules support that relationship.

## Regulatory status

Regulatory status is not copied from a discovery result as a global peptide flag. It is recorded against an exact product/presentation, active ingredient, chemical form where known, indication, authority, jurisdiction, label/application and effective date. FDA status cannot be inferred from DailyMed presence, trial status or a publication.

## Mechanism of action

Source-reported mechanism text remains a discovery hint only. Curated mechanism assertions are entered in `peptide_mechanisms`, linked to source records and classified by evidence level (regulatory label, human mechanistic, human clinical, animal, in-vitro, ex-vivo, computational, AI-extracted, curator-interpreted or unknown). No missing mechanism is filled by AI guesswork.

## One dossier per canonical peptide

The user-facing catalogue will have one navigable dossier for each canonical peptide identity. Source candidates remain in a discovery/review workspace until resolved. Multiple source observations can link to the same dossier without duplicating the peptide entity; distinct chemical forms and product presentations remain separately addressable within it.

## Coverage and completeness

A worldwide inventory is an ongoing evidence-coverage programme, not a one-time scrape. The platform must record source coverage, query terms, retrieval time, pagination, API limitations, failed sources, duplicate rates and curator outcomes. It must never claim that a peptide does not exist or is not approved merely because it was absent from the sources searched.


## Additional peptide-source coverage candidates (planned, not yet integrated)

| Source | Potential contribution | Access / governance consideration |
|---|---|---|
| APD6 | Curated natural antimicrobial peptide sequence datasets with organism/source categories | Public FASTA downloads; preserve release date and citation |
| DBAASP | Antimicrobial peptide sequences, experimental activity, MIC and target-organism annotations | Verify current download/API access and field-level reuse terms before ingestion |
| PeptideAtlas | Mass-spectrometry-supported endogenous peptide/proteomics observations across organisms | Data products are CC BY-NC 4.0; restrict to non-commercial use unless separately licensed |
| IEDB | Peptide epitopes and immune assay evidence | Epitope evidence is not a comprehensive peptide inventory or proof of therapeutic status |

These sources cover different biological domains and must remain separately attributed. A peptide sequence observed in a proteomics or epitope dataset is not automatically a mature, stable, independently existing therapeutic peptide entity.
